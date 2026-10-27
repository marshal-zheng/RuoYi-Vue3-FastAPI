"""Actual SDK + domain contracts using a memory transport; never call a model or public host."""

import asyncio
import json
import os
import socket
import subprocess
import sys
from types import SimpleNamespace
from uuid import uuid4

import httpx2
import pytest
from openai import AsyncOpenAI
from opentelemetry.instrumentation.utils import is_instrumentation_enabled

from common.ai_context import AIError, document_tokens
from common.remark_document_v1 import plain_to_remark, remark_literal_text
from config.env import TextFieldAISettings, get_config
from exceptions.exception import PermissionException
from module_admin.entity.vo.text_field_ai_vo import TextFieldAIRequest
from modules.system.application.services.ai_providers.openai_compatible import OpenAICompatibleProvider
from modules.system.application.services.text_field_ai_service import TextFieldAIService

SENTINEL = 'PRIVATE-NEVER-LOG-THIS'
ACTOR = SimpleNamespace(permissions=['system:post:add'])


def settings(**changes):
    return TextFieldAISettings(
        **{
            'ai_enabled': True,
            'ai_base_url': 'http://127.0.0.1:8123/v1',
            'ai_model': 'deployment-custom-model',
            **changes,
        }
    )


def body(service, **changes):
    status = service.status()
    return {
        'version': 'ai-context/v1',
        'requestId': str(uuid4()),
        'captureId': str(uuid4()),
        'manifestRevision': service.manifest_revision,
        'policyRevision': status.policyRevision or '0' * 64,
        'scope': 'system.post',
        'purpose': 'remark',
        'action': 'draft',
        'selectedContextIds': [],
        'profile': 'basic-rich-text',
        'instruction': '根据表单信息起草',
        'target': 'document',
        'document': None,
        'selection': None,
        'candidate': None,
        'context': [{'id': 'postName', 'label': '岗位名称', 'sensitivity': 'public', 'value': '设备维护'}],
        **changes,
    }


def text_root(text='负责设备维护', marks=None):
    return {
        'type': 'doc',
        'content': [
            {'type': 'paragraph', 'content': [{'type': 'text', 'text': text, **({'marks': marks} if marks else {})}]}
        ],
    }


def envelope(document=None, notices=None):
    return json.dumps({'document': document, 'notices': notices or []}, ensure_ascii=False)


def chunk(text='', finish=None):
    return (
        'data: '
        + json.dumps(
            {
                'id': 'chunk',
                'object': 'chat.completion.chunk',
                'created': 1,
                'model': 'deployment-custom-model',
                'choices': [{'index': 0, 'delta': {'content': text}, 'finish_reason': finish}],
            }
        )
        + '\n\n'
    ).encode()


class ProviderStream(httpx2.AsyncByteStream):
    def __init__(self, parts, wait=None):
        self.parts, self.wait = parts, wait
        self.closed = False
        self.waiting = asyncio.Event()

    async def __aiter__(self):
        for part in self.parts:
            if isinstance(part, Exception):
                raise part
            yield part
        if self.wait is not None:
            self.waiting.set()
            await self.wait.wait()

    async def aclose(self):
        self.closed = True


def provider_service(parts=None, *, status=200, wait=None, config=None):
    stream = ProviderStream(
        parts if parts is not None else [chunk(envelope(text_root())), chunk(finish='stop'), b'data: [DONE]\n\n'], wait
    )
    requests, clients = [], []

    def handler(incoming):
        assert not is_instrumentation_enabled()
        requests.append(incoming)
        return httpx2.Response(
            status,
            stream=stream,
            headers={'Content-Type': 'text/event-stream', 'Location': 'http://forbidden.test/leak'},
        )

    def factory(config):
        clients.append(True)
        return OpenAICompatibleProvider(config, transport=httpx2.MockTransport(handler))

    return TextFieldAIService(config or settings(), provider_factory=factory), stream, requests, clients


async def generate(service, **changes):
    payload = TextFieldAIRequest.model_validate(body(service, **changes))
    tokens = service.validate(payload, ACTOR)
    events = []

    async def emit(event):
        events.append(event)

    await service.produce(payload, tokens, emit)
    return events


