from contextlib import AsyncExitStack
from asyncio import Lock
from weakref import WeakValueDictionary
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from typing import List
from config.constant import CommonConstant
from config.get_scheduler import SchedulerUtil
from exceptions.exception import ValidationException, ResourceNotFoundException
from config.error_codes import ErrorCode
from module_admin.entity.do.enums import JobStatusEnum, MisfirePolicyEnum
from module_admin.entity.do.job_do import JobDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.job_vo import DeleteJobModel, JobModel, JobPageQueryModel
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.transaction_manager import transactional
from ports import IDictDataService, IJobRepository


_JOB_OPERATION_LOCKS: WeakValueDictionary[int, Lock] = WeakValueDictionary()


def _job_operation_lock(job_id: int) -> Lock:
    # Locks live only while operations hold/wait for them; scheduling is local to this process.
    return _JOB_OPERATION_LOCKS.setdefault(job_id, Lock())


class JobService:
    """
    定时任务管理模块服务层
    """

    def __init__(self, job_repo: IJobRepository, query_db: AsyncSession):
        self.job_repo = job_repo
        self.query_db = query_db

    async def get_job_list_services(self, query_object: JobPageQueryModel, is_page: bool = False):
        """
        获取定时任务列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 定时任务列表信息对象
        """
        if is_page:
            job_list_result = await self.job_repo.paginate_with_filters(
                page=query_object.page,
                page_size=query_object.page_size,
                job_name=query_object.job_name,
                job_group=query_object.job_group,
                status=query_object.status,
            )
        else:
            job_list_result = await self.job_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                job_name=query_object.job_name,
                job_group=query_object.job_group,
                status=query_object.status,
            )
            job_list_result = job_list_result.items if hasattr(job_list_result, 'items') else job_list_result

        return job_list_result

    async def check_job_unique_services(self, page_object: JobModel):
        """
        校验定时任务是否存在service

        :param page_object: 定时任务对象
        :return: 校验结果
        """
        job_id = -1 if page_object.job_id is None else page_object.job_id
        job = await self.job_repo.find_by_info(
            job_name=page_object.job_name,
            job_group=page_object.job_group,
            job_executor=page_object.job_executor,
            invoke_target=page_object.invoke_target,
            job_args=page_object.job_args,
            job_kwargs=page_object.job_kwargs,
            cron_expression=page_object.cron_expression,
        )
        if job and job.job_id != job_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    async def _save_job(self, page_object: JobModel, *, creating: bool = False, status_only: bool = False):
        """Own this job write unit so DB commit errors can restore the previous schedule."""
        fields = {
            'job_name',
            'job_group',
            'job_executor',
            'invoke_target',
            'job_args',
            'job_kwargs',
            'cron_expression',
            'misfire_policy',
            'concurrent',
            'status',
            'remark',
            'update_by',
            'update_time',
        }
        changes = page_object.model_dump(include=fields, exclude_unset=True)
        previous_record = None
        if creating:
            row = JobDO(**changes, **page_object.model_dump(include={'create_by', 'create_time'}, exclude_unset=True))
            effective = JobModel(
                **{
                    'job_group': 'default',
                    'job_executor': 'default',
                    'misfire_policy': '3',
                    'concurrent': '1',
                    'status': '0',
                    **changes,
                }
            )
        else:
            row = await self.job_repo.find_for_update(page_object.job_id)
            if row is None:
                raise ResourceNotFoundException(user_message='定时任务不存在', error_code=ErrorCode.RESOURCE_NOT_FOUND)
            effective = JobModel(**CamelCaseUtil.transform_result(row))
            previous_record = effective.model_dump()
            effective = effective.model_copy(update=changes)
        if not status_only or effective.status == JobStatusEnum.NORMAL.value:
            SchedulerUtil.validate_job(effective)
        if not status_only and not await self.check_job_unique_services(effective):
            raise ValidationException(error_code=ErrorCode.RESOURCE_CONFLICT, user_message='定时任务已存在')

        job_id = await self._commit_job_change(row, effective, changes, previous_record)
        return CrudResponseModel(
            is_success=True, message='新增成功' if creating else '更新成功', result={'jobId': job_id}
        )

    async def _restore_job_record(self, job_id, previous_record):
        if previous_record is None:
            await self.job_repo.delete_by_id(job_id)
        else:
            stored = await self.job_repo.find_by_id(job_id)
            for key, value in previous_record.items():
                setattr(stored, key, value)
            # Restore the original audit timestamp even when DB precision made it compare equal.
            flag_modified(stored, 'update_time')
            await self.job_repo.update(stored)
        await self.query_db.commit()

    async def _commit_job_change(self, row, effective, changes, previous_record):
        creating = previous_record is None
        previous = None if creating else SchedulerUtil.snapshot_scheduler_job(row.job_id)
        schedule_touched = False
        completed = False
        db_committed = False
        job_id = row.job_id
        async with AsyncExitStack() as creation_lock:
            try:
                if creating:
                    row = await self.job_repo.add(row)
                    await creation_lock.enter_async_context(_job_operation_lock(row.job_id))
                else:
                    for key, value in changes.items():
                        setattr(row, key, value)
                    await self.job_repo.update(row)
                job_id = row.job_id
                effective.job_id = job_id
                # New configuration must never become executable before its database commit succeeds.
                if isinstance(self.query_db, AsyncSession):
                    await self.query_db.commit()
                    db_committed = True
                schedule_touched = True
                if effective.status == JobStatusEnum.NORMAL.value:
                    SchedulerUtil.add_scheduler_job(effective)
                else:
                    SchedulerUtil.remove_scheduler_job(job_id)
                completed = True
            finally:
                if not completed:
                    # Restore synchronously before another await can let a failed candidate execute.
                    try:
                        if schedule_touched:
                            SchedulerUtil.restore_scheduler_job(job_id, previous)
                    finally:
                        if isinstance(self.query_db, AsyncSession):
                            await self.query_db.rollback()
                            if db_committed:
                                await self._restore_job_record(job_id, previous_record)
        return job_id

    async def add_job_services(self, page_object: JobModel):
        return await self._save_job(page_object, creating=True)

    async def edit_job_services(self, page_object: JobModel):
        async with _job_operation_lock(page_object.job_id):
            return await self._save_job(page_object)

    async def change_job_status_services(self, page_object: JobModel):
        async with _job_operation_lock(page_object.job_id):
            # The status operation cannot mutate configuration, even for internal callers.
            return await self._save_job(
                JobModel(
                    **page_object.model_dump(
                        include={'job_id', 'status', 'update_by', 'update_time'},
                        exclude_unset=True,
                    )
                ),
                status_only=True,
            )

    async def execute_job_once_services(self, page_object: JobModel):
        async with _job_operation_lock(page_object.job_id):
            row = await self.job_repo.find_for_update(page_object.job_id)
            if row is None:
                raise ResourceNotFoundException(user_message='定时任务不存在', error_code=ErrorCode.RESOURCE_NOT_FOUND)
            job_info = JobModel(**CamelCaseUtil.transform_result(row))
            SchedulerUtil.validate_job(job_info)
            if isinstance(self.query_db, AsyncSession):
                await self.query_db.commit()
            return self._execute_job_once(job_info)

    def _execute_job_once(self, job_info: JobModel):
        SchedulerUtil.validate_job(job_info)
        previous = SchedulerUtil.snapshot_scheduler_job(job_info.job_id)
        applied = False
        try:
            SchedulerUtil.execute_scheduler_job_once(job_info)
            applied = True
        finally:
            if not applied:
                SchedulerUtil.restore_scheduler_job(job_info.job_id, previous)
        return CrudResponseModel(
            is_success=True,
            message='执行成功',
            result={
                'jobId': job_info.job_id,
                'jobGroup': job_info.job_group,
            },
        )

    @transactional()
    async def delete_job_services(self, page_object: DeleteJobModel):
        """
        删除定时任务信息service

        :param page_object: 删除定时任务对象
        :return: 删除定时任务校验结果
        """
        if not page_object.job_ids:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT, field='job_ids', user_message='传入定时任务id为空'
            )

        job_id_list = page_object.job_ids.split(',')
        for job_id in job_id_list:
            async with _job_operation_lock(int(job_id)):
                await self.job_repo.delete_by_id(int(job_id))
                SchedulerUtil.remove_scheduler_job(job_id=job_id)
        return CrudResponseModel(is_success=True, message='删除成功')

    async def job_detail_services(self, job_id: int):
        """
        获取定时任务详细信息service

        :param job_id: 定时任务id
        :return: 定时任务id对应的信息
        """
        job = await self.job_repo.find_by_id(job_id)
        if job:
            result = JobModel(**CamelCaseUtil.transform_result(job))
        else:
            raise ResourceNotFoundException(
                user_message='定时任务不存在',
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                developer_message=f'job_id={job_id} not found',
            )

        return result

    @staticmethod
    async def export_job_list_services(request: Request, job_list: List, dict_data_service: IDictDataService):
        """
        导出定时任务信息service

        :param request: Request对象
        :param job_list: 定时任务信息列表
        :param dict_data_service: 字典数据服务
        :return: 定时任务信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'jobId': '任务编码',
            'jobName': '任务名称',
            'jobGroup': '任务组名',
            'jobExecutor': '任务执行器',
            'invokeTarget': '调用目标字符串',
            'jobArgs': '位置参数',
            'jobKwargs': '关键字参数',
            'cronExpression': 'cron执行表达式',
            'misfirePolicy': '计划执行错误策略',
            'concurrent': '是否并发执行',
            'status': '状态',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
            'remark': '备注',
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

        for item in job_list:
            if item.get('status') == JobStatusEnum.NORMAL.value:
                item['status'] = '正常'
            else:
                item['status'] = '暂停'
            if str(item.get('jobGroup')) in job_group_option_dict.keys():
                item['jobGroup'] = job_group_option_dict.get(str(item.get('jobGroup'))).get('label')
            if str(item.get('jobExecutor')) in job_executor_option_dict.keys():
                item['jobExecutor'] = job_executor_option_dict.get(str(item.get('jobExecutor'))).get('label')
            if item.get('misfirePolicy') == MisfirePolicyEnum.IMMEDIATELY.value:
                item['misfirePolicy'] = '立即执行'
            elif item.get('misfirePolicy') == MisfirePolicyEnum.ONCE.value:
                item['misfirePolicy'] = '执行一次'
            else:
                item['misfirePolicy'] = '放弃执行'
            if item.get('concurrent') == '0':
                item['concurrent'] = '允许'
            else:
                item['concurrent'] = '禁止'
        binary_data = ExcelUtil.export_list2excel(job_list, mapping_dict)

        return binary_data
