from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from module_admin.entity.do.enums import JobStatusEnum
from module_admin.entity.do.job_do import JobLogDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.job_vo import DeleteJobLogModel, JobLogModel, JobLogPageQueryModel
from utils.excel_util import ExcelUtil
from utils.transaction_manager import transactional
from ports import IDictDataService, IJobLogRepository


class JobLogService:
    """
    定时任务日志管理模块服务层
    """

    def __init__(self, job_log_repo: IJobLogRepository, query_db: AsyncSession):
        self.job_log_repo = job_log_repo
        self.query_db = query_db

    async def get_job_log_list_services(self, query_object: JobLogPageQueryModel, is_page: bool = False):
        """
        获取定时任务日志列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 定时任务日志列表信息对象
        """
        if is_page:
            job_log_list_result = await self.job_log_repo.paginate_with_filters(
                page=query_object.page,
                page_size=query_object.page_size,
                job_name=query_object.job_name,
                job_group=query_object.job_group,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
            )
        else:
            job_log_list_result = await self.job_log_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                job_name=query_object.job_name,
                job_group=query_object.job_group,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
            )
            if hasattr(job_log_list_result, 'items'):
                job_log_list_result = job_log_list_result.items

        return job_log_list_result

    @transactional()
    async def add_job_log_services(self, page_object: JobLogModel):
        """
        新增定时任务日志信息service

        :param page_object: 新增定时任务日志对象
        :return: 新增定时任务日志校验结果
        """
        db_job_log = JobLogDO(**page_object.model_dump())
        await self.job_log_repo.add(db_job_log)
        return CrudResponseModel(is_success=True, message='新增成功')

    @transactional()
    async def delete_job_log_services(self, page_object: DeleteJobLogModel):
        """
        删除定时任务日志信息service

        :param page_object: 删除定时任务日志对象
        :return: 删除定时任务日志校验结果
        """
        if page_object.job_log_ids:
            job_log_id_list = [int(id) for id in page_object.job_log_ids.split(',')]
            await self.job_log_repo.delete_by_ids(job_log_id_list)
            result = dict(is_success=True, message='删除成功')
        else:
            result = dict(is_success=False, message='传入定时任务日志id为空')
        return CrudResponseModel(**result)

    @transactional()
    async def clear_job_log_services(self):
        """
        清除定时任务日志信息service

        :return: 清除定时任务日志校验结果
        """
        await self.job_log_repo.clear_all()
        result = dict(is_success=True, message='清除成功')

        return CrudResponseModel(**result)

    @staticmethod
    async def export_job_log_list_services(request: Request, job_log_list: List, dict_data_service: IDictDataService):
        """
        导出定时任务日志信息service

        :param request: Request对象
        :param job_log_list: 定时任务日志信息列表
        :param dict_data_service: 字典数据服务
        :return: 定时任务日志信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'jobLogId': '任务日志编码',
            'jobName': '任务名称',
            'jobGroup': '任务组名',
            'jobExecutor': '任务执行器',
            'invokeTarget': '调用目标字符串',
            'jobArgs': '位置参数',
            'jobKwargs': '关键字参数',
            'jobTrigger': '任务触发器',
            'jobMessage': '日志信息',
            'status': '执行状态',
            'exceptionInfo': '异常信息',
            'createTime': '创建时间',
        }

        job_group_list = await dict_data_service.query_dict_data_list_from_cache_services(
            request.app.state.redis, dict_type='sys_job_group'
        )
        job_group_option = [dict(label=item.get('dictLabel'), value=item.get('dictValue')) for item in job_group_list]
        job_group_option_dict = {item.get('value'): item for item in job_group_option}
        job_executor_list = await dict_data_service.query_dict_data_list_from_cache_services(
            request.app.state.redis, dict_type='sys_job_executor'
        )
        job_executor_option = [
            dict(label=item.get('dictLabel'), value=item.get('dictValue')) for item in job_executor_list
        ]
        job_executor_option_dict = {item.get('value'): item for item in job_executor_option}

        for item in job_log_list:
            if item.get('status') == JobStatusEnum.NORMAL.value:
                item['status'] = '正常'
            else:
                item['status'] = '暂停'
            if str(item.get('jobGroup')) in job_group_option_dict.keys():
                item['jobGroup'] = job_group_option_dict.get(str(item.get('jobGroup'))).get('label')
            if str(item.get('jobExecutor')) in job_executor_option_dict.keys():
                item['jobExecutor'] = job_executor_option_dict.get(str(item.get('jobExecutor'))).get('label')
        binary_data = ExcelUtil.export_list2excel(job_log_list, mapping_dict)

        return binary_data
