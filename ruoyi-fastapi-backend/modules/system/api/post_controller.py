from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.enums import BusinessType
from config.get_db import get_db
from container.dependencies import service_provider
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.post_vo import DeletePostModel, PostModel, PostPageQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.system.application.services.post_service import PostService
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import AddPostCommand, DeletePostCommand, EditPostCommand
from modules.system.application.mediator import Mediator
from modules.system.application.queries import GetPostDetailQuery, GetPostListQuery
from utils.common_util import bytes2file_response
from utils.http_contract_responses import require_int_value
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil
from utils.validation_util import ValidateFields

postController = APIRouter(prefix='/system/post', dependencies=[Depends(get_current_user)])  # noqa: N816


async def _load_post_detail(request: Request, *, post_id: int, mediator: Mediator):
    detail_query = GetPostDetailQuery(
        post_id=post_id,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    return await mediator.query(detail_query)


@postController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:post:list'))]
)
async def get_system_post_list(
    request: Request,
    post_page_query: PostPageQueryModel = Depends(PostPageQueryModel.as_query),
    mediator: Mediator = Depends(provide_system_mediator),
):
    list_query = GetPostListQuery(
        query=post_page_query,
        is_page=True,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    post_page_query_result = await mediator.query(list_query)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(post_page_query_result)


@postController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:post:add'))])
@ValidateFields(validate_model='add_post')
@Log(title='岗位管理', business_type=BusinessType.INSERT)
async def add_system_post(
    request: Request,
    add_post: PostModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    add_post.create_by = current_user.user.user_name
    add_post.create_time = datetime.now()
    add_post.update_by = current_user.user.user_name
    add_post.update_time = datetime.now()

    add_command = AddPostCommand(
        query_db=query_db,
        post=add_post,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    add_result = await mediator.send(add_command)
    message = add_result.data.get('message') if add_result.data else '新增成功'
    logger.info(message)

    post_id = require_int_value(add_result.data, 'postId', 'post_id', contract_name='system.post.create')
    resource = await _load_post_detail(request, post_id=int(post_id), mediator=mediator)
    location = ResponseUtil.build_absolute_location(request, f'/system/post/{post_id}')
    return ResponseUtil.created_resource(resource, location=location)


@postController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:post:edit'))])
@ValidateFields(validate_model='edit_post')
@Log(title='岗位管理', business_type=BusinessType.UPDATE)
async def edit_system_post(
    request: Request,
    edit_post: PostModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    edit_post.update_by = current_user.user.user_name
    edit_post.update_time = datetime.now()

    edit_command = EditPostCommand(
        query_db=query_db,
        post=edit_post,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    edit_result = await mediator.send(edit_command)
    message = edit_result.data.get('message') if edit_result.data else '更新成功'
    logger.info(message)

    resource = await _load_post_detail(request, post_id=edit_post.post_id, mediator=mediator)
    return ResponseUtil.ok_resource(resource)


@postController.delete('/{post_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:post:remove'))])
@Log(title='岗位管理', business_type=BusinessType.DELETE)
async def delete_system_post(
    request: Request,
    post_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
    mediator: Mediator = Depends(provide_system_mediator),
):
    delete_post = DeletePostModel(postIds=post_ids)
    delete_command = DeletePostCommand(
        query_db=query_db,
        delete_post=delete_post,
        redis_client=getattr(request.app.state, 'redis', None),
        operator=current_user.user.user_name,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    delete_result = await mediator.send(delete_command)
    message = delete_result.data.get('message') if delete_result.data else '删除成功'
    logger.info(message)

    return ResponseUtil.no_content()


@postController.get(
    '/{post_id}', response_model=PostModel, dependencies=[Depends(CheckUserInterfaceAuth('system:post:query'))]
)
async def query_detail_system_post(
    request: Request,
    post_id: int,
    mediator: Mediator = Depends(provide_system_mediator),
):
    detail_query = GetPostDetailQuery(
        post_id=post_id,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    post_detail_result = await mediator.query(detail_query)
    logger.info(f'获取post_id为{post_id}的信息成功')

    return ResponseUtil.ok_resource(post_detail_result)


@postController.post('/export', dependencies=[Depends(CheckUserInterfaceAuth('system:post:export'))])
@Log(title='岗位管理', business_type=BusinessType.EXPORT)
async def export_system_post_list(
    request: Request,
    post_page_query: PostPageQueryModel = Form(),
    post_service: PostService = Depends(service_provider('post_service')),
    mediator: Mediator = Depends(provide_system_mediator),
):
    list_query = GetPostListQuery(
        query=post_page_query,
        is_page=False,
        trace_id=request.headers.get('x-trace-id'),
        request_id=request.headers.get('x-request-id'),
    )
    post_query_result = await mediator.query(list_query)
    post_rows = [row.model_dump(by_alias=True) for row in post_query_result.items]
    post_export_result = await post_service.export_post_list_services(post_rows)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(post_export_result))
