import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from apscheduler.events import (
    EVENT_JOB_ADDED,
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    JobEvent,
    JobExecutionEvent,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import config.get_scheduler as target
from module_admin.entity.do.job_do import JobDO, JobLogDO


@pytest.mark.asyncio
async def test_date_job_result_is_recorded_after_scheduler_removes_job(monkeypatch):
    observed = asyncio.Event()
    persist = AsyncMock(side_effect=lambda _event: observed.set())
    monkeypatch.setattr(target.SchedulerUtil, '_persist_job_event', persist)
    scheduler = AsyncIOScheduler()
    scheduler.add_listener(target.SchedulerUtil.scheduler_event_listener)
    scheduler.start()
    try:

        async def harmless_job():
            return 'completed'

        scheduler.add_job(harmless_job, 'date', id='123')
        await asyncio.wait_for(observed.wait(), 2)
        assert scheduler.get_job('123') is None
        assert persist.await_count == 1
        assert persist.await_args.args[0].code == EVENT_JOB_EXECUTED
    finally:
        scheduler.shutdown(wait=False)
        await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_registration_event_is_not_reported_as_success(monkeypatch):
    persist = AsyncMock()
    monkeypatch.setattr(target.SchedulerUtil, '_persist_job_event', persist)
    target.SchedulerUtil.scheduler_event_listener(JobEvent(EVENT_JOB_ADDED, '123', 'default'))
    await asyncio.sleep(0)
    persist.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'code,status,exception',
    [(EVENT_JOB_EXECUTED, '0', None), (EVENT_JOB_ERROR, '1', ValueError('failed')), (EVENT_JOB_MISSED, '1', None)],
)
async def test_execution_outcome_uses_persisted_definition(monkeypatch, code, status, exception):
    session = AsyncMock()
    transaction = MagicMock()
    transaction.__aenter__ = AsyncMock()
    transaction.__aexit__ = AsyncMock(return_value=False)
    session.begin = MagicMock(return_value=transaction)
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(target, 'AsyncSessionLocal', lambda: context)
    job = SimpleNamespace(
        job_name='owned job',
        job_group='default',
        job_executor='default',
        invoke_target='module_task.scheduler_test.job',
        job_args='qa',
        job_kwargs='{}',
        cron_expression='0 0 0 1 1 ?',
    )
    repository = MagicMock(find_by_id=AsyncMock(return_value=job))
    monkeypatch.setattr(target, 'JobRepository', lambda _: repository)
    service = MagicMock(add_job_log_services=AsyncMock())
    monkeypatch.setattr(target, 'JobLogService', lambda **_: service)
    event = JobExecutionEvent(code, '123', 'default', datetime.now(UTC), exception=exception)
    await target.SchedulerUtil._persist_job_event(event)
    repository.find_by_id.assert_awaited_once_with(123)
    log = service.add_job_log_services.await_args.args[0]
    assert log.job_name == 'owned job'
    assert log.status == status
    assert log.exception_info == ('任务错过计划执行时间' if code == EVENT_JOB_MISSED else str(exception or ''))
    assert 'JobExecutionEvent' in log.job_message


@pytest.mark.asyncio
async def test_execution_log_commits_after_reading_the_job(monkeypatch):
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(lambda conn: JobDO.__table__.create(conn))
        await connection.run_sync(lambda conn: JobLogDO.__table__.create(conn))
    try:
        async with sessions() as session, session.begin():
            session.add(JobDO(job_id=123, job_name='owned job', invoke_target='module_task.scheduler_test.job'))
        monkeypatch.setattr(target, 'AsyncSessionLocal', sessions)
        event = JobExecutionEvent(EVENT_JOB_EXECUTED, '123', 'default', datetime.now(UTC))
        await target.SchedulerUtil._persist_job_event(event)
        async with sessions() as session:
            rows = (await session.execute(select(JobLogDO))).scalars().all()
            assert len(rows) == 1
            assert rows[0].job_name == 'owned job'
            assert rows[0].status == '0'
    finally:
        await engine.dispose()
