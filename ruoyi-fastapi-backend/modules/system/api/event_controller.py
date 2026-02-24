from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Request

from config.enums import BusinessType
from events.repositories import EventHistoryFilters
from events.schemas import EventHistoryQuery, EventReplayRequest
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from modules.identity.ports import get_current_user
from module_admin.entity.vo.user_vo import CurrentUserModel
from utils.log_util import logger
from utils.response_util import ResponseUtil


eventController = APIRouter(prefix='/events', dependencies=[Depends(get_current_user)])  # noqa: N816


@eventController.get('/history', dependencies=[Depends(CheckUserInterfaceAuth('monitor:event:query'))])
async def list_event_history(
    request: Request,
    query: EventHistoryQuery = Depends(),
):
    event_runtime = getattr(request.app.state, 'event_runtime', None)
    if event_runtime is None:
        return ResponseUtil.success(http_status=503, data={'status': 'unavailable', 'detail': 'event_runtime_not_initialized'})

    filters = EventHistoryFilters(
        aggregate_id=query.aggregate_id,
        aggregate_type=query.aggregate_type,
        event_type=query.event_type,
        begin_time=query.begin_time,
        end_time=query.end_time,
        page_num=query.page_num,
        page_size=query.page_size,
    )
    rows, total = await event_runtime.list_history(filters)
    logger.info('查询事件历史成功')
    return ResponseUtil.success(
        data={
            'rows': rows,
            'total': total,
            'pageNum': query.page_num,
            'pageSize': query.page_size,
        }
    )


@eventController.post('/replay', dependencies=[Depends(CheckUserInterfaceAuth('monitor:event:replay'))])
@Log(title='事件回放', business_type=BusinessType.UPDATE)
async def replay_events(
    request: Request,
    payload: EventReplayRequest,
    current_user: CurrentUserModel = Depends(get_current_user),
):
    event_runtime = getattr(request.app.state, 'event_runtime', None)
    if event_runtime is None:
        return ResponseUtil.success(http_status=503, data={'status': 'unavailable', 'detail': 'event_runtime_not_initialized'})

    replay_id = uuid4().hex
    filters = EventHistoryFilters(
        aggregate_id=payload.aggregate_id,
        aggregate_type=payload.aggregate_type,
        event_type=payload.event_type,
        begin_time=payload.begin_time,
        end_time=payload.end_time,
        page_num=1,
        page_size=payload.limit,
    )
    result = await event_runtime.replay(filters=filters, replay_id=replay_id, limit=payload.limit)

    logger.bind(
        event='event_replay_request',
        replay_id=replay_id,
        operator=current_user.user.user_name,
        total=result.total,
        succeeded=result.succeeded,
        failed=result.failed,
    ).info('event_replay_request_completed')

    return ResponseUtil.success(
        data={
            'replayId': result.replay_id,
            'total': result.total,
            'succeeded': result.succeeded,
            'failed': result.failed,
            'failureSamples': result.failure_samples,
        }
    )
