"""Real ASGI admission, rate limiting, final audit and streaming lifecycle without a database/model."""

import asyncio
import copy
import json
from types import SimpleNamespace

import httpx2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.gzip import GZipMiddleware

from exceptions.exception import AuthException
from middlewares.rate_limit_middleware import RateLimitASGIMiddleware
from middlewares.text_field_ai_middleware import TextFieldAIEntryMiddleware
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.system.api import text_field_ai_controller as controller
from modules.system.api import text_field_ai_stream
from modules.system.api.text_field_ai_openapi import install_text_field_ai_openapi
from modules.system.api.text_field_ai_stream import PrivateEventSourceResponse as RealEventSourceResponse
from modules.system.application.services.ai_providers.openai_compatible import OpenAICompatibleProvider
from modules.system.application.services.text_field_ai_service import TextFieldAIService
from resilience.bulkhead import BulkheadRegistry
from tests.unit.services.test_text_field_ai import (
    SENTINEL,
    ProviderStream,
    body,
    chunk,
    envelope,
    provider_service,
    settings,
    text_root,
)
from utils.log_util import logger
from utils.prometheus_metrics import PrometheusMetricsRegistry


def make_app(service, *, rate=False):
    app = FastAPI()
    app.include_router(controller.text_field_ai_router)
    actor = CurrentUserModel(permissions=['system:post:add'], roles=[], user=UserInfoModel(userId=2, userName='editor'))

    async def get_user():
        return actor

    records = []

    async def audit_writer(record):
        records.append(copy.deepcopy(record))

    app.dependency_overrides[controller.get_current_user] = get_user
    app.dependency_overrides[controller.provide_text_field_ai_service] = lambda: service
    app.state.resilience_runtime = SimpleNamespace(bulkhead_registry=BulkheadRegistry())
    app.state.text_field_ai_audit_writer = audit_writer
    app.state.metrics_registry = PrometheusMetricsRegistry()
    if rate:
        app.add_middleware(RateLimitASGIMiddleware, ai_user_limit=1, ai_ip_limit=2)
    app.add_middleware(GZipMiddleware, minimum_size=1)
    app.add_middleware(TextFieldAIEntryMiddleware)
    return app, actor, records


@pytest.fixture
def context():
    service, stream, requests, clients = provider_service()
    app, actor, records = make_app(service)
    with TestClient(app) as client:
        yield SimpleNamespace(
            service=service,
            stream=stream,
            requests=requests,
            clients=clients,
            app=app,
            actor=actor,
            records=records,
            client=client,
        )


def post(ctx, **changes):
    return ctx.client.post('/system/ai/text-field/generate', json=body(ctx.service, **changes))


def events(response):
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]


def test_status_reveals_only_public_policy_and_no_model_address_or_key(context):
    result = context.client.get('/system/ai/text-field/status')
    assert result.status_code == 200
    status = result.json()
    assert status['available'] and len(status['manifestRevision']) == len(status['policyRevision']) == 64
    assert not any(key in result.text for key in ('127.0.0.1', 'deployment-custom-model', 'api_key'))
    assert not context.requests and not context.clients


def test_sse_success_ids_and_safe_audit_are_finalized_after_provider_closed(context):
    payload = body(context.service)
    response = context.client.post('/system/ai/text-field/generate', json=payload)
    assert response.status_code == 200
    assert response.headers['content-encoding'] == 'identity'
    assert response.headers['cache-control'] == 'no-store'
    frames = events(response)
    assert frames[-1]['type'] == 'result'
    assert all(
        frame['requestId'] == payload['requestId'] and frame['captureId'] == payload['captureId'] for frame in frames
    )
    assert context.stream.closed
    assert len(context.records) == 1
    record = context.records[0]
    assert record['outcome'] == 'completed' and record['contextIds'] == ['postName']
    assert record['counts'] == {'public': 1, 'personal': 0}
    assert '设备维护' not in json.dumps(record, ensure_ascii=False)
    assert (
        'text_field_ai_requests_total{outcome="completed"} 1'
        in context.app.state.metrics_registry.render_http_metrics()
    )


