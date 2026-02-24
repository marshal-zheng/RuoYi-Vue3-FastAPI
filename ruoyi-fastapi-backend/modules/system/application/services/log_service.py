from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from exceptions.exception import ValidationException
from module_admin.entity.do.log_do import OperLogDO, LogininforDO
from module_admin.entity.do.enums import BusinessStatusEnum, LoginStatusEnum
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.log_vo import (
    DeleteLoginLogModel,
    DeleteOperLogModel,
    LogininforModel,
    LoginLogPageQueryModel,
    OperLogModel,
    OperLogPageQueryModel,
    UnlockUser,
)
from utils.excel_util import ExcelUtil
from utils.transaction_manager import transactional
from ports import IDictDataService, ILoginLogRepository, IOperLogRepository


class OperationLogService:
    """
    操作日志管理模块服务层
    """

    def __init__(self, oper_log_repo: IOperLogRepository, query_db: AsyncSession):
        self.oper_log_repo = oper_log_repo
        self.query_db = query_db

    async def get_operation_log_list_services(self, query_object: OperLogPageQueryModel, is_page: bool = False):
        """
        获取操作日志列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 操作日志列表信息对象
        """
        if is_page:
            operation_log_list_result = await self.oper_log_repo.paginate_with_filters(
                page=query_object.page_num,
                page_size=query_object.page_size,
                title=query_object.title,
                oper_name=query_object.oper_name,
                business_type=query_object.business_type,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                order_by_column=query_object.order_by_column,
                is_asc=query_object.is_asc,
            )
        else:
            operation_log_list_result = await self.oper_log_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                title=query_object.title,
                oper_name=query_object.oper_name,
                business_type=query_object.business_type,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                order_by_column=query_object.order_by_column,
                is_asc=query_object.is_asc,
            )
            if hasattr(operation_log_list_result, 'rows'):
                operation_log_list_result = operation_log_list_result.rows

        return operation_log_list_result

    @transactional()
    async def add_operation_log_services(self, page_object: OperLogModel):
        """
        新增操作日志service

        :param page_object: 新增操作日志对象
        :return: 新增操作日志校验结果
        """
        db_oper_log = OperLogDO(**page_object.model_dump())
        await self.oper_log_repo.add(db_oper_log)
        return CrudResponseModel(is_success=True, message='新增成功')

    @transactional()
    async def delete_operation_log_services(self, page_object: DeleteOperLogModel):
        """
        删除操作日志信息service

        :param page_object: 删除操作日志对象
        :return: 删除操作日志校验结果
        """
        if page_object.oper_ids:
            oper_id_list = [int(id) for id in page_object.oper_ids.split(',')]
            await self.oper_log_repo.delete_by_ids(oper_id_list)
            return CrudResponseModel(is_success=True, message='删除成功')
        else:
            raise ValidationException(
                user_message='传入操作日志id为空',
                developer_message='Operation log IDs parameter is empty',
                field='oper_ids',
            )

    @transactional()
    async def clear_operation_log_services(self):
        """
        清除操作日志信息service

        :return: 清除操作日志校验结果
        """
        await self.oper_log_repo.clear_all()
        return CrudResponseModel(is_success=True, message='清除成功')

    async def export_operation_log_list_services(
        self, request: Request, operation_log_list: List, dict_data_service: IDictDataService
    ):
        """
        导出操作日志信息service

        :param request: Request对象
        :param operation_log_list: 操作日志信息列表
        :param dict_data_service: 字典数据服务
        :return: 操作日志信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'operId': '日志编号',
            'title': '系统模块',
            'businessType': '操作类型',
            'method': '方法名称',
            'requestMethod': '请求方式',
            'operName': '操作人员',
            'deptName': '部门名称',
            'operUrl': '请求URL',
            'operIp': '操作地址',
            'operLocation': '操作地点',
            'operParam': '请求参数',
            'jsonResult': '返回参数',
            'status': '操作状态',
            'error_msg': '错误消息',
            'operTime': '操作日期',
            'costTime': '消耗时间（毫秒）',
        }

        operation_type_list = await dict_data_service.query_dict_data_list_from_cache_services(
            request.app.state.redis, dict_type='sys_oper_type'
        )
        operation_type_option = [
            dict(label=item.get('dictLabel'), value=item.get('dictValue')) for item in operation_type_list
        ]
        operation_type_option_dict = {item.get('value'): item for item in operation_type_option}

        for item in operation_log_list:
            if str(item.get('status')) == BusinessStatusEnum.SUCCESS.value:
                item['status'] = '成功'
            else:
                item['status'] = '失败'
            if str(item.get('businessType')) in operation_type_option_dict.keys():
                item['businessType'] = operation_type_option_dict.get(str(item.get('businessType'))).get('label')
        binary_data = ExcelUtil.export_list2excel(operation_log_list, mapping_dict)

        return binary_data


class LoginLogService:
    """
    登录日志管理模块服务层
    """

    def __init__(self, login_log_repo: ILoginLogRepository, query_db: AsyncSession):
        self.login_log_repo = login_log_repo
        self.query_db = query_db

    async def get_login_log_list_services(self, query_object: LoginLogPageQueryModel, is_page: bool = False):
        """
        获取登录日志列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 登录日志列表信息对象
        """
        if is_page:
            operation_log_list_result = await self.login_log_repo.paginate_with_filters(
                page=query_object.page_num,
                page_size=query_object.page_size,
                ipaddr=query_object.ipaddr,
                user_name=query_object.user_name,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                order_by_column=query_object.order_by_column,
                is_asc=query_object.is_asc,
            )
        else:
            operation_log_list_result = await self.login_log_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                ipaddr=query_object.ipaddr,
                user_name=query_object.user_name,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
                order_by_column=query_object.order_by_column,
                is_asc=query_object.is_asc,
            )
            if hasattr(operation_log_list_result, 'rows'):
                operation_log_list_result = operation_log_list_result.rows

        return operation_log_list_result

    @transactional()
    async def add_login_log_services(self, page_object: LogininforModel):
        """
        新增登录日志service

        :param page_object: 新增登录日志对象
        :return: 新增登录日志校验结果
        """
        db_login_log = LogininforDO(**page_object.model_dump())
        await self.login_log_repo.add(db_login_log)
        return CrudResponseModel(is_success=True, message='新增成功')

    @transactional()
    async def delete_login_log_services(self, page_object: DeleteLoginLogModel):
        """
        删除操作日志信息service

        :param page_object: 删除操作日志对象
        :return: 删除操作日志校验结果
        """
        if page_object.info_ids:
            info_id_list = [int(id) for id in page_object.info_ids.split(',')]
            await self.login_log_repo.delete_by_ids(info_id_list)
            return CrudResponseModel(is_success=True, message='删除成功')
        else:
            raise ValidationException(
                user_message='传入登录日志id为空',
                developer_message='Login log IDs parameter is empty',
                field='info_ids',
            )

    @transactional()
    async def clear_login_log_services(self):
        """
        清除操作日志信息service

        :return: 清除操作日志校验结果
        """
        await self.login_log_repo.clear_all()
        return CrudResponseModel(is_success=True, message='清除成功')

    async def unlock_user_services(self, request: Request, unlock_user: UnlockUser):
        locked_user = await request.app.state.redis.get(f'account_lock:{unlock_user.user_name}')
        if locked_user:
            await request.app.state.redis.delete(f'account_lock:{unlock_user.user_name}')
            return CrudResponseModel(is_success=True, message='解锁成功')
        else:
            raise ValidationException(
                user_message='该用户未锁定',
                developer_message=f'User is not locked: user_name={unlock_user.user_name}',
                field='user_name',
            )

    @staticmethod
    async def export_login_log_list_services(login_log_list: List):
        """
        导出登录日志信息service

        :param login_log_list: 登录日志信息列表
        :return: 登录日志信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'infoId': '访问编号',
            'userName': '用户名称',
            'ipaddr': '登录地址',
            'loginLocation': '登录地点',
            'browser': '浏览器',
            'os': '操作系统',
            'status': '登录状态',
            'msg': '操作信息',
            'loginTime': '登录日期',
        }

        for item in login_log_list:
            if item.get('status') == LoginStatusEnum.SUCCESS.value:
                item['status'] = '成功'
            else:
                item['status'] = '失败'
        binary_data = ExcelUtil.export_list2excel(login_log_list, mapping_dict)

        return binary_data
