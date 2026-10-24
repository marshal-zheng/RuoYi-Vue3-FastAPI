"""Resilience policy configuration models."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class RetryPolicyConfig(BaseModel):
    """Retry policy settings."""

    enabled: bool = True
    max_retries: int = 3
    base_delay: float = 0.05
    max_delay: float = 1.0
    jitter: float = 0.1
    retry_exceptions: List[str] = Field(default_factory=lambda: ['TimeoutError', 'ConnectionError', 'OSError'])

    @model_validator(mode='after')
    def validate_delays(self) -> 'RetryPolicyConfig':
        if self.max_retries < 0:
            raise ValueError('max_retries must be >= 0')
        if self.base_delay <= 0:
            raise ValueError('base_delay must be > 0')
        if self.max_delay < self.base_delay:
            raise ValueError('max_delay must be >= base_delay')
        if self.jitter < 0:
            raise ValueError('jitter must be >= 0')
        return self


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker settings."""

    enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0
    half_open_max_calls: int = 3
    half_open_success_threshold: int = 2

    @model_validator(mode='after')
    def validate_thresholds(self) -> 'CircuitBreakerConfig':
        if self.failure_threshold <= 0:
            raise ValueError('failure_threshold must be > 0')
        if self.recovery_timeout_seconds <= 0:
            raise ValueError('recovery_timeout_seconds must be > 0')
        if self.half_open_max_calls <= 0:
            raise ValueError('half_open_max_calls must be > 0')
        if self.half_open_success_threshold <= 0:
            raise ValueError('half_open_success_threshold must be > 0')
        if self.half_open_success_threshold > self.half_open_max_calls:
            raise ValueError('half_open_success_threshold must be <= half_open_max_calls')
        return self


class BulkheadConfig(BaseModel):
    """Bulkhead settings."""

    enabled: bool = True
    max_concurrency: int = 64
    max_wait_seconds: float = 0.2

    @model_validator(mode='after')
    def validate_limits(self) -> 'BulkheadConfig':
        if self.max_concurrency <= 0:
            raise ValueError('max_concurrency must be > 0')
        if self.max_wait_seconds < 0:
            raise ValueError('max_wait_seconds must be >= 0')
        return self


class OperationBinding(BaseModel):
    """Binding from one operation name to resilience policy names."""

    operation: str
    retry_policy: str = 'default'
    circuit_policy: str = 'default'
    bulkhead_policy: str = 'default'
    critical: bool = True
    degraded_service: Optional[str] = None
    fallback: Optional[Any] = None


class DeepHealthConfig(BaseModel):
    """Deep health check settings."""

    timeout_seconds: float = 2.0
    external_urls: List[str] = Field(default_factory=list)


class ResiliencePolicyDocument(BaseModel):
    """Top-level resilience policy document."""

    retry_policies: Dict[str, RetryPolicyConfig] = Field(default_factory=lambda: {'default': RetryPolicyConfig()})
    circuit_policies: Dict[str, CircuitBreakerConfig] = Field(default_factory=lambda: {'default': CircuitBreakerConfig()})
    bulkhead_policies: Dict[str, BulkheadConfig] = Field(default_factory=lambda: {'default': BulkheadConfig()})
    bindings: List[OperationBinding] = Field(default_factory=list)
    deep_health: DeepHealthConfig = Field(default_factory=DeepHealthConfig)

    @model_validator(mode='after')
    def validate_bindings(self) -> 'ResiliencePolicyDocument':
        retry_names = set(self.retry_policies.keys())
        circuit_names = set(self.circuit_policies.keys())
        bulkhead_names = set(self.bulkhead_policies.keys())
        for binding in self.bindings:
            if binding.retry_policy not in retry_names:
                raise ValueError(f'Unknown retry policy: {binding.retry_policy} (op={binding.operation})')
            if binding.circuit_policy not in circuit_names:
                raise ValueError(f'Unknown circuit policy: {binding.circuit_policy} (op={binding.operation})')
            if binding.bulkhead_policy not in bulkhead_names:
                raise ValueError(f'Unknown bulkhead policy: {binding.bulkhead_policy} (op={binding.operation})')
        return self
