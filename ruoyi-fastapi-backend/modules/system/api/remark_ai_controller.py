"""Authenticated AI draft endpoint; generated content is never persisted here."""

import asyncio
import json
from contextlib import aclosing, suppress

from fastapi import APIRouter, Depends

from config.env import RemarkAIConfig
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.remark_ai_vo import RemarkAIRequest, RemarkAIStatus
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.system.application.services.remark_ai_service import RemarkAIService
from utils.response_util import ResponseUtil

remark_ai_router = APIRouter(prefix='/system/remark/ai', dependencies=[Depends(get_current_user)])
PERMISSION_AREAS = {
    'user': 'system:user',
    'role': 'system:role',
    'post': 'system:post',
    'dictType': 'system:dict',
    'dictData': 'system:dict',
    'config': 'system:config',
    'genTable': 'tool:gen',
}


def provide_remark_ai_service():
    return RemarkAIService(RemarkAIConfig)


@remark_ai_router.get('/status', response_model=RemarkAIStatus)
async def get_remark_ai_status(service: RemarkAIService = Depends(provide_remark_ai_service)):
    return RemarkAIStatus(available=service.available)


async def stream_remark_events(events):
    """Keep the connection alive and cancel/close the provider when the browser disconnects."""
    queue = asyncio.Queue(maxsize=1)

    async def produce():
        # One task must own the complete provider iterator: its total timeout is task-scoped.
        async with aclosing(events):
            try:
                async for event in events:
                    await queue.put(event)
            except Exception:
                # Do not let unexpected provider diagnostics expose prompts in framework logs.
                await queue.put(
                    {'type': 'error', 'code': 'provider-unavailable', 'message': 'AI 服务暂不可用，请稍后重试'}
                )
        await queue.put(None)

    producer = asyncio.create_task(produce())
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=10)
            except TimeoutError:
                yield ': heartbeat\n\n'
                continue
            if event is None:
                return
            yield 'data: ' + json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n\n'
    finally:
        producer.cancel()
        with suppress(asyncio.CancelledError):
            await producer


@remark_ai_router.post(
    '/generate',
    responses={200: {'content': {'text/event-stream': {}}, 'description': 'SSE delta / result / error events'}},
)
async def generate_remark_ai(
    payload: RemarkAIRequest,
    current_user: CurrentUserModel = Depends(get_current_user),
    service: RemarkAIService = Depends(provide_remark_ai_service),
):
    area = PERMISSION_AREAS[payload.scene]
    permissions = [f'{area}:edit'] if payload.scene == 'genTable' else [f'{area}:add', f'{area}:edit']
    CheckUserInterfaceAuth(permissions)(current_user)
    service.ensure_available()
    return ResponseUtil.streaming(
        data=stream_remark_events(service.generate(payload)),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-store',
            'X-Accel-Buffering': 'no',
            # Starlette 0.45's GZipMiddleware otherwise buffers incremental SSE output.
            'Content-Encoding': 'identity',
        },
    )
