from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.protocol_vo import (
    ProtocolModel,
    ProtocolPageQueryModel,
    DeleteProtocolModel,
    LockProtocolModel
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_admin.service.protocol_service import ProtocolService
from utils.log_util import logger
from utils.response_util import ResponseUtil
from utils.page_util import PageResponseModel


protocolController = APIRouter(prefix='/system/protocol', tags=['协议管理'])


@protocolController.get(
    '/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('protocol:list'))]
)
async def get_protocol_list(
    request: Request,
    protocol_page_query: ProtocolPageQueryModel = Depends(ProtocolPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db)
):
    """
    获取协议列表
    """
    try:
        # 获取分页数据
        protocol_page_query_result = await ProtocolService.get_protocol_list_services(
            query_db, protocol_page_query, is_page=True
        )
        logger.info('获取成功')
        return ResponseUtil.success(model_content=protocol_page_query_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@protocolController.post(
    '',
    response_model=CrudResponseModel,
    dependencies=[
        Depends(CheckUserInterfaceAuth('protocol:add')),
    ]
)
@Log(title='协议管理', business_type=BusinessType.INSERT, log_type='operation')
async def add_protocol(
    request: Request,
    add_protocol: ProtocolModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    新增协议
    """
    try:
        add_protocol.create_by = current_user.user.user_name
        add_protocol.update_by = current_user.user.user_name
        add_protocol_result = await ProtocolService.add_protocol_services(query_db, add_protocol)
        logger.info(add_protocol_result.message)
        return ResponseUtil.success(msg=add_protocol_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@protocolController.put(
    '',
    response_model=CrudResponseModel,
    dependencies=[
        Depends(CheckUserInterfaceAuth('protocol:edit')),
    ]
)
@Log(title='协议管理', business_type=BusinessType.UPDATE, log_type='operation')
async def edit_protocol(
    request: Request,
    edit_protocol: ProtocolModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    编辑协议
    """
    try:
        edit_protocol.update_by = current_user.user.user_name
        edit_protocol_result = await ProtocolService.edit_protocol_services(query_db, edit_protocol)
        logger.info(edit_protocol_result.message)
        return ResponseUtil.success(msg=edit_protocol_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@protocolController.delete(
    '/{protocol_ids}',
    response_model=CrudResponseModel,
    dependencies=[
        Depends(CheckUserInterfaceAuth('protocol:remove')),
    ]
)
@Log(title='协议管理', business_type=BusinessType.DELETE, log_type='operation')
async def delete_protocol(
    request: Request,
    protocol_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    删除协议
    """
    try:
        delete_protocol = DeleteProtocolModel(protocolIds=protocol_ids, updateBy=current_user.user.user_name)
        delete_protocol_result = await ProtocolService.delete_protocol_services(query_db, delete_protocol)
        logger.info(delete_protocol_result.message)
        return ResponseUtil.success(msg=delete_protocol_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@protocolController.get(
    '/{protocol_id}',
    dependencies=[Depends(CheckUserInterfaceAuth('protocol:query'))]
)
async def query_protocol_detail(
    request: Request,
    protocol_id: int,
    query_db: AsyncSession = Depends(get_db)
):
    """
    获取协议详情
    """
    try:
        protocol_detail_result = await ProtocolService.protocol_detail_services(query_db, protocol_id)
        logger.info('获取成功')
        return ResponseUtil.success(data=protocol_detail_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@protocolController.put(
    '/lock',
    response_model=CrudResponseModel,
    dependencies=[
        Depends(CheckUserInterfaceAuth('protocol:edit')),
    ]
)
@Log(title='协议管理', business_type=BusinessType.UPDATE, log_type='operation')
async def lock_protocol(
    request: Request,
    lock_protocol: LockProtocolModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    固化/解除固化协议
    """
    try:
        lock_protocol.update_by = current_user.user.user_name
        lock_protocol_result = await ProtocolService.lock_protocol_services(query_db, lock_protocol)
        logger.info(lock_protocol_result.message)
        return ResponseUtil.success(msg=lock_protocol_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))
