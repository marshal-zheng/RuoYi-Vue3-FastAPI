"""Real request/stream boundaries with an in-memory provider, never paid model calls."""

import asyncio
import json
from contextlib import suppress

import httpx
import pytest
from pydantic import ValidationError

from common.remark_document_v1 import plain_to_remark, remark_literal_text, validate_remark
from config.env import RemarkAISettings
from module_admin.entity.vo.remark_ai_vo import RemarkAIRequest
from modules.system.api.remark_ai_controller import stream_remark_events
from modules.system.application.services.remark_ai_service import (
    RemarkAIError,
    RemarkAIService,
    normalize_output,
    preview_text,
)


def request(**changes):
    return RemarkAIRequest.model_validate(
        {
            'scene': 'post',
            'instruction': '写一段简短岗位说明',
            'target': 'document',
            'document': None,
            'context': {'postName': '设备维护', 'postCode': 'maintenance'},
            **changes,
        }
    )


def settings(**changes):
    return RemarkAISettings(
        deepseek_api_key='test-provider-secret',
        deepseek_base_url='https://provider.test/v1',
        deepseek_model='deepseek-chat',
        **changes,
    )


def text_root(text='负责设备维护', marks=None):
    node = {'type': 'text', 'text': text}
    if marks:
        node['marks'] = marks
    return {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [node]}]}


def chunk(content=None, finish=None, **delta):
    if content is not None:
        delta['content'] = content
    return ('data: ' + json.dumps({'choices': [{'delta': delta, 'finish_reason': finish}]}) + '\n\n').encode()


class ProviderStream(httpx.AsyncByteStream):
    def __init__(self, parts, wait=None):
        self.parts = parts
        self.closed = False
        self.wait = wait
        self.waiting = asyncio.Event()

    async def __aiter__(self):
        for part in self.parts:
            yield part
        if self.wait is not None:
            self.waiting.set()
            await self.wait.wait()

    async def aclose(self):
        self.closed = True


def provider_service(parts, *, status=200, wait=None):
    stream = ProviderStream(parts, wait=wait)
    requests = []

    def handler(incoming):
        requests.append(incoming)
        return httpx.Response(status, stream=stream, headers={'Content-Type': 'text/event-stream'})

    transport = httpx.MockTransport(handler)
    service = RemarkAIService(
        settings(), client_factory=lambda **kwargs: httpx.AsyncClient(transport=transport, **kwargs)
    )
    return service, stream, requests


@pytest.mark.parametrize(
    'changes',
    [
        {'context': {'password': 'must-not-leak'}},
        {'context': {'configValue': 'must-not-leak'}, 'scene': 'config'},
        {'context': {'roleNames': ['wrong scene']}},
        {'context': {'postName': {'nested': 'form'}}},
        {'context': {'postName': 'x' * 301}},
        {'context': {'postName': ['x'] * 51}},
        {'context': {'postName': ['x' * 300] * 21}},
        {'instruction': '   '},
        {'instruction': 'x' * 2001},
        {'target': 'selection'},
        {'selection': plain_to_remark('选区', identity_key='selection')},
        {'scene': 'arbitrary'},
        {'password': 'not-an-accepted-field'},
    ],
)
def test_request_rejects_incorrect_scope_and_overbroad_context(changes):
    with pytest.raises(ValidationError):
        request(**changes)


def test_request_preserves_full_document_selection_candidate_and_allowlisted_labels():
    original = plain_to_remark('原始完整备注', identity_key='original')
    selection = plain_to_remark('选区', identity_key='selection')
    candidate = plain_to_remark('上一个候选', identity_key='candidate')
    result = request(target='selection', document=original, selection=selection, candidate=candidate)
    assert result.model_dump(mode='json')['candidate'] == candidate
    assert result.model_dump(mode='json')['document'] == original


