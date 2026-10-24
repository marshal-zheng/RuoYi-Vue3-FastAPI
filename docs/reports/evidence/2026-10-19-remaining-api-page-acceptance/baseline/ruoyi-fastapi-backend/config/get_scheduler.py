import json
import asyncio
from apscheduler.events import EVENT_ALL
from apscheduler.job import Job
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
import os
import sys
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from asyncio import iscoroutinefunction
from datetime import datetime, timedelta
from sqlalchemy.engine import create_engine
from typing import Union
from config.database import AsyncSessionLocal, quote_plus
from config.env import DataBaseConfig, RedisConfig
from module_admin.entity.vo.job_vo import JobLogModel, JobModel
from modules.scheduler.infrastructure.job_repository import JobLogRepository, JobRepository
from modules.scheduler.application.job_log_service import JobLogService
from config.job_registry import JobFunctionRegistry
from utils.log_util import logger
from utils.cron_util import CronUtil
from exceptions.exception import ValidationException
import module_task  # noqa: F401


# 重写Cron定时
class MyCronTrigger(CronTrigger):
    @classmethod
    def from_crontab(cls, expr: str, timezone=None):
        values = expr.split()
        if len(values) != 6 and len(values) != 7:
            raise ValueError('Wrong number of fields; got {}, expected 6 or 7'.format(len(values)))

        second = values[0]
        minute = values[1]
        hour = values[2]
        if '?' in values[3]:
            day = None
        elif 'L' in values[5]:
            day = f'last {values[5].replace("L", "")}'
        elif 'W' in values[3]:
            day = cls.__find_recent_workday(int(values[3].split('W')[0]))
        else:
            day = values[3].replace('L', 'last')
        month = values[4]
        if '?' in values[5] or 'L' in values[5]:
            week = None
        elif '#' in values[5]:
            week = int(values[5].split('#')[1])
        else:
            week = values[5]
        if '#' in values[5]:
            day_of_week = int(values[5].split('#')[0]) - 1
        else:
            day_of_week = None
        year = values[6] if len(values) == 7 else None
        return cls(
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            week=week,
            day_of_week=day_of_week,
            year=year,
            timezone=timezone,
        )

    @classmethod
    def __find_recent_workday(cls, day: int):
        now = datetime.now()
        date = datetime(now.year, now.month, day)
        if date.weekday() < 5:
            return date.day
        else:
            diff = 1
            while True:
                previous_day = date - timedelta(days=diff)
                if previous_day.weekday() < 5:
                    return previous_day.day
                else:
                    diff += 1


SQLALCHEMY_DATABASE_URL = (
    f'mysql+pymysql://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
    f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    f'?charset=utf8mb4'
)
if DataBaseConfig.db_type == 'postgresql':
    SQLALCHEMY_DATABASE_URL = (
        f'postgresql+psycopg2://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
        f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    )
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=DataBaseConfig.db_echo,
    max_overflow=DataBaseConfig.db_max_overflow,
    pool_size=DataBaseConfig.db_pool_size,
    pool_recycle=DataBaseConfig.db_pool_recycle,
    pool_timeout=DataBaseConfig.db_pool_timeout,
)
job_stores = {
    'default': MemoryJobStore(),
    'sqlalchemy': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URL, engine=engine),
    'redis': RedisJobStore(
        **dict(
            host=RedisConfig.redis_host,
            port=RedisConfig.redis_port,
            username=RedisConfig.redis_username,
            password=RedisConfig.redis_password,
            db=RedisConfig.redis_database,
        )
    ),
}
_is_pytest = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST') is not None
executors = {'default': AsyncIOExecutor()}
if not _is_pytest:
    try:
        executors['processpool'] = ProcessPoolExecutor(5)
    except PermissionError:
        logger.warning('ProcessPoolExecutor unavailable; falling back to ThreadPoolExecutor')
        executors['processpool'] = ThreadPoolExecutor(5)
job_defaults = {'coalesce': False, 'max_instance': 1}
scheduler = AsyncIOScheduler()
scheduler.configure(jobstores=job_stores, executors=executors, job_defaults=job_defaults)


