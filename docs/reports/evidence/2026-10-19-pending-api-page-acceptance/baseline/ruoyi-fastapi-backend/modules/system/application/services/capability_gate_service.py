"""Runtime capability gate resolution for module-scoped HTTP interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Request  # noqa: TC002

from config.enums import RedisInitKeyConfig
from exceptions.exception import PermissionException
from scripts.internal.db_workflow.capability_declaration_compiler import CapabilityDeclarationCompiler

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from scripts.internal.db_workflow.capability_models import CapabilityRuntimeGate


class CapabilityGateService:
    """Resolve module runtime gates from compiled capability declarations."""

    def __init__(self, *, runtime_gates: Mapping[str, CapabilityRuntimeGate] | None = None) -> None:
        self._runtime_gates = dict(runtime_gates or {})

    @classmethod
    def from_declarations(cls, *, modules_root: str | Path | None = None) -> CapabilityGateService:
        compiled_state = CapabilityDeclarationCompiler(modules_root=modules_root).compile()
        return cls(runtime_gates=compiled_state.runtime_gates)

    @property
    def runtime_gates(self) -> dict[str, CapabilityRuntimeGate]:
        return dict(self._runtime_gates)

    def get_runtime_gate(self, module_key: str) -> CapabilityRuntimeGate | None:
        return self._runtime_gates.get(str(module_key).strip())

    async def is_module_enabled(self, request: Request, module_key: str) -> bool:
        runtime_gate = self.get_runtime_gate(module_key)
        if runtime_gate is None:
            return True

        redis = getattr(request.app.state, 'redis', None)
        if redis is None:
            return False

        raw_value = await redis.get(self._redis_key(runtime_gate.config_key))
        normalized = self._normalize_enabled_value(raw_value)
        if normalized is None:
            return False
        return normalized

    async def assert_module_enabled(self, request: Request, module_key: str) -> None:
        if await self.is_module_enabled(request, module_key):
            return

        runtime_gate = self.get_runtime_gate(module_key)
        config_key = runtime_gate.config_key if runtime_gate is not None else f'capability.{module_key}.enabled'
        raise PermissionException(
            user_message=f'模块 {module_key} 当前未启用',
            developer_message=(
                f'Capability gate denied request for module={module_key}, '
                f'config_key={config_key}, request_path={request.url.path}'
            ),
            resource=module_key,
        )

    @staticmethod
    def _redis_key(config_key: str) -> str:
        return f'{RedisInitKeyConfig.SYS_CONFIG.key}:{config_key}'

    @staticmethod
    def _normalize_enabled_value(value: Any) -> bool | None:
        if isinstance(value, bool):
            return value

        candidate = str(value or '').strip().lower()
        if not candidate:
            return None
        if candidate in {'true', '1', 'yes', 'y', 'on'}:
            return True
        if candidate in {'false', '0', 'no', 'n', 'off'}:
            return False
        return None


def get_capability_gate_service(request: Request) -> CapabilityGateService:
    service = getattr(request.app.state, 'capability_gate_service', None)
    if isinstance(service, CapabilityGateService):
        return service

    service = CapabilityGateService.from_declarations()
    request.app.state.capability_gate_service = service
    return service


def invalidate_capability_gate_service(target: Any) -> None:
    state = getattr(target, 'state', target)
    if state is None:
        return
    try:
        delattr(state, 'capability_gate_service')
    except AttributeError:
        return


def require_capability_enabled(module_key: str):
    async def _dependency(request: Request) -> bool:
        service = get_capability_gate_service(request)
        await service.assert_module_enabled(request, module_key)
        return True

    return _dependency
