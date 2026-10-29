"""Scheduler entry points (registered invoke targets for sys_job; all run with concurrent='1')."""

from __future__ import annotations

from modules.file_assets.application.composition import peek_file_asset_services
from utils.log_util import logger

JOB_MAINTAIN = 'modules.file_assets.jobs.maintain'
JOB_SWEEP_ORPHANS = 'modules.file_assets.jobs.sweep_orphans'
JOB_PURGE_TOMBSTONES = 'modules.file_assets.jobs.purge_tombstones'

# (job_name, invoke_target, cron, remark) seeded idempotently by the file asset schema step.
MAINTENANCE_JOBS = (
    (
        '文件资产-回收与删除',
        JOB_MAINTAIN,
        '0 * * * * ?',
        '每分钟：草稿到期/上传遗弃/失败记录认领为待删除，并按资产状态执行到期删除（失败持久化退避）',
    ),
    (
        '文件资产-孤儿对象清扫',
        JOB_SWEEP_ORPHANS,
        '0 30 3 * * ?',
        '每日：列举当前与上一月前缀，删除宽限期后记录为 FAILED/DELETED 的对象，备份恢复与迁移窗口请暂停',
    ),
    ('文件资产-墓碑清除', JOB_PURGE_TOMBSTONES, '0 0 4 * * ?', '每日：清除已确认删除满保留期的 DELETED 记录'),
)


def _services():
    services = peek_file_asset_services()
    if services is None:
        logger.warning('file_assets job skipped: services are not initialized in this process')
    return services


async def maintain() -> dict:
    services = _services()
    if services is None:
        return {'skipped': 'not_initialized'}
    reclaim = await services.cleanup.reclaim()
    deletions = await services.cleanup.run_deletions()
    return {'reclaim': reclaim, 'deletions': deletions}


async def sweep_orphans() -> dict:
    services = _services()
    if services is None:
        return {'skipped': 'not_initialized'}
    report = await services.cleanup.sweep_orphans(scheduled=True)
    return report.to_dict()


async def purge_tombstones() -> int:
    services = _services()
    if services is None:
        return 0
    return await services.cleanup.purge_tombstones()