@pytest.mark.parametrize('kind,status', [('auth', 401), ('vo', 422), ('permission', 403), ('policy', 403)])
def test_rejected_requests_are_audited_once_and_never_log_payload(context, kind, status):
    if kind == 'auth':

        async def unauthorized():
            raise AuthException()

        context.app.dependency_overrides[controller.get_current_user] = unauthorized
    if kind == 'permission':
        context.actor.permissions = []
    changes = {'instruction': SENTINEL}
    if kind == 'vo':
        changes[SENTINEL] = SENTINEL
    if kind == 'policy':
        changes['policyRevision'] = '0' * 64
    logs = []
    sink = logger.add(lambda message: logs.append(str(message)))
    try:
        response = post(context, **changes)
    finally:
        logger.remove(sink)
    assert response.status_code == status
    assert SENTINEL not in response.text + '\n'.join(logs) + json.dumps(context.records)
    assert len(context.records) == 1
    assert not context.clients and not context.requests


def test_disabled_service_is_a_safe_503_and_ordinary_codec_remains_available(context):
    disabled, _, _, _ = provider_service(config=settings(ai_enabled=False))
    context.app.dependency_overrides[controller.provide_text_field_ai_service] = lambda: disabled
    response = context.client.post('/system/ai/text-field/generate', json=body(disabled))
    assert response.status_code == 503 and response.json()['aiCode'] == 'provider-unavailable'
    assert not context.requests and len(context.records) == 1
    assert not context.client.get('/system/ai/text-field/status').json()['available']


def test_ai_rate_limit_rejects_before_model_and_audits_the_middleware_429():
    service, _, requests, _ = provider_service()
    app, _, records = make_app(service, rate=True)
    with TestClient(app) as client:
        assert client.post('/system/ai/text-field/generate', json=body(service)).status_code == 200
        # The second stream uses the already consumed fixture stream but still counts as an attempt.
        assert client.post('/system/ai/text-field/generate', json=body(service)).status_code == 200
        response = client.post('/system/ai/text-field/generate', json=body(service))
    assert response.status_code == 429 and response.json()['aiCode'] == 'quota-exceeded'
    assert len(requests) == 2 and len(records) == 3
    assert records[-1]['outcome'] == 'quota-exceeded' and records[-1]['scope'] == 'unknown'


async def test_bulkhead_permit_covers_upstream_until_disconnect_and_then_closes():
    service, stream, _, _ = provider_service([chunk('{"document":')], wait=asyncio.Event())
    app, _, records = make_app(service)
    disconnect = asyncio.Event()
    sent = []
    payload = json.dumps(body(service)).encode()
    delivered = False

    async def receive():
        nonlocal delivered
        if not delivered:
            delivered = True
            return {'type': 'http.request', 'body': payload, 'more_body': False}
        await disconnect.wait()
        return {'type': 'http.disconnect'}

    async def send(message):
        sent.append(message)

    scope = {
        'type': 'http',
        'asgi': {'version': '3.0'},
        'http_version': '1.1',
        'scheme': 'http',
        'method': 'POST',
        'path': '/system/ai/text-field/generate',
        'raw_path': b'/system/ai/text-field/generate',
        'root_path': '',
        'query_string': b'',
        'headers': [(b'content-type', b'application/json')],
        'client': ('127.0.0.1', 1234),
        'server': ('test', 80),
    }
    task = asyncio.create_task(app(scope, receive, send))
    await asyncio.wait_for(stream.waiting.wait(), timeout=2)
    pools = await app.state.resilience_runtime.bulkhead_registry.list_snapshots()
    assert pools[0]['active'] == 1
    assert not stream.closed and not records
    disconnect.set()
    await asyncio.wait_for(task, timeout=2)
    assert stream.closed
    assert (await app.state.resilience_runtime.bulkhead_registry.list_snapshots())[0]['active'] == 0
    assert len(records) == 1 and records[0]['outcome'] == 'cancelled'


