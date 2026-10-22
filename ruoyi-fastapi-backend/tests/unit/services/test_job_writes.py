"""Job writes through real persistence and an isolated APScheduler instance."""

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from config.job_registry import JobFunctionRegistry
from exceptions.exception import ValidationException
from module_admin.entity.do.job_do import JobDO
from module_admin.entity.vo.job_vo import JobModel
from modules.scheduler.application.job_service import JobService
from modules.scheduler.infrastructure.job_repository import JobRepository


async def harmless(*args, **kwargs):
    return args, kwargs


@pytest.fixture
async def runtime(db_session):
    scheduler = AsyncIOScheduler(executors={'default': AsyncIOExecutor()})
    scheduler.start(paused=True)
    target = 'module_task.contract_test.harmless'
    JobFunctionRegistry.register_function(target, harmless)
    with patch('config.get_scheduler.scheduler', scheduler):
        service = JobService(JobRepository(db_session), db_session)
        yield SimpleNamespace(service=service, scheduler=scheduler, db=db_session, target=target)
        await db_session.execute(delete(JobDO).where(JobDO.invoke_target == target))
        await db_session.commit()
    scheduler.shutdown(wait=False)
    JobFunctionRegistry.unregister(target)


def config(runtime, **changes):
    return JobModel(
        job_name='contract',
        job_group='default',
        job_executor='default',
        invoke_target=runtime.target,
        cron_expression='0 0 0 * * ?',
        status='1',
        **changes,
    )


async def create(runtime, status='0'):
    data = config(runtime)
    data.status = status
    result = await runtime.service.add_job_services(data)
    return result.result['jobId']


@pytest.mark.asyncio
async def test_partial_edit_preserves_enabled_schedule_and_configuration(runtime):
    job_id = await create(runtime)
    await runtime.service.edit_job_services(JobModel(job_id=job_id, remark='changed'))
    row = await runtime.db.get(JobDO, job_id)
    assert row.status == '0'
    assert row.invoke_target == runtime.target
    assert runtime.scheduler.get_job(str(job_id)) is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'changes,field',
    [
        ({'invoke_target': 'module_task.missing'}, 'invoke_target'),
        ({'cron_expression': 'bad cron'}, 'cron_expression'),
        ({'cron_expression': '0 0 0 1 1 ? xxxx'}, 'cron_expression'),
        ({'job_kwargs': '[]'}, 'job_kwargs'),
        ({'job_group': 'unknown'}, 'job_group'),
        ({'job_executor': 'unknown'}, 'job_executor'),
    ],
)
async def test_invalid_edit_preserves_database_and_previous_schedule(runtime, changes, field):
    job_id = await create(runtime)
    before = runtime.scheduler.get_job(str(job_id)).__getstate__()
    with pytest.raises(ValidationException) as failure:
        await runtime.service.edit_job_services(JobModel(job_id=job_id, **changes))
    assert failure.value.extra['field'] == field
    row = await runtime.db.get(JobDO, job_id)
    assert row.invoke_target == runtime.target
    assert row.cron_expression == '0 0 0 * * ?'
    assert runtime.scheduler.get_job(str(job_id)).__getstate__() == before


@pytest.mark.asyncio
async def test_commit_failure_restores_database_and_exact_previous_schedule(runtime):
    job_id = await create(runtime)
    before = runtime.scheduler.get_job(str(job_id)).__getstate__()
    with (
        patch.object(runtime.db, 'commit', side_effect=RuntimeError('commit rejected')),
        pytest.raises(RuntimeError, match='commit rejected'),
    ):
        await runtime.service.edit_job_services(JobModel(job_id=job_id, remark='must rollback', status='1'))
    row = (await runtime.db.execute(select(JobDO).where(JobDO.job_id == job_id))).scalar_one()
    assert row.remark != 'must rollback'
    assert row.status == '0'
    assert runtime.scheduler.get_job(str(job_id)).__getstate__() == before


@pytest.mark.asyncio
async def test_run_once_uses_persisted_args_and_preserves_paused_state(runtime):
    data = config(runtime, job_args='one,two', job_kwargs='{"answer":42}')
    result = await runtime.service.add_job_services(data)
    job_id = result.result['jobId']
    assert runtime.scheduler.get_job(str(job_id)) is None
    result = await runtime.service.execute_job_once_services(JobModel(job_id=job_id))
    scheduled = runtime.scheduler.get_job(str(job_id))
    assert scheduled.args == ('one', 'two')
    assert scheduled.kwargs == {'answer': 42}
    assert (await runtime.db.get(JobDO, job_id)).status == '1'
    assert result.result == {'jobId': job_id, 'jobGroup': 'default'}


@pytest.mark.asyncio
async def test_existing_example_functions_are_registered():
    assert JobFunctionRegistry.exists('module_task.scheduler_test.job')
    assert JobFunctionRegistry.exists('module_task.scheduler_test.async_job')


@pytest.mark.asyncio
async def test_status_transition_changes_only_status_and_keeps_parameters(runtime):
    job_id = await create(runtime, status='1')
    await runtime.service.change_job_status_services(
        JobModel(job_id=job_id, status='0', invoke_target='forged', job_args='forged')
    )
    assert runtime.scheduler.get_job(str(job_id)).func is harmless
    row = await runtime.db.get(JobDO, job_id)
    assert row.invoke_target == runtime.target
    assert row.job_args != 'forged'
    await runtime.service.change_job_status_services(JobModel(job_id=job_id, status='1'))
    assert runtime.scheduler.get_job(str(job_id)) is None
    assert row.status == '1'


