"""Unified resilience executor: circuit -> retry -> bulkhead -> fallback."""

from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable, Optional

from resilience.bulkhead import BulkheadRejectedError, BulkheadRegistry
from resilience.circuit_breaker import CircuitBreakerOpenError, CircuitBreakerRegistry
from resilience.degradation import mark_degraded
from resilience.metrics import ResilienceMetrics
from resilience.policy_center import PolicyCenter
from resilience.retry_policy import RetryExhaustedError, execute_with_retry


class ResilienceExecutor:
    """Execute critical operations under configured resilience policies."""

    def __init__(
        self,
        *,
        policy_center: PolicyCenter,
        circuit_registry: CircuitBreakerRegistry,
        bulkhead_registry: BulkheadRegistry,
        metrics: ResilienceMetrics,
    ) -> None:
        self._policy_center = policy_center
        self._circuit_registry = circuit_registry
        self._bulkhead_registry = bulkhead_registry
        self._metrics = metrics

    async def execute(
        self,
        operation: str,
        action: Callable[[], Awaitable[Any]],
        *,
        fallback: Optional[Any] = None,
    ) -> Any:
        binding = self._policy_center.find_binding(operation)
        if binding is None:
            return await action()

        retry_policy = self._policy_center.get_retry_policy(binding)
        circuit_policy = self._policy_center.get_circuit_policy(binding)
        bulkhead_policy = self._policy_center.get_bulkhead_policy(binding)

        breaker = await self._circuit_registry.get_or_create(operation, circuit_policy)
        if not await breaker.allow_request():
            await self._metrics.inc('circuit_breaker_rejected_total')
            return await self._handle_failure(operation, CircuitBreakerOpenError(operation), binding, fallback)

        async def _invoke_retry() -> Any:
            return await execute_with_retry(operation=operation, policy=retry_policy, action=action)

        bulkhead = await self._bulkhead_registry.get_or_create(operation, bulkhead_policy)
        try:
            result = await bulkhead.run(_invoke_retry)
            await breaker.on_success()
            return result
        except BulkheadRejectedError as exc:
            await self._metrics.inc('bulkhead_rejected_total')
            await breaker.on_failure(exc)
            return await self._handle_failure(operation, exc, binding, fallback)
        except RetryExhaustedError as exc:
            retry_attempts = max(int(getattr(exc.context, 'attempts', 1)) - 1, 0)
            if retry_attempts > 0:
                await self._metrics.inc('retry_attempt_total', retry_attempts)
            await self._metrics.inc('retry_exhausted_total')
            await breaker.on_failure(exc)
            return await self._handle_failure(operation, exc, binding, fallback)
        except Exception as exc:
            await self._metrics.inc('operation_error_total')
            await breaker.on_failure(exc)
            return await self._handle_failure(operation, exc, binding, fallback)

    async def _handle_failure(self, operation: str, exc: Exception, binding, fallback: Optional[Any]) -> Any:
        if binding.critical and fallback is None:
            raise exc

        degraded_name = binding.degraded_service or operation
        mark_degraded(degraded_name, type(exc).__name__)

        chosen_fallback = fallback if fallback is not None else binding.fallback
        if callable(chosen_fallback):
            result = chosen_fallback()
            if inspect.isawaitable(result):
                return await result
            return result
        return chosen_fallback