def test_user_rate_quota_is_independent_of_ip_quota():
    service, _, requests, _ = provider_service()
    app, _, records = make_app(service, rate=True)

    class TokenService:
        async def extract_user_context_from_token(self, _token):
            return {'userId': 2}

    app.state.security_token_service = TokenService()
    with TestClient(app) as client:
        headers = {'Authorization': 'Bearer synthetic-user-token'}
        assert client.post('/system/ai/text-field/generate', json=body(service), headers=headers).status_code == 200
        assert client.post('/system/ai/text-field/generate', json=body(service), headers=headers).status_code == 429
    assert len(requests) == 1 and len(records) == 2
    assert records[-1]['outcome'] == 'quota-exceeded'


def test_audit_failure_is_once_and_content_free(context):
    attempts = []

    async def fail(record):
        attempts.append(record)
        raise RuntimeError(SENTINEL)

    context.app.state.text_field_ai_audit_writer = fail
    logs = []
    sink = logger.add(lambda message: logs.append(str(message)))
    try:
        response = post(context, instruction=SENTINEL)
    finally:
        logger.remove(sink)
    assert events(response)[-1]['type'] == 'result'
    assert len(attempts) == 1 and SENTINEL not in json.dumps(attempts) + ''.join(logs)
    assert 'text_field_ai_audit_failures_total 1' in context.app.state.metrics_registry.render_http_metrics()


def test_sdk_error_body_and_prompt_never_escape_http_sse_or_debug_logs(caplog):
    service, stream, requests, _ = provider_service([b'data: {"error":{"message":"' + SENTINEL.encode() + b'"}}\n\n'])
    app, _, records = make_app(service)
    with caplog.at_level('DEBUG'), TestClient(app) as client:
        response = client.post('/system/ai/text-field/generate', json=body(service, instruction=SENTINEL))
    assert events(response)[-1]['type'] == 'error'
    assert events(response)[-1]['code'] == 'provider-unavailable'
    assert SENTINEL not in response.text + caplog.text + json.dumps(records)
    assert len(requests) == 1 and stream.closed