async def test_sdk_uses_only_explicit_lan_endpoint_and_model_without_openai_auth(monkeypatch):
    for key in ('OPENAI_API_KEY', 'OPENAI_ADMIN_KEY', 'OPENAI_ORG_ID', 'OPENAI_PROJECT_ID', 'OPENAI_BASE_URL'):
        monkeypatch.setenv(key, SENTINEL)
    service, stream, requests, clients = provider_service()
    events = await generate(service)
    assert events[-1]['type'] == 'result'
    assert remark_literal_text(events[-1]['document']) == '负责设备维护'
    assert len(clients) == len(requests) == 1
    assert stream.closed
    request = requests[0]
    assert str(request.url) == 'http://127.0.0.1:8123/v1/chat/completions'
    assert 'authorization' not in request.headers
    assert SENTINEL not in str(request.headers)
    assert json.loads(request.content)['model'] == 'deployment-custom-model'
    data = json.loads(json.loads(request.content)['messages'][1]['content'])
    assert data['purposeLabel'] == '岗位备注' and data['noticeContextIds'] == ['postName', 'postCode', 'status']
    assert not {'version', 'requestId', 'captureId', 'manifestRevision', 'policyRevision'} & data.keys()


@pytest.mark.parametrize(
    'config',
    [
        TextFieldAISettings(),
        settings(ai_enabled=False),
        settings(ai_base_url=''),
        settings(ai_model=''),
        settings(ai_auth_mode='bearer'),
        settings(ai_base_url='https://user:password@example.test/v1'),
        settings(ai_base_url='http://@127.0.0.1/v1'),
        settings(ai_base_url='http://127.0.0.1/v1?'),
        settings(ai_base_url='http://127.0.0.1/v1#'),
        settings(ai_context_personal_policy='plain'),
    ],
)
def test_disabled_or_incomplete_configuration_never_constructs_provider(config, monkeypatch):
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *_args, **_kwargs: pytest.fail('DNS attempted'))
    service, _, requests, clients = provider_service(config=config)
    assert not service.status().available
    with pytest.raises(AIError, match='provider-unavailable'):
        service.validate(TextFieldAIRequest.model_validate(body(service)), ACTOR)
    assert not requests and not clients
    assert plain_to_remark('普通编辑照常可用', identity_key='test')


@pytest.mark.parametrize(
    'changes,code',
    [
        ({'manifestRevision': '0' * 64}, 'context-rejected'),
        ({'scope': 'system.unknown'}, 'context-rejected'),
        ({'purpose': 'unknown'}, 'context-rejected'),
        ({'policyRevision': '0' * 64}, 'policy-rejected'),
        ({'action': 'rewrite'}, 'context-rejected'),
        (
            {'context': [{'id': 'postName', 'label': SENTINEL, 'sensitivity': 'public', 'value': 'x'}]},
            'context-rejected',
        ),
        (
            {'context': [{'id': 'password', 'label': '密码', 'sensitivity': 'public', 'value': SENTINEL}]},
            'context-rejected',
        ),
    ],
)
def test_admission_rejections_never_construct_provider(changes, code):
    service, _, requests, clients = provider_service()
    with pytest.raises(AIError, match=code):
        service.validate(TextFieldAIRequest.model_validate(body(service, **changes)), ACTOR)
    assert not clients and not requests


@pytest.mark.parametrize(
    'scope',
    [
        'system.user',
        'system.role',
        'system.post',
        'system.dict.type',
        'system.dict.data',
        'system.config',
        'tool.gen.table',
    ],
)
def test_manifest_any_of_permission_uses_full_permissions(scope):
    service, _, _, clients = provider_service()
    meta = service.manifest.scopes[scope]
    payload = TextFieldAIRequest.model_validate(body(service, scope=scope, context=[]))
    for permission in meta.permissions.values:
        service.validate(payload, SimpleNamespace(permissions=[permission]))
    with pytest.raises(PermissionException):
        service.validate(payload, SimpleNamespace(permissions=['tool:gen:add']))
    assert not clients


@pytest.mark.parametrize('status', [401, 429, 307, 308, 500])
async def test_sdk_no_retry_or_redirect_and_upstream_auth_is_provider_unavailable(status):
    service, stream, requests, _ = provider_service([], status=status)
    with pytest.raises(AIError, match='provider-unavailable'):
        await generate(service)
    assert len(requests) == 1 and stream.closed


