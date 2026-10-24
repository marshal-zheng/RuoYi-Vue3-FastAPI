"""Resilience policy center with runtime reload support."""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Dict, Optional

from resilience.models import (
    BulkheadConfig,
    CircuitBreakerConfig,
    OperationBinding,
    ResiliencePolicyDocument,
    RetryPolicyConfig,
)


class PolicyCenter:
    """In-memory policy center with atomic reload."""

    def __init__(self, document: ResiliencePolicyDocument, source_path: Optional[Path] = None) -> None:
        self._lock = RLock()
        self._document = document
        self._source_path = source_path
        self._binding_index = {item.operation: item for item in document.bindings}

    @classmethod
    def from_json_file(cls, path: Path) -> 'PolicyCenter':
        payload = json.loads(path.read_text(encoding='utf-8'))
        document = ResiliencePolicyDocument.model_validate(payload)
        return cls(document=document, source_path=path)

    @classmethod
    def from_defaults(cls) -> 'PolicyCenter':
        return cls(document=ResiliencePolicyDocument())

    def reload(self) -> None:
        """Reload policy file from source path."""
        if self._source_path is None:
            return
        payload = json.loads(self._source_path.read_text(encoding='utf-8'))
        document = ResiliencePolicyDocument.model_validate(payload)
        with self._lock:
            self._document = document
            self._binding_index = {item.operation: item for item in document.bindings}

    def update(self, payload: Dict) -> None:
        """Hot update with validated payload."""
        document = ResiliencePolicyDocument.model_validate(payload)
        with self._lock:
            self._document = document
            self._binding_index = {item.operation: item for item in document.bindings}
            if self._source_path is not None:
                self._source_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    def find_binding(self, operation: str) -> Optional[OperationBinding]:
        with self._lock:
            return self._binding_index.get(operation)

    def get_retry_policy(self, binding: OperationBinding) -> RetryPolicyConfig:
        with self._lock:
            return self._document.retry_policies[binding.retry_policy]

    def get_circuit_policy(self, binding: OperationBinding) -> CircuitBreakerConfig:
        with self._lock:
            return self._document.circuit_policies[binding.circuit_policy]

    def get_bulkhead_policy(self, binding: OperationBinding) -> BulkheadConfig:
        with self._lock:
            return self._document.bulkhead_policies[binding.bulkhead_policy]

    def list_bindings(self) -> Dict[str, OperationBinding]:
        with self._lock:
            return dict(self._binding_index)

    def snapshot(self) -> Dict:
        with self._lock:
            return self._document.model_dump(mode='json')
