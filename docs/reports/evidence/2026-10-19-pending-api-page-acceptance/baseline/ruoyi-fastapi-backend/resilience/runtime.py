"""Resilience runtime wiring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncEngine

from ports import IRedisClient
from resilience.bulkhead import BulkheadRegistry
from resilience.circuit_breaker import CircuitBreakerRegistry
from resilience.executor import ResilienceExecutor
from resilience.health_deep import DeepHealthChecker
from resilience.metrics import ResilienceMetrics
from resilience.policy_center import PolicyCenter
from resilience.saga_engine import InMemorySagaStore, RedisSagaStore, SagaEngine


POLICY_FILE = Path(__file__).resolve().parent / 'policy_bindings.json'


@dataclass
class ResilienceRuntime:
    """Runtime object exposing resilience components."""

    policy_center: PolicyCenter
    circuit_registry: CircuitBreakerRegistry
    bulkhead_registry: BulkheadRegistry
    saga_engine: SagaEngine
    metrics: ResilienceMetrics
    executor: ResilienceExecutor
    deep_health_checker: DeepHealthChecker

    async def status(self) -> Dict[str, Any]:
        circuit_states = await self.circuit_registry.list_snapshots()
        bulkhead_states = await self.bulkhead_registry.list_snapshots()
        metric_counters = await self.metrics.snapshot()
        return {
            'bindings': list(self.policy_center.list_bindings().keys()),
            'circuits': circuit_states,
            'bulkheads': bulkhead_states,
            'metrics': metric_counters,
        }


def build_resilience_runtime(
    *,
    redis_client: Optional[IRedisClient],
    db_engine: AsyncEngine,
) -> ResilienceRuntime:
    if POLICY_FILE.exists():
        policy_center = PolicyCenter.from_json_file(POLICY_FILE)
    else:
        policy_center = PolicyCenter.from_defaults()

    circuit_registry = CircuitBreakerRegistry()
    bulkhead_registry = BulkheadRegistry()
    metrics = ResilienceMetrics()

    if redis_client is not None:
        saga_store = RedisSagaStore(redis_client=redis_client)
    else:
        saga_store = InMemorySagaStore()
    saga_engine = SagaEngine(store=saga_store)

    executor = ResilienceExecutor(
        policy_center=policy_center,
        circuit_registry=circuit_registry,
        bulkhead_registry=bulkhead_registry,
        metrics=metrics,
    )

    snapshot = policy_center.snapshot()
    deep_health = snapshot.get('deep_health', {})
    external_urls = deep_health.get('external_urls', [])
    timeout_seconds = float(deep_health.get('timeout_seconds', 2.0))

    deep_health_checker = DeepHealthChecker(
        db_engine=db_engine,
        redis_client=redis_client,
        external_urls=external_urls,
        timeout_seconds=timeout_seconds,
    )

    return ResilienceRuntime(
        policy_center=policy_center,
        circuit_registry=circuit_registry,
        bulkhead_registry=bulkhead_registry,
        saga_engine=saga_engine,
        metrics=metrics,
        executor=executor,
        deep_health_checker=deep_health_checker,
    )