@pytest.mark.parametrize(
    'parts,code',
    [
        ([chunk(envelope(text_root()))], 'incomplete-output'),
        ([chunk(envelope(text_root())), chunk(finish='length')], 'output-limit'),
        ([chunk(envelope(text_root())), chunk(finish='stop'), RuntimeError(SENTINEL)], 'provider-unavailable'),
        ([chunk(''), chunk(finish='stop')], 'invalid-output'),
        ([chunk('{broken'), chunk(finish='stop')], 'invalid-output'),
        ([chunk(envelope()), chunk(finish='stop')], 'invalid-output'),
        ([chunk(envelope(text_root('{{PHONE_1}}'))), chunk(finish='stop')], 'invalid-output'),
    ],
)
async def test_sdk_terminal_and_output_rules(parts, code):
    service, stream, _, _ = provider_service(parts)
    try:
        await generate(service)
    except RuntimeError:
        # Unexpected adapter faults are mapped at the streaming service boundary, never returned verbatim.
        assert code == 'provider-unavailable'
    except AIError as error:
        assert error.code == code
    else:
        pytest.fail('invalid candidate accepted')
    assert stream.closed


async def test_notice_only_is_a_valid_terminal_result():
    service, stream, _, _ = provider_service(
        [
            chunk(envelope(notices=[{'code': 'information-unavailable', 'contextIds': ['postCode']}])),
            chunk(finish='stop'),
        ]
    )
    events = await generate(service)
    assert events == [
        {
            'type': 'result',
            'document': None,
            'notices': [{'code': 'information-unavailable', 'contextIds': ['postCode']}],
            'meta': {'promptVersion': 'text-field/v1', 'model': 'deployment-custom-model', 'contextIds': ['postName']},
        }
    ]
    assert stream.closed


@pytest.mark.parametrize(
    'document',
    [
        text_root('{{PHONE_1}}', [{'type': 'link', 'attrs': {'href': 'https://example.test/{{PHONE_1}}'}}]),
        text_root('x', [{'type': 'link', 'attrs': {'href': 'https://example.test/%7B%7BPHONE_1%7D%7D'}}]),
        {
            'type': 'doc',
            'content': [
                {
                    'type': 'paragraph',
                    'content': [{'type': 'text', 'text': '{'}, {'type': 'text', 'text': '{PHONE_1}}'}],
                }
            ],
        },
    ],
)
def test_tokens_cannot_hide_in_attributes_or_split_across_text_nodes(document):
    with pytest.raises(ValueError):
        document_tokens(document)


async def test_cancel_and_timeout_close_the_actual_sdk_stream():
    for timeout in (False, True):
        wait = asyncio.Event()
        service, stream, _, _ = provider_service(
            [chunk('{"document":')], wait=wait, config=settings(ai_text_field_timeout_seconds=0.1 if timeout else 90)
        )
        task = asyncio.create_task(generate(service))
        await asyncio.wait_for(stream.waiting.wait(), timeout=1)
        if timeout:
            with pytest.raises(TimeoutError):
                await task
        else:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert stream.closed


