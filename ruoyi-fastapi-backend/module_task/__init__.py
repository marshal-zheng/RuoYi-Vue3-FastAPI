from config.job_registry import JobFunctionRegistry

from . import scheduler_test

JobFunctionRegistry.register_function('module_task.scheduler_test.job', scheduler_test.job)
JobFunctionRegistry.register_function('module_task.scheduler_test.async_job', scheduler_test.async_job)