def test_large_or_malformed_request_has_safe_bounded_422(context):
    for data in ('{"instruction":', 'x' * 1048577):
        response = context.client.post(
            '/system/ai/text-field/generate', content=data, headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 422
        assert response.json()['aiCode'] == 'context-rejected'
    assert not context.clients and len(context.records) == 2


async def asgi_request(app, payload, *, disconnect=None, send_hook=None):
    sent, delivered = [], False
    disconnected = disconnect or asyncio.Event()

    async def receive():
        nonlocal delivered
        if not delivered:
            delivered = True
            return {'type': 'http.request', 'body': json.dumps(payload).encode(), 'more_body': False}
        await disconnected.wait()
        return {'type': 'http.disconnect'}

    async def send(message):
        sent.append(message)
        if send_hook:
            await send_hook(message)

    scope = {
        'type': 'http',
        'asgi': {'version': '3.0'},
        'http_version': '1.1',
        'scheme': 'http',
        'method': 'POST',
        'path': '/system/ai/text-field/generate',
        'raw_path': b'/system/ai/text-field/generate',
        'root_path': '',
        'query_string': b'',
        'headers': [(b'content-type', b'application/json')],
        'client': ('127.0.0.1', 1234),
        'server': ('test', 80),
    }
    await app(scope, receive, send)
    return sent


async def test_two_live_streams_hold_permits_saturation_is_finite_and_disconnect_releases_all():
    streams = []

    def factory(config):
        def handler(_request):
            stream = ProviderStream([chunk('{"document":')], wait=asyncio.Event())
            streams.append(stream)
            return httpx2.Response(200, stream=stream, headers={'Content-Type': 'text/event-stream'})

        return OpenAICompatibleProvider(config, transport=httpx2.MockTransport(handler))

    service = TextFieldAIService(
        settings(ai_text_field_concurrency=2, ai_text_field_wait_seconds=0.01), provider_factory=factory
    )
    app, _, records = make_app(service)
    disconnect = asyncio.Event()
    tasks = [asyncio.create_task(asgi_request(app, body(service), disconnect=disconnect)) for _ in range(2)]
    async with asyncio.timeout(2):
        while len(streams) < 2 or not all(stream.waiting.is_set() for stream in streams):
            await asyncio.sleep(0.001)
    assert (await app.state.resilience_runtime.bulkhead_registry.list_snapshots())[0]['active'] == 2
    rejected = await asyncio.wait_for(asgi_request(app, body(service)), timeout=2)
    assert b'"code":"provider-unavailable"' in b''.join(message.get('body', b'') for message in rejected)
    assert len(streams) == 2 and not any(stream.closed for stream in streams)
    disconnect.set()
    await asyncio.wait_for(asyncio.gather(*tasks), timeout=2)
    assert all(stream.closed for stream in streams)
    assert (await app.state.resilience_runtime.bulkhead_registry.list_snapshots())[0]['active'] == 0
    assert sorted(record['outcome'] for record in records) == ['cancelled', 'cancelled', 'provider-unavailable']


async def test_asgi_heartbeat_remains_incremental_under_gzip_and_slow_sender_closes_provider(monkeypatch):
    def fast_response(*args, **kwargs):
        return RealEventSourceResponse(*args, **{**kwargs, 'ping': 0.01, 'send_timeout': 0.03})

    monkeypatch.setattr(text_field_ai_stream, 'PrivateEventSourceResponse', fast_response)
    for slow in (False, True):
        service, stream, _, _ = provider_service([chunk('{"document":')], wait=asyncio.Event())
        app, _, records = make_app(service)
        disconnect = asyncio.Event()
        saw_ping = asyncio.Event()

        async def sending(message, saw_ping=saw_ping, slow=slow, disconnect=disconnect):
            if b': ping' in message.get('body', b''):
                saw_ping.set()
                if slow:
                    await asyncio.Event().wait()
                else:
                    disconnect.set()

        task = asyncio.create_task(asgi_request(app, body(service), disconnect=disconnect, send_hook=sending))
        await asyncio.wait_for(saw_ping.wait(), timeout=2)
        await asyncio.wait_for(task, timeout=2)
        assert stream.closed and len(records) == 1
        assert (await app.state.resilience_runtime.bulkhead_registry.list_snapshots())[0]['active'] == 0


def test_sse_library_debug_logging_cannot_record_generated_document(caplog):
    service, _, _, _ = provider_service([chunk(envelope(text_root(SENTINEL))), chunk(finish='stop')])
    app, _, records = make_app(service)
    with caplog.at_level('DEBUG'), TestClient(app) as client:
        response = client.post('/system/ai/text-field/generate', json=body(service))
    assert events(response)[-1]['type'] == 'result'
    assert SENTINEL in response.text
    assert SENTINEL not in caplog.text + json.dumps(records)


def test_openapi_explicit_union_has_resolvable_refs_and_problem_details(context):
    install_text_field_ai_openapi(context.app)
    schema = context.app.openapi()
    responses = schema['paths']['/system/ai/text-field/generate']['post']['responses']
    assert set(responses['200']['content']) == {'text/event-stream'}
    event = responses['200']['content']['text/event-stream']['schema']
    assert event['discriminator']['propertyName'] == 'type' and len(event['oneOf']) == 3
    for status in ('401', '403', '422', '429', '503'):
        assert set(responses[status]['content']) == {'application/problem+json'}

    def refs(value):
        if isinstance(value, dict):
            if '$ref' in value:
                target = schema
                for part in value['$ref'].removeprefix('#/').split('/'):
                    target = target[part]
            for item in value.values():
                refs(item)
        elif isinstance(value, list):
            for item in value:
                refs(item)

    refs(schema)


def test_authentication_precedes_json_parsing_and_body_receive(context):
    async def unauthorized():
        raise AuthException()

    context.app.dependency_overrides[controller.get_current_user] = unauthorized
    response = context.client.post(
        '/system/ai/text-field/generate', content='malformed-' + SENTINEL, headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 401
    assert SENTINEL not in response.text + json.dumps(context.records)
    assert len(context.records) == 1 and not context.clients
