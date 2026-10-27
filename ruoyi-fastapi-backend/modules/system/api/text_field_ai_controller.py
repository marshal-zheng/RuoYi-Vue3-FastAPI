# ruff: noqa: PLC0415 -- Optional SSE transport is imported only for an admitted request.
"""Authenticated field AI API. Admission precedes streaming; no request-body Log decorator."""

import asyncio
import json
from contextlib import suppress
from functools import lru_cache

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException

from common.ai_context import MESSAGES, TOKEN, AIError
from config.env import TextFieldAIConfig
from config.error_codes import ErrorCode
from exceptions.exception import AppException, PermissionException
from module_admin.entity.vo.text_field_ai_vo import (
    TextFieldAIProblem,
    TextFieldAIRequest,
    TextFieldAIStatus,
)
from modules.identity.ports import get_current_user
from modules.system.application.services.text_field_ai_service import TextFieldAIService
from resilience.bulkhead import BulkheadRejectedError
from resilience.models import BulkheadConfig
from utils.response_util import ResponseUtil

HTTP_ERRORS = {
    'context-rejected': (422, ErrorCode.VALIDATION_ERROR),
    'policy-rejected': (403, ErrorCode.FORBIDDEN),
    'permission-denied': (403, ErrorCode.FORBIDDEN),
    'provider-unavailable': (503, ErrorCode.EXTERNAL_SERVICE_ERROR),
}


def problem(request, code, status=None, error_code=None):
    http_status, number = HTTP_ERRORS[code]
    audit = getattr(request.state, 'text_field_ai_audit', None)
    if audit is not None:
        audit['outcome'] = code
    return ResponseUtil.problem_details(
        request=request,
        http_status=status or http_status,
        error_code=error_code or number,
        title=MESSAGES[code],
        extensions={'aiCode': code},
    )


class SafeAIRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe(request):
            try:
                return await handler(request)
            except (RequestValidationError, ValueError, TypeError, RecursionError):
                return problem(request, 'context-rejected')
            except AIError as error:
                return problem(request, error.code)
            except AppException as error:
                code = 'permission-denied' if error.http_status in {401, 403} else 'context-rejected'
                return problem(request, code, error.http_status, error.error_code)
            except HTTPException as error:
                if error.status_code == 400:
                    return problem(request, 'context-rejected')
                return problem(
                    request, 'permission-denied', error.status_code, 20001 if error.status_code == 401 else 20004
                )

        return safe


@lru_cache
def provide_text_field_ai_service():
    return TextFieldAIService(TextFieldAIConfig)


async def ai_user(request: Request, current_user=Depends(get_current_user)):
    audit = getattr(request.state, 'text_field_ai_audit', None)
    if audit is not None:
        audit['userId'] = current_user.user.user_id
    return current_user


async def read_ai_payload(request: Request, _user=Depends(ai_user)):
    # FastAPI reads Body parameters before dependencies. Parse here so IAM precedes JSON/VO work.
    return TextFieldAIRequest.model_validate(await request.json())


text_field_ai_router = APIRouter(
    prefix='/system/ai/text-field', route_class=SafeAIRoute, dependencies=[Depends(ai_user)]
)


@text_field_ai_router.get('/status', response_model=TextFieldAIStatus)
async def get_text_field_ai_status(service: TextFieldAIService = Depends(provide_text_field_ai_service)):
    return service.status()


async def stream_events(request, service, payload, tokens):
    queue = asyncio.Queue(maxsize=1)
    base = {'requestId': payload.requestId, 'captureId': payload.captureId}
    terminal = 'provider-unavailable'

    async def emit(event):
        await queue.put({**base, **event})

    async def produce():
        try:
            runtime = getattr(request.app.state, 'resilience_runtime', None)
            if runtime is None:
                raise AIError('provider-unavailable')
            settings = service.settings
            bulkhead = await runtime.bulkhead_registry.get_or_create(
                'text-field-ai',
                BulkheadConfig(
                    max_concurrency=settings.ai_text_field_concurrency,
                    max_wait_seconds=settings.ai_text_field_wait_seconds,
                ),
            )
            await bulkhead.run(lambda: service.produce(payload, tokens, emit))
        except asyncio.CancelledError:
            raise
        except (TimeoutError, AIError, BulkheadRejectedError) as error:
            code = (
                error.code
                if isinstance(error, AIError)
                else 'timeout'
                if isinstance(error, TimeoutError)
                else 'provider-unavailable'
            )
            await emit({'type': 'error', 'code': code, 'message': MESSAGES[code]})
        except Exception:
            await emit({'type': 'error', 'code': 'provider-unavailable', 'message': MESSAGES['provider-unavailable']})
        await queue.put(None)

    producer = asyncio.create_task(produce())
    try:
        while (event := await queue.get()) is not None:
            if event['type'] == 'result':
                terminal = 'completed'
            elif event['type'] == 'error':
                terminal = event['code']
            yield {'event': 'message', 'data': json.dumps(event, ensure_ascii=False, separators=(',', ':'))}
        request.state.text_field_ai_audit['outcome'] = terminal
    finally:
        producer.cancel()
        with suppress(asyncio.CancelledError):
            await producer


@text_field_ai_router.post(
    '/generate',
    responses={
        200: {
            'description': 'SSE message frames (comments are heartbeats)',
            'content': {
                'text/event-stream': {
                    'schema': {
                        'oneOf': [
                            {'$ref': '#/components/schemas/DeltaEvent'},
                            {'$ref': '#/components/schemas/ResultEvent'},
                            {'$ref': '#/components/schemas/ErrorEvent'},
                        ],
                        'discriminator': {'propertyName': 'type'},
                    }
                }
            },
        },
        **{status: {'model': TextFieldAIProblem} for status in (401, 403, 422, 429, 503)},
    },
)
async def generate_text_field_ai(
    request: Request,
    payload: TextFieldAIRequest = Depends(read_ai_payload),
    current_user=Depends(ai_user),
    service: TextFieldAIService = Depends(provide_text_field_ai_service),
):
    audit = getattr(request.state, 'text_field_ai_audit', None)
    if audit is None:
        # Only standalone embedding without the repository middleware reaches this guard.
        raise AIError('provider-unavailable')
    audit.update(clientRequestId=payload.requestId, captureId=payload.captureId)
    service.canonical_scope(payload)
    audit.update(scope=payload.scope, purpose=payload.purpose)
    try:
        tokens = service.validate(payload, current_user)
    except PermissionException:
        raise AIError('permission-denied') from None
    audit.update(
        contextIds=[item.id for item in payload.context],
        counts={key: sum(item.sensitivity == key for item in payload.context) for key in ('public', 'personal')},
        maskedCount=sum(bool(TOKEN.search(str(item.value))) for item in payload.context),
        promptVersion='text-field/v1',
        model=service.settings.ai_model,
    )
    # sse-starlette is optional, imported only for an admitted configured request.
    from modules.system.api.text_field_ai_stream import PrivateEventSourceResponse

    return PrivateEventSourceResponse(
        stream_events(request, service, payload, tokens),
        ping=10,
        send_timeout=10,
        headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no', 'Content-Encoding': 'identity'},
    )
