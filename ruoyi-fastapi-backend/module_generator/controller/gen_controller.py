from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request
from utils.validation_util import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from config.enums import BusinessType
from container.dependencies import service_provider
from config.env import GenConfig
from config.get_db import get_db
from config.error_codes import ErrorCode
from exceptions.exception import BusinessException
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckRoleInterfaceAuth, CheckUserInterfaceAuth
from modules.identity.application.services.login_service import LoginService
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_generator.entity.vo.gen_vo import DeleteGenTableModel, EditGenTableModel, GenTablePageQueryModel
from module_generator.service.gen_service import GenTableColumnService, GenTableService
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


genController = APIRouter(prefix='/tool/gen', dependencies=[Depends(LoginService.get_current_user)])


@genController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('tool:gen:list'))]
)
async def get_gen_table_list(
    request: Request,
    gen_page_query: GenTablePageQueryModel = Depends(GenTablePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
):
    # 获取分页数据
    gen_page_query_result = await gen_table_service.get_gen_table_list_services(gen_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=gen_page_query_result)


@genController.get(
    '/db/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('tool:gen:list'))]
)
async def get_gen_db_table_list(
    request: Request,
    gen_page_query: GenTablePageQueryModel = Depends(GenTablePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
):
    # 获取分页数据
    gen_page_query_result = await gen_table_service.get_gen_db_table_list_services(gen_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=gen_page_query_result)


@genController.post('/importTable', dependencies=[Depends(CheckUserInterfaceAuth('tool:gen:import'))])
@Log(title='代码生成', business_type=BusinessType.IMPORT)
async def import_gen_table(
    request: Request,
    tables: str = Query(),
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    table_names = tables.split(',') if tables else []
    add_gen_table_list = await gen_table_service.get_gen_db_table_list_by_name_services(table_names)
    add_gen_table_result = await gen_table_service.import_gen_table_services(add_gen_table_list, current_user)
    logger.info(add_gen_table_result.message)

    return ResponseUtil.success(message=add_gen_table_result.message)


@genController.put('', dependencies=[Depends(CheckUserInterfaceAuth('tool:gen:edit'))])
@ValidateFields(validate_model='edit_gen_table')
@Log(title='代码生成', business_type=BusinessType.UPDATE)
async def edit_gen_table(
    request: Request,
    edit_gen_table: EditGenTableModel,
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    edit_gen_table.update_by = current_user.user.user_name
    edit_gen_table.update_time = datetime.now()
    await gen_table_service.validate_edit(edit_gen_table)
    edit_gen_result = await gen_table_service.edit_gen_table_services(edit_gen_table)
    logger.info(edit_gen_result.message)

    return ResponseUtil.success(message=edit_gen_result.message)


@genController.delete('/{table_ids}', dependencies=[Depends(CheckUserInterfaceAuth('tool:gen:remove'))])
@Log(title='代码生成', business_type=BusinessType.DELETE)
async def delete_gen_table(
    request: Request,
    table_ids: str,
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
):
    delete_gen_table = DeleteGenTableModel(tableIds=table_ids)
    delete_gen_table_result = await gen_table_service.delete_gen_table_services(delete_gen_table)
    logger.info(delete_gen_table_result.message)

    return ResponseUtil.success(message=delete_gen_table_result.message)


@genController.post('/createTable', dependencies=[Depends(CheckRoleInterfaceAuth('admin'))])
@Log(title='创建表', business_type=BusinessType.OTHER)
async def create_table(
    request: Request,
    sql: str = Query(),
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    create_table_result = await gen_table_service.create_table_services(sql, current_user)
    logger.info(create_table_result.message)

    return ResponseUtil.success(message=create_table_result.message)


@genController.get('/batchGenCode', dependencies=[Depends(CheckUserInterfaceAuth('tool:gen:code'))])
@Log(title='代码生成', business_type=BusinessType.GENCODE)
async def batch_gen_code(
    request: Request,
    tables: str = Query(),
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
):
    table_names = tables.split(',') if tables else []
    batch_gen_code_result = await gen_table_service.batch_gen_code_services(table_names)
    logger.info('生成代码成功')

    return ResponseUtil.streaming(data=bytes2file_response(batch_gen_code_result))


@genController.get('/genCode/{table_name}', dependencies=[Depends(CheckUserInterfaceAuth('tool:gen:code'))])
@Log(title='代码生成', business_type=BusinessType.GENCODE)
async def gen_code_local(
    request: Request,
    table_name: str,
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
):
    if not GenConfig.allow_overwrite:
        logger.error('【系统预设】不允许生成文件覆盖到本地')
        raise BusinessException(
            user_message='代码生成失败：系统配置不允许覆盖本地文件',
            error_code=ErrorCode.CODEGEN_OVERWRITE_DISABLED,
            http_status=403,
            developer_message=f'Code generation blocked: GenConfig.allow_overwrite is False for table {table_name}'
        )
    gen_code_local_result = await gen_table_service.generate_code_services(table_name)
    logger.info(gen_code_local_result.message)

    return ResponseUtil.success(message=gen_code_local_result.message)


@genController.get('/{table_id}', dependencies=[Depends(CheckUserInterfaceAuth('tool:gen:query'))])
async def query_detail_gen_table(
    request: Request,
    table_id: int,
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
    gen_table_column_service: GenTableColumnService = Depends(service_provider('gen_table_column_service')),
):
    gen_table = await gen_table_service.get_gen_table_by_id_services(table_id)
    gen_tables = await gen_table_service.get_gen_table_all_services()
    gen_columns = await gen_table_column_service.get_gen_table_column_list_by_table_id_services(table_id)
    gen_table_detail_result = dict(info=gen_table, rows=gen_columns, tables=gen_tables)
    logger.info(f'获取table_id为{table_id}的信息成功')

    return ResponseUtil.success(data=gen_table_detail_result)


@genController.get('/preview/{table_id}', dependencies=[Depends(CheckUserInterfaceAuth('tool:gen:preview'))])
async def preview_code(
    request: Request,
    table_id: int,
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
):
    preview_code_result = await gen_table_service.preview_code_services(table_id)
    logger.info('获取预览代码成功')

    return ResponseUtil.success(data=preview_code_result)


@genController.get('/synchDb/{table_name}', dependencies=[Depends(CheckUserInterfaceAuth('tool:gen:edit'))])
@Log(title='代码生成', business_type=BusinessType.UPDATE)
async def sync_db(
    request: Request,
    table_name: str,
    query_db: AsyncSession = Depends(get_db),
    gen_table_service: GenTableService = Depends(service_provider('gen_table_service')),
):
    sync_db_result = await gen_table_service.sync_db_services(table_name)
    logger.info(sync_db_result.message)

    return ResponseUtil.success(data=sync_db_result.message)