def test_normalization_admits_named_color_bold_link_and_preserves_text():
    marks = [
        {'type': 'textStyle', 'attrs': {'color': 'red'}},
        {'type': 'bold'},
        {'type': 'link', 'attrs': {'href': 'https://example.com/docs'}},
    ]
    result = normalize_output(json.dumps(text_root(marks=marks)))
    assert validate_remark(result) == result
    assert remark_literal_text(result) == '负责设备维护'
    node = result['body']['content']['content'][0]
    assert node['attrs']['blockId'].startswith('blk_')
    assert [mark['type'] for mark in node['content'][0]['marks']] == ['link', 'textStyle', 'bold']
    assert normalize_output(json.dumps(text_root(marks=marks))) != result  # A new candidate owns new block ids.


@pytest.mark.parametrize(
    'root',
    [
        {'type': 'doc', 'content': [{'type': 'image', 'attrs': {'src': 'https://example.com/a.png'}}]},
        text_root(marks=[{'type': 'underline'}]),
        text_root(marks=[{'type': 'link', 'attrs': {'href': 'javascript:alert(1)'}}]),
        text_root(marks=[{'type': 'textStyle', 'attrs': {'color': '#ff0000'}}]),
        text_root(marks=[{'type': 'textStyle', 'attrs': {'color': 'red', 'fontSize': '40px'}}]),
        {'type': 'doc', 'content': [{'type': 'paragraph'}]},
        {'type': 'doc', 'content': [{'type': 'paragraph', 'attrs': {'textAlign': 'center'}}]},
        {'type': 'doc', 'content': [{'type': 'orderedList', 'attrs': {'start': 0}, 'content': []}]},
    ],
)
def test_normalization_rejects_unsupported_and_empty_documents(root):
    with pytest.raises(RemarkAIError):
        normalize_output(json.dumps(root))


def test_normalization_rejects_character_limit_without_truncation():
    with pytest.raises(RemarkAIError, match='output-limit'):
        normalize_output(json.dumps(text_root('中' * 5001)))


def test_partial_json_preview_handles_unicode_escapes_and_only_reads_content():
    content = json.dumps(text_root('中文😀"引号"\\'), ensure_ascii=True)
    prior = ''
    for size in range(1, len(content) + 1):
        current = preview_text(content[:size])
        if current.startswith(prior):
            prior = current
    assert prior == '中文😀"引号"\\'
    assert preview_text('{"type":"doc","reasoning_content":"private","content":[') == ''


async def test_provider_stream_emits_actual_plaintext_deltas_then_validated_document():
    content = json.dumps(text_root(), ensure_ascii=False)
    # Split within the text node so this proves progressive preview before the final object.
    split = content.index('设备')
    service, stream, requests = provider_service(
        [
            chunk(reasoning_content='DO-NOT-DISPLAY-THINKING'),
            chunk(content[:split]),
            chunk(content[split:]),
            chunk(finish='stop'),
            b'data: [DONE]\n\n',
        ]
    )
    events = [event async for event in service.generate(request())]
    deltas = [event['text'] for event in events if event['type'] == 'delta']
    assert len(deltas) == 2
    assert ''.join(deltas) == '负责设备维护'
    assert events[-1]['type'] == 'result'
    assert validate_remark(events[-1]['document']) == events[-1]['document']
    assert stream.closed
    assert len(requests) == 1
    body = json.loads(requests[0].content)
    assert body['stream'] is True
    assert body['response_format'] == {'type': 'json_object'}
    assert body['model'] == 'deepseek-chat'
    assert requests[0].headers['Authorization'] == 'Bearer test-provider-secret'
    assert 'DO-NOT-DISPLAY' not in json.dumps(events)