def test_optional_sdk_absence_does_not_prevent_application_import():
    script = r"""
import importlib.abc, socket, sys
class NoOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'openai', 'httpx2', 'sse_starlette'}:
            raise AssertionError('optional SDK imported while AI is disabled')
sys.meta_path.insert(0, NoOptional())
def forbidden(*args, **kwargs):
    raise AssertionError('network attempted while AI is disabled')
socket.getaddrinfo = forbidden
socket.socket.connect = forbidden
from utils.log_util import logger
logger.remove()
import server
from modules.system.api.text_field_ai_controller import provide_text_field_ai_service
assert not provide_text_field_ai_service().status().available
print('disabled-app-import-ok')
"""
    result = subprocess.run(
        [sys.executable, '-c', script],
        env={**os.environ, 'AI_ENABLED': 'false'},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert 'disabled-app-import-ok' in result.stdout


def test_invalid_optional_env_fails_closed_without_echo(monkeypatch):
    monkeypatch.setenv('AI_ENABLED', 'true')
    monkeypatch.setenv('AI_TEXT_FIELD_CONCURRENCY', SENTINEL)
    config = get_config.get_text_field_ai_config()
    assert not config.ai_enabled and not config.is_configured


def test_corrupt_manifest_disables_ai_without_provider_construction(tmp_path):
    path = tmp_path / 'bad.json'
    path.write_text('{"version":"ai-context/v1","scopes":{"system.x":{}}}')
    service, _, requests, clients = provider_service(config=settings(ai_context_manifest_path=str(path)))
    status = service.status()
    assert not status.available and status.manifestRevision is None
    assert not clients and not requests


@pytest.mark.parametrize('kind,value', [('phone', '{{EMAIL_1}}'), ('phone', SENTINEL), ('other', '{{PHONE_1}}')])
def test_mask_requires_whole_typed_personal_tokens(kind, value):
    service, _, _, clients = provider_service()
    payload = TextFieldAIRequest.model_validate(
        body(
            service,
            scope='system.user',
            action='include-context',
            selectedContextIds=['phonenumber'],
            context=[
                {'id': 'phonenumber', 'label': '手机号码', 'sensitivity': 'personal', 'kind': kind, 'value': value}
            ],
        )
    )
    with pytest.raises(AIError):
        service.validate(payload, SimpleNamespace(permissions=['system:user:edit']))
    assert not clients


async def test_masked_personal_result_keeps_only_supplied_tokens_and_suppresses_tracing():
    service, stream, _, _ = provider_service([chunk(envelope(text_root('联系 {{PHONE_1}}'))), chunk(finish='stop')])
    payload = TextFieldAIRequest.model_validate(
        body(
            service,
            scope='system.user',
            action='include-context',
            selectedContextIds=['phonenumber'],
            context=[
                {
                    'id': 'phonenumber',
                    'label': '手机号码',
                    'sensitivity': 'personal',
                    'kind': 'phone',
                    'value': '{{PHONE_1}}',
                }
            ],
        )
    )
    tokens = service.validate(payload, SimpleNamespace(permissions=['system:user:edit']))
    events = []

    async def emit(event):
        events.append(event)

    await service.produce(payload, tokens, emit)
    assert remark_literal_text(events[-1]['document']) == '联系 {{PHONE_1}}' and stream.closed


async def test_product_adapter_real_loopback_http_without_dns_or_any_public_connection(monkeypatch, caplog):
    caplog.set_level('DEBUG')
    received, connected, clients = [], [], []
    finished = asyncio.Event()

    async def handle(reader, writer):
        try:
            head = await reader.readuntil(b'\r\n\r\n')
            length = next(
                int(line.split(b':', 1)[1])
                for line in head.split(b'\r\n')
                if line.lower().startswith(b'content-length:')
            )
            payload = await reader.readexactly(length)
            received.append((head, json.loads(payload)))
            content = chunk(envelope(text_root())) + chunk(finish='stop') + b'data: [DONE]\n\n'
            writer.write(
                b'HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nX-Request-Id: '
                + SENTINEL.encode()
                + b'\r\nConnection: close\r\nContent-Length: '
                + str(len(content)).encode()
                + b'\r\n\r\n'
                + content
            )
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            finished.set()

    server = await asyncio.start_server(handle, '127.0.0.1', 0)
    port = server.sockets[0].getsockname()[1]
    connect = socket.socket.connect

    def only_loopback(sock, address):
        assert address[0] == '127.0.0.1' and address[1] == port, 'unexpected provider destination'
        connected.append(address)
        return connect(sock, address)

    def no_dns(*_args, **_kwargs):
        pytest.fail('provider DNS was attempted')

    monkeypatch.setattr(socket.socket, 'connect', only_loopback)
    monkeypatch.setattr(socket, 'getaddrinfo', no_dns)
    monkeypatch.setenv('OPENAI_API_KEY', SENTINEL)
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://forbidden.invalid/v1')

    def client_factory(**kwargs):
        client = AsyncOpenAI(**kwargs)
        clients.append(client)
        return client

    config = settings(ai_base_url=f'http://127.0.0.1:{port}/v1')
    service = TextFieldAIService(
        config, provider_factory=lambda config: OpenAICompatibleProvider(config, client_factory=client_factory)
    )
    try:
        events = await generate(service)
        await asyncio.wait_for(finished.wait(), timeout=2)
        assert events[-1]['type'] == 'result'
        assert len(received) == len(connected) == len(clients) == 1
        assert all(client.is_closed() for client in clients)
        head, payload = received[0]
        assert head.startswith(b'POST /v1/chat/completions HTTP/1.1')
        assert b'authorization:' not in head.lower() and SENTINEL.encode() not in head
        assert payload['model'] == 'deployment-custom-model'
        assert SENTINEL not in caplog.text
    finally:
        server.close()
        await server.wait_closed()


async def test_context_values_preserve_surrounding_whitespace_at_the_provider_boundary():
    service, _, requests, _ = provider_service()
    value = ' 设备维护 \n'
    await generate(service, context=[{'id': 'postName', 'label': '岗位名称', 'sensitivity': 'public', 'value': value}])
    data = json.loads(json.loads(requests[0].content)['messages'][1]['content'])
    assert data['context'][0]['value'] == value
