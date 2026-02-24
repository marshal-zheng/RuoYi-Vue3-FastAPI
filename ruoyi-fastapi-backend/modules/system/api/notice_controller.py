from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.notice_vo import DeleteNoticeModel, NoticeModel, NoticePageQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import AddNoticeCommand, DeleteNoticeCommand, EditNoticeCommand
from modules.system.application.mediator import Mediator
from modules.system.application.queries import GetNoticeDetailQuery, GetNoticeListQuery
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil
from utils.validation_util import ValidateFields

noticeController = APIRouter(prefix='/system/notice', dependencies=[Depends(get_current_user)])  # noqa: N816


@noticeController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:notice:list'))]
)
async def get_system_notice_list(
    request: Request,
    notice_page_query: NoticePageQueryModel = Depends(NoticePageQueryModel.as_query),
    mediator: Mediator = Depends(provide_system_mediator),
):
    list_query = GetNoticeListQuery(
        query=notice_page_query,
        is_page=True,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    notice_page_query_result = await mediator.query(list_query)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=notice_page_query_result)


@noticeController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:notice:add'))])
@ValidateFields(validate_model='add_notice')
@Log(title='通知公告', business_type=BusinessType.INSERT)
async def add_system_notice(
    request: Request,
    add_notice: NoticeModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    add_notice.create_by = current_user.user.user_name
    add_notice.create_time = datetime.now()
    add_notice.update_by = current_user.user.user_name
    add_notice.update_time = datetime.now()

    add_command = AddNoticeCommand(
        query_db=query_db,
        notice=add_notice,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    add_result = await mediator.send(add_command)
    message = add_result.data.get('message') if add_result.data else '新增成功'
    logger.info(message)

    return ResponseUtil.success(message=message)


@noticeController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:notice:edit'))])
@ValidateFields(validate_model='edit_notice')
@Log(title='通知公告', business_type=BusinessType.UPDATE)
async def edit_system_notice(
    request: Request,
    edit_notice: NoticeModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_notice.update_by = current_user.user.user_name
    edit_notice.update_time = datetime.now()

    edit_command = EditNoticeCommand(
        query_db=query_db,
        notice=edit_notice,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    return ResponseUtil.success(message=message)


@noticeController.delete('/{notice_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:notice:remove'))])
@Log(title='通知公告', business_type=BusinessType.DELETE)
async def delete_system_notice(
    request: Request,
    notice_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    delete_notice = DeleteNoticeModel(noticeIds=notice_ids)
    delete_command = DeleteNoticeCommand(
        query_db=query_db,
        delete_notice=delete_notice,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    delete_result = await mediator.send(delete_command)
    message = delete_result.data.get('message') if delete_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.success(message=message)


@noticeController.get(
    '/{notice_id}', response_model=NoticeModel, dependencies=[Depends(CheckUserInterfaceAuth('system:notice:query'))]
)
async def query_detail_system_post(
    request: Request,
    notice_id: int,
    mediator: Mediator = Depends(provide_system_mediator),
):
    detail_query = GetNoticeDetailQuery(
        notice_id=notice_id,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    notice_detail_result = await mediator.query(detail_query)
    logger.info(f'获取notice_id为{notice_id}的信息成功')

    return ResponseUtil.success(data=notice_detail_result)