@pytest.mark.parametrize(
    ('parts', 'code'),
    [
        ([chunk('{}'), chunk(finish='stop'), b'data: [DONE]\n\n'], 'invalid-output'),
        ([chunk(json.dumps(text_root('x' * 5001)))], 'output-limit'),
        ([chunk('{"type":"doc"'), chunk(finish='length')], 'output-limit'),
        ([chunk(json.dumps(text_root())), chunk(finish='stop')], 'incomplete-output'),
        ([chunk(json.dumps(text_root())), b'data: [DONE]\n\n'], 'incomplete-output'),
        ([chunk(finish='content_filter')], 'incomplete-output'),
        ([b'data: {"choices":"not-array"}\n\n'], 'invalid-output'),
        ([b'data: invalid-json\n\n'], 'invalid-output'),
        ([chunk('{"type":[]}'), chunk(finish='stop'), b'data: [DONE]\n\n'], 'invalid-output'),
    ],
)
async def test_provider_failures_never_return_a_partial_success(parts, code):
    service, stream, _ = provider_service(parts)
    events = [event async for event in service.generate(request())]
    assert events[-1]['type'] == 'error'
    assert events[-1]['code'] == code
    assert all(event['type'] != 'result' for event in events)
    assert stream.closed


async def test_provider_http_failure_omits_upstream_body_and_secret():
    service, stream, _ = provider_service([b'PRIVATE-PROVIDER-ERROR test-provider-secret'], status=401)
    events = [event async for event in service.generate(request())]
    assert events == [{'type': 'error', 'code': 'provider-unavailable', 'message': 'AI 服务暂不可用，请稍后重试'}]
    assert stream.closed


async def test_provider_timeout_uses_public_error_without_http_exception_details():
    def handler(_request):
        raise httpx.ReadTimeout('PRIVATE_PROVIDER_ERROR')

    transport = httpx.MockTransport(handler)
    service = RemarkAIService(
        settings(), client_factory=lambda **kwargs: httpx.AsyncClient(transport=transport, **kwargs)
    )
    assert [event async for event in service.generate(request())] == [
        {'type': 'error', 'code': 'timeout', 'message': 'AI 生成超时，请稍后重试'},
    ]


async def test_disconnect_cancels_pending_provider_read_and_closes_http_stream():
    service, stream, _ = provider_service([], wait=asyncio.Event())
    events = stream_remark_events(service.generate(request()))
    pending = asyncio.create_task(anext(events))
    await asyncio.wait_for(stream.waiting.wait(), timeout=1)
    pending.cancel()
    with suppress(asyncio.CancelledError):
        await pending
    assert stream.closed


async def test_closing_after_preview_closes_upstream_before_the_next_read():
    content = json.dumps(text_root())
    service, stream, _ = provider_service([chunk(content)], wait=asyncio.Event())
    events = service.generate(request())
    assert (await anext(events))['type'] == 'delta'
    await events.aclose()
    assert stream.closed


async def test_total_timeout_survives_multiple_sse_events_and_closes_a_stalled_provider():
    content = json.dumps(text_root())
    service, stream, _ = provider_service([chunk(content)], wait=asyncio.Event())
    service.settings = service.settings.model_copy(update={'remark_ai_timeout_seconds': 0.02})
    async with asyncio.timeout(1):
        events = [
            json.loads(encoded.removeprefix('data: '))
            async for encoded in stream_remark_events(service.generate(request()))
        ]
    assert events[0]['type'] == 'delta'
    assert events[-1]['code'] == 'timeout'
    assert stream.closed


async def test_selection_followup_prompt_contains_frozen_original_and_previous_candidate():
    content = json.dumps(text_root('调整后的片段'))
    service, _, requests = provider_service([chunk(content), chunk(finish='stop'), b'data: [DONE]\n\n'])
    body = request(
        document=plain_to_remark('完整原文', identity_key='doc'),
        target='selection',
        selection=plain_to_remark('原始选区', identity_key='selection'),
        candidate=plain_to_remark('上一候选', identity_key='candidate'),
    )
    events = [event async for event in service.generate(body)]
    assert remark_literal_text(events[-1]['document']) == '调整后的片段'
    prompt = json.loads(json.loads(requests[0].content)['messages'][1]['content'])
    assert prompt['target'] == 'selection'
    assert remark_literal_text(prompt['document']) == '完整原文'
    assert remark_literal_text(prompt['candidate']) == '上一候选'
