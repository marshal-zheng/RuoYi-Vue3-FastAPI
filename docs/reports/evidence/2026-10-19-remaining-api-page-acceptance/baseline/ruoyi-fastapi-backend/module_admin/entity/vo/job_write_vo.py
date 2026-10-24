"""Operation-specific public inputs for scheduled jobs."""

from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from module_admin.entity.vo.base import CamelModelBase


class _JobEditorFields(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    job_name: str = Field(default=None, min_length=1, max_length=64, description='任务名称')
    job_group: str = Field(default=None, min_length=1, max_length=64, description='任务组名')
    job_executor: str = Field(default=None, min_length=1, max_length=64, description='任务执行器')
    invoke_target: str = Field(default=None, min_length=1, max_length=500, description='已注册调用目标')
    cron_expression: str = Field(default=None, min_length=1, max_length=255, description='Cron执行表达式')
    job_args: str | None = Field(default=None, max_length=255, description='逗号分隔的位置参数')
    job_kwargs: str | None = Field(default=None, max_length=255, description='JSON对象形式的关键字参数')
    misfire_policy: Literal['1', '2', '3'] = Field(default=None, description='计划执行错误策略')
    concurrent: Literal['0', '1'] = Field(default=None, description='是否并发执行')
    status: Literal['0', '1'] = Field(default=None, description='状态(0正常 1暂停)')
    remark: str | None = Field(default=None, max_length=500, description='备注')

    @model_validator(mode='after')
    def validate_nonblank_fields(self):
        for name in ('job_name', 'job_group', 'job_executor', 'invoke_target', 'cron_expression'):
            if name in self.model_fields_set and not getattr(self, name).strip():
                raise ValueError(f'{name}不能为空')
        return self


class JobCreateModel(_JobEditorFields):
    job_name: str = Field(min_length=1, max_length=64, description='任务名称')
    invoke_target: str = Field(min_length=1, max_length=500, description='已注册调用目标')
    cron_expression: str = Field(min_length=1, max_length=255, description='Cron执行表达式')


class JobUpdateModel(_JobEditorFields):
    job_id: int = Field(gt=0, description='任务ID')


class JobStatusUpdateModel(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    job_id: int = Field(gt=0, description='任务ID')
    status: Literal['0', '1'] = Field(description='状态(0正常 1暂停)')


class JobRunModel(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    job_id: int = Field(gt=0, description='任务ID')
