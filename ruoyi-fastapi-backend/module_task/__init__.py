from config.job_registry import JobFunctionRegistry
from modules.file_assets import jobs as file_asset_jobs

from . import scheduler_test

JobFunctionRegistry.register_function('module_task.scheduler_test.job', scheduler_test.job)
JobFunctionRegistry.register_function('module_task.scheduler_test.async_job', scheduler_test.async_job)
JobFunctionRegistry.register_function(file_asset_jobs.JOB_MAINTAIN, file_asset_jobs.maintain)
JobFunctionRegistry.register_function(file_asset_jobs.JOB_SWEEP_ORPHANS, file_asset_jobs.sweep_orphans)
JobFunctionRegistry.register_function(file_asset_jobs.JOB_PURGE_TOMBSTONES, file_asset_jobs.purge_tombstones)
