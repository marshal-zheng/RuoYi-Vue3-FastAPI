"""Content-free AI entry auditing and bounded receive; never inspect unvalidated request bodies."""

import time

import anyio

from modules.system.application.services.ai_providers.base import MESSAGES, AIError
from modules.system.application.services.text_field_ai_audit import write_ai_audit
from utils.log_util import logger

AI_GENERATE_PATH = '/system/ai/text-field/generate'
MAX_REQUEST_BYTES = 1048576


def ai_route_path(scope):
    path, root = scope.get('path', ''), scope.get('root_path', '')
    return path[len(root) :] if root and (path == root or path.startswith(root + '/')) else path


class TextFieldAIEntryMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get('type') != 'http' or scope.get('method') != 'POST' or ai_route_path(scope) != AI_GENERATE_PATH:
            await self.app(scope, receive, send)
            return
        state = scope.setdefault('state', {})
        audit = {
            'userId': 'anonymous',
            'scope': 'unknown',
            'purpose': 'unknown',
            'contextIds': [],
            'counts': {'public': 0, 'personal': 0},
            'maskedCount': 0,
            'outcome': 'pending',
        }
        state['text_field_ai_audit'] = audit
        started, status, ended, received = time.perf_counter(), 500, False, 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            if message.get('type') == 'http.request':
                received += len(message.get('body', b''))
                if received > MAX_REQUEST_BYTES:
                    raise AIError('context-rejected')
            return message

        async def observed_send(message):
            nonlocal status, ended
            if message.get('type') == 'http.response.start':
                status = message['status']
                for key, value in message.get('headers', []):
                    if key.lower() == b'x-request-id':
                        audit['requestId'] = value.decode('latin-1')[:128]
            await send(message)
            if message.get('type') == 'http.response.body' and not message.get('more_body', False):
                ended = True

        try:
            await self.app(scope, bounded_receive, observed_send)
        finally:
            if not ended:
                audit['outcome'] = 'cancelled'
            elif status >= 400 and audit['outcome'] == 'pending':
                audit['outcome'] = {
                    401: 'permission-denied',
                    403: 'permission-denied',
                    422: 'context-rejected',
                    429: 'quota-exceeded',
                    503: 'provider-unavailable',
                }.get(status, 'context-rejected')
            if audit.get('outcome') not in {*MESSAGES, 'completed', 'cancelled'}:
                audit['outcome'] = 'provider-unavailable'
            audit['latencyMs'] = max(0, round((time.perf_counter() - started) * 1000))
            if not state.get('text_field_ai_audit_attempted'):
                state['text_field_ai_audit_attempted'] = True
                app_state = scope['app'].state
                metrics = getattr(app_state, 'metrics_registry', None)
                if metrics:
                    metrics.observe_text_field_ai(audit['outcome'], audit['latencyMs'] / 1000)
                writer = getattr(app_state, 'text_field_ai_audit_writer', write_ai_audit)
                failed = False
                with anyio.CancelScope(shield=True), anyio.move_on_after(2) as cleanup:
                    try:
                        await writer(dict(audit))
                    except Exception:
                        failed = True
                if failed or cleanup.cancel_called:
                    logger.warning('text_field_ai audit-write-failed')
                    if metrics:
                        metrics.observe_text_field_ai_audit_failure()
