import pytest

from resilience.saga_engine import InMemorySagaStore, SagaEngine, SagaStepDefinition


@pytest.mark.asyncio
async def test_saga_compensates_on_failure():
    calls = []

    async def step1_action(payload):
        calls.append('step1_action')

    async def step1_compensate(payload):
        calls.append('step1_compensate')

    async def step2_action(payload):
        calls.append('step2_action')
        raise RuntimeError('step2_failed')

    async def step2_compensate(payload):
        calls.append('step2_compensate')

    engine = SagaEngine(store=InMemorySagaStore())
    instance = await engine.execute(
        name='test_saga',
        payload={'x': 1},
        steps=[
            SagaStepDefinition(name='step1', action=step1_action, compensate=step1_compensate),
            SagaStepDefinition(name='step2', action=step2_action, compensate=step2_compensate),
        ],
    )

    assert instance['status'] in ('FAILED', 'FAILED_NEEDS_MANUAL_INTERVENTION')
    assert calls[0] == 'step1_action'
    assert calls[1] == 'step2_action'
    assert 'step1_compensate' in calls