class SchedulerUtil:
    """
    定时任务相关方法
    """

    @classmethod
    async def init_system_scheduler(cls):
        """
        应用启动时初始化定时任务

        :return:
        """
        logger.info('开始启动定时任务...')
        scheduler.start()
        async with AsyncSessionLocal() as session:
            job_repo = JobRepository(session)
            job_list = await job_repo.find_all_active()
            for item in job_list:
                cls.remove_scheduler_job(job_id=str(item.job_id))
                cls.add_scheduler_job(item)
        scheduler.add_listener(cls.scheduler_event_listener, EVENT_ALL)
        logger.info('系统初始定时任务加载成功')

    @classmethod
    async def close_system_scheduler(cls):
        """
        应用关闭时关闭定时任务

        :return:
        """
        scheduler.shutdown()
        logger.info('关闭定时任务成功')

    @classmethod
    def get_scheduler_job(cls, job_id: Union[str, int]):
        """
        根据任务id获取任务对象

        :param job_id: 任务id
        :return: 任务对象
        """
        query_job = scheduler.get_job(job_id=str(job_id))

        return query_job

    @classmethod
    def _job_options(cls, job_info: JobModel, *, run_once: bool = False):
        try:
            job_func = JobFunctionRegistry.get(job_info.invoke_target)
        except ValueError as error:
            raise ValidationException(user_message='调用目标未注册', field='invoke_target') from error
        try:
            cron_valid = CronUtil.validate_cron_expression(job_info.cron_expression or '')
        except (ValueError, TypeError) as error:
            raise ValidationException(user_message='Cron表达式不正确', field='cron_expression') from error
        if not cron_valid:
            raise ValidationException(user_message='Cron表达式不正确', field='cron_expression')
        try:
            trigger = MyCronTrigger.from_crontab(job_info.cron_expression, timezone=scheduler.timezone)
        except (ValueError, TypeError) as error:
            raise ValidationException(user_message='Cron表达式无法调度', field='cron_expression') from error
        try:
            kwargs = json.loads(job_info.job_kwargs) if job_info.job_kwargs else {}
            if not isinstance(kwargs, dict):
                raise ValueError('Expected JSON object')
        except (ValueError, TypeError) as error:
            raise ValidationException(user_message='关键字参数必须是JSON对象', field='job_kwargs') from error
        for alias, lookup, field in (
            (job_info.job_group or 'default', scheduler._lookup_jobstore, 'job_group'),
            (job_info.job_executor or 'default', scheduler._lookup_executor, 'job_executor'),
        ):
            try:
                lookup(alias)
            except KeyError as error:
                raise ValidationException(user_message='任务组或执行器不存在', field=field) from error
        if run_once:
            trigger = (
                OrTrigger(triggers=[DateTrigger(timezone=scheduler.timezone), trigger])
                if job_info.status == '0'
                else DateTrigger(timezone=scheduler.timezone)
            )
        return {
            'func': job_func,
            'trigger': trigger,
            'args': tuple(job_info.job_args.split(',')) if job_info.job_args else (),
            'kwargs': kwargs,
            'id': str(job_info.job_id) if job_info.job_id is not None else 'validation',
            'name': job_info.job_name,
            'misfire_grace_time': 1000000000000 if job_info.misfire_policy == '3' else None,
            'coalesce': job_info.misfire_policy == '2',
            'max_instances': 3 if job_info.concurrent == '0' else 1,
            'jobstore': job_info.job_group or 'default',
            'executor': 'default' if iscoroutinefunction(job_func) else job_info.job_executor or 'default',
        }

    @classmethod
    def validate_job(cls, job_info: JobModel):
        options = cls._job_options(job_info)
        try:
            # APScheduler validates callable signatures with exactly the argument conversion used for execution.
            Job(scheduler, **{key: value for key, value in options.items() if key != 'jobstore'})
        except (ValueError, TypeError) as error:
            raise ValidationException(
                user_message='调用参数与任务函数不匹配', field='job_args', developer_message=str(error)
            ) from error

    @classmethod
    def snapshot_scheduler_job(cls, job_id):
        job = cls.get_scheduler_job(job_id)
        if job is None:
            return None
        return {
            'func': job.func,
            'trigger': job.trigger,
            'args': job.args,
            'kwargs': dict(job.kwargs),
            'id': job.id,
            'name': job.name,
            'misfire_grace_time': job.misfire_grace_time,
            'coalesce': job.coalesce,
            'max_instances': job.max_instances,
            'next_run_time': job.next_run_time,
            'jobstore': job._jobstore_alias,
            'executor': job.executor,
        }

    @classmethod
    def restore_scheduler_job(cls, job_id, previous):
        cls.remove_scheduler_job(job_id)
        if previous is not None:
            scheduler.add_job(**previous, replace_existing=True)

    @classmethod
    def _replace_scheduler_job(cls, job_info, *, run_once=False):
        options = cls._job_options(job_info, run_once=run_once)
        old = cls.get_scheduler_job(job_info.job_id)
        scheduler.add_job(**options, replace_existing=True)
        if old is not None and old._jobstore_alias != options['jobstore']:
            scheduler.remove_job(old.id, jobstore=old._jobstore_alias)

    @classmethod
    def add_scheduler_job(cls, job_info: JobModel):
        cls._replace_scheduler_job(job_info)

    @classmethod
    def execute_scheduler_job_once(cls, job_info: JobModel):
        cls._replace_scheduler_job(job_info, run_once=True)

    @classmethod
    def remove_scheduler_job(cls, job_id: Union[str, int]):
        for job in scheduler.get_jobs():
            if job.id == str(job_id):
                scheduler.remove_job(job.id, jobstore=job._jobstore_alias)

    @classmethod
    def scheduler_event_listener(cls, event):
        # 获取事件类型和任务ID
        event_type = event.__class__.__name__
        # 获取任务执行异常信息
        status = '0'
        exception_info = ''
        if event_type == 'JobExecutionEvent' and event.exception:
            exception_info = str(event.exception)
            status = '1'
        if hasattr(event, 'job_id'):
            job_id = event.job_id
            query_job = cls.get_scheduler_job(job_id=job_id)
            if query_job:
                query_job_info = query_job.__getstate__()
                # 获取任务名称
                job_name = query_job_info.get('name')
                # 获取任务组名
                job_group = query_job._jobstore_alias
                # 获取任务执行器
                job_executor = query_job_info.get('executor')
                # 获取调用目标字符串
                invoke_target = query_job_info.get('func')
                # 获取调用函数位置参数
                job_args = ','.join(query_job_info.get('args'))
                # 获取调用函数关键字参数
                job_kwargs = json.dumps(query_job_info.get('kwargs'))
                # 获取任务触发器
                job_trigger = str(query_job_info.get('trigger'))
                # 构造日志消息
                job_message = f'事件类型: {event_type}, 任务ID: {job_id}, 任务名称: {job_name}, 执行于{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                job_log = JobLogModel(
                    jobName=job_name,
                    jobGroup=job_group,
                    jobExecutor=job_executor,
                    invokeTarget=invoke_target,
                    jobArgs=job_args,
                    jobKwargs=job_kwargs,
                    jobTrigger=job_trigger,
                    jobMessage=job_message,
                    status=status,
                    exceptionInfo=exception_info,
                    createTime=datetime.now(),
                )
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    logger.warning('scheduler_event_listener 未检测到运行中的事件循环，跳过任务日志写入')
                    return
                task = loop.create_task(cls._persist_job_log(job_log))
                task.add_done_callback(cls._log_async_task_exception)

    @classmethod
    async def _persist_job_log(cls, job_log: JobLogModel):
        async with AsyncSessionLocal() as session:
            job_log_service = JobLogService(
                job_log_repo=JobLogRepository(session),
                query_db=session,
            )
            await job_log_service.add_job_log_services(job_log)

    @staticmethod
    def _log_async_task_exception(task: asyncio.Task):
        try:
            task.result()
        except Exception as exc:  # pragma: no cover - defensive branch
            logger.error(f'scheduler_event_listener 任务日志写入失败: {exc}')
