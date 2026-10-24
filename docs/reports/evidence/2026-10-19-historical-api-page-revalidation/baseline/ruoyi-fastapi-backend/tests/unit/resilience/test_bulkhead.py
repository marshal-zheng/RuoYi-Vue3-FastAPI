import asyncio

import pytest

from resilience.bulkhead import Bulkhead, BulkheadRejectedError
from resilience.models import BulkheadConfig


@pytest.mark.asyncio
async def test_bulkhead_rejects_when_queue_timeout():
    bulkhead = Bulkhead(
        name='redis.get',
        config=BulkheadConfig(enabled=True, max_concurrency=1, max_wait_seconds=0.01),
    )

    start = asyncio.Event()

    async def slow_action():
        start.set()
        await asyncio.sleep(0.05)
        return 'ok'

    task = asyncio.create_task(bulkhead.run(slow_action))
    await start.wait()

    with pytest.raises(BulkheadRejectedError):
        await bulkhead.run(lambda: asyncio.sleep(0.0))

    await task
