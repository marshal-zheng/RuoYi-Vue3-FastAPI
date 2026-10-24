from sqlalchemy import Column, DateTime, Integer, String
from module_admin.entity.do.base import LegacyBaseModel, LogBaseModel
from module_admin.entity.do.enums import JobStatusEnum, MisfirePolicyEnum, BusinessStatusEnum


class JobDO(LegacyBaseModel):
    """
    定时任务调度表
    """

    __tablename__ = 'sys_job'

    job_id = Column(Integer, primary_key=True, autoincrement=True, comment='任务ID')
    job_name = Column(String(64), nullable=True, default='', comment='任务名称')
    job_group = Column(String(64), nullable=True, default='default', comment='任务组名')
    job_executor = Column(String(64), nullable=True, default='default', comment='任务执行器')
    invoke_target = Column(String(500), nullable=False, comment='调用目标字符串')
    job_args = Column(String(255), nullable=True, default='', comment='位置参数')
    job_kwargs = Column(String(255), nullable=True, default='', comment='关键字参数')
    cron_expression = Column(String(255), nullable=True, default='', comment='cron执行表达式')
    misfire_policy = Column(
        String(20),
        nullable=True,
        default=MisfirePolicyEnum.ABANDON.value,
        comment='计划执行错误策略（1立即执行 2执行一次 3放弃执行）',
    )
    concurrent = Column(String(1), nullable=True, default='1', comment='是否并发执行（0允许 1禁止）')
    status = Column(String(1), nullable=True, default=JobStatusEnum.NORMAL.value, comment='状态（0正常 1暂停）')
    remark = Column(String(500), nullable=True, default='', comment='备注信息')


class JobLogDO(LogBaseModel):
    """
    定时任务调度日志表
    """

    __tablename__ = 'sys_job_log'

    job_log_id = Column(Integer, primary_key=True, autoincrement=True, comment='任务日志ID')
    job_name = Column(String(64), nullable=False, comment='任务名称')
    job_group = Column(String(64), nullable=False, comment='任务组名')
    job_executor = Column(String(64), nullable=False, comment='任务执行器')
    invoke_target = Column(String(500), nullable=False, comment='调用目标字符串')
    job_args = Column(String(255), nullable=True, default='', comment='位置参数')
    job_kwargs = Column(String(255), nullable=True, default='', comment='关键字参数')
    job_trigger = Column(String(255), nullable=True, default='', comment='任务触发器')
    job_message = Column(String(500), nullable=True, default='', comment='日志信息')
    status = Column(String(1), nullable=True, default=BusinessStatusEnum.SUCCESS.value, comment='执行状态（0正常 1失败）')
    exception_info = Column(String(2000), nullable=True, default='', comment='异常信息')