@pytest.mark.asyncio
async def test_pause_can_stop_existing_invalid_configuration(runtime):
    job_id = await create(runtime)
    row = await runtime.db.get(JobDO, job_id)
    row.cron_expression = 'old invalid cron'
    await runtime.db.commit()
    await runtime.service.change_job_status_services(JobModel(job_id=job_id, status='1'))
    assert runtime.scheduler.get_job(str(job_id)) is None
    assert row.status == '1'


@pytest.mark.asyncio
async def test_scheduler_failure_restores_database_and_schedule(runtime):
    job_id = await create(runtime)
    before = runtime.scheduler.get_job(str(job_id)).__getstate__()
    original = runtime.scheduler.add_job
    calls = 0

    def fail_after_replacement(*args, **kwargs):
        nonlocal calls
        calls += 1
        result = original(*args, **kwargs)
        if calls == 1:
            raise RuntimeError('scheduler store failure')
        return result

    with patch.object(runtime.scheduler, 'add_job', side_effect=fail_after_replacement), pytest.raises(RuntimeError):
        await runtime.service.edit_job_services(JobModel(job_id=job_id, remark='must rollback'))
    row = (await runtime.db.execute(select(JobDO).where(JobDO.job_id == job_id))).scalar_one()
    assert row.remark != 'must rollback'
    assert runtime.scheduler.get_job(str(job_id)).__getstate__() == before


@pytest.mark.asyncio
async def test_failed_delayed_commit_never_executes_new_task(runtime):
    called = []

    async def record():
        called.append(True)

    JobFunctionRegistry.register_function(runtime.target, record)
    data = config(runtime)
    data.status = '0'
    data.cron_expression = '* * * * * ?'
    runtime.scheduler.resume()

    async def fail_commit():
        await asyncio.sleep(1.2)
        raise RuntimeError('late commit failure')

    with patch.object(runtime.db, 'commit', side_effect=fail_commit), pytest.raises(RuntimeError):
        await runtime.service.add_job_services(data)
    assert called == []
    assert runtime.scheduler.get_jobs() == []


@pytest.mark.asyncio
async def test_group_move_removes_old_store_schedule(runtime):
    runtime.scheduler.add_jobstore('memory', alias='second')
    job_id = await create(runtime)
    await runtime.service.edit_job_services(JobModel(job_id=job_id, job_group='second'))
    jobs = runtime.scheduler.get_jobs()
    assert len(jobs) == 1
    assert jobs[0]._jobstore_alias == 'second'
    assert (await runtime.db.get(JobDO, job_id)).job_group == 'second'


@pytest.mark.asyncio
async def test_run_once_executes_and_preserves_enabled_or_paused_status(runtime):
    executed = asyncio.Queue()

    async def record(*args, **kwargs):
        await executed.put((args, kwargs))

    JobFunctionRegistry.register_function(runtime.target, record)
    job_id = await create(runtime)
    runtime.scheduler.resume()
    await runtime.service.execute_job_once_services(JobModel(job_id=job_id))
    await asyncio.wait_for(executed.get(), timeout=2)
    assert runtime.scheduler.get_job(str(job_id)) is not None
    assert (await runtime.db.get(JobDO, job_id)).status == '0'
    await runtime.service.change_job_status_services(JobModel(job_id=job_id, status='1'))
    await runtime.service.execute_job_once_services(JobModel(job_id=job_id))
    await asyncio.wait_for(executed.get(), timeout=2)
    assert runtime.scheduler.get_job(str(job_id)) is None
    assert (await runtime.db.get(JobDO, job_id)).status == '1'
    assert executed.empty()


@pytest.mark.asyncio
async def test_failed_change_cannot_overwrite_concurrent_success(runtime):
    job_id = await create(runtime)
    entered, release = asyncio.Event(), asyncio.Event()
    rollback = runtime.db.rollback
    original = runtime.scheduler.add_job
    failed_once = False

    async def delayed_rollback():
        entered.set()
        await release.wait()
        await rollback()

    def fail_candidate(*args, **kwargs):
        nonlocal failed_once
        result = original(*args, **kwargs)
        if kwargs.get('name') == 'failed A' and not failed_once:
            failed_once = True
            raise RuntimeError('A rejected')
        return result

    async def attempt(task):
        try:
            return await task
        except RuntimeError as error:
            return error

    factory = async_sessionmaker(runtime.db.bind, expire_on_commit=False)
    async with factory() as other:
        second = JobService(JobRepository(other), other)
        with (
            patch.object(runtime.db, 'rollback', side_effect=delayed_rollback),
            patch.object(runtime.scheduler, 'add_job', side_effect=fail_candidate),
        ):
            a = asyncio.create_task(
                attempt(runtime.service.edit_job_services(JobModel(job_id=job_id, job_name='failed A')))
            )
            await asyncio.wait_for(entered.wait(), timeout=2)
            b = asyncio.create_task(second.edit_job_services(JobModel(job_id=job_id, job_name='successful B')))
            await asyncio.sleep(0.05)
            serialized = not b.done()
            release.set()
            assert isinstance(await a, RuntimeError)
            await b
        assert serialized
        row = await other.get(JobDO, job_id)
        assert row.job_name == 'successful B'
        assert runtime.scheduler.get_job(str(job_id)).name == row.job_name
