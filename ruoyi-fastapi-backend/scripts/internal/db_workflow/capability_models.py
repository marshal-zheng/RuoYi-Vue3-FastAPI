"""Core capability-state models and workflow metadata helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from pathlib import Path

CapabilityObjectDomain = Literal['menus', 'role_grants', 'dict_types', 'dict_data', 'configs', 'runtime_gates']

LEGACY_CAPABILITY_MODULE_KEY = 'legacy.seed-data'
CAPABILITY_MANAGED_OBJECT_DOMAINS: tuple[CapabilityObjectDomain, ...] = (
    'menus',
    'role_grants',
    'dict_types',
    'dict_data',
    'configs',
)
LEGACY_MANAGED_OBJECT_SCOPES: tuple[str, ...] = (
    'menus',
    'role_menus',
    'dict_types',
    'dict_data',
    'configs',
)

ENTITY_TYPE_TO_CAPABILITY_DOMAIN: dict[str, CapabilityObjectDomain] = {
    'sys_menu': 'menus',
    'sys_role_menu': 'role_grants',
    'sys_dict_type': 'dict_types',
    'sys_dict_data': 'dict_data',
    'sys_config': 'configs',
}


@dataclass(frozen=True)
class CapabilityResourceState:
    """Normalized object-level capability resources."""

    menus: dict[int, dict[str, Any]] = field(default_factory=dict)
    role_grants: dict[str, tuple[int, ...]] = field(default_factory=dict)
    dict_types: dict[str, dict[str, Any]] = field(default_factory=dict)
    dict_data: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    configs: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityRuntimeGate:
    """Runtime module gate derived from capability declarations."""

    module_key: str
    config_key: str
    default_enabled: bool = False


@dataclass(frozen=True)
class ModuleCapabilityDeclaration:
    """Single-module declaration source compiled into capability state."""

    module_key: str
    source_path: Path
    dependencies: tuple[str, ...] = ()
    resources: CapabilityResourceState = field(default_factory=CapabilityResourceState)
    runtime_gate: CapabilityRuntimeGate | None = None


@dataclass(frozen=True)
class CapabilityCompilationChecksums:
    """Stable checksums emitted by declaration compilation."""

    source_checksum: str
    compiled_checksum: str


@dataclass(frozen=True)
class CompiledCapabilityState:
    """Full normalized capability target state across all modules."""

    modules: dict[str, ModuleCapabilityDeclaration] = field(default_factory=dict)
    resources: CapabilityResourceState = field(default_factory=CapabilityResourceState)
    runtime_gates: dict[str, CapabilityRuntimeGate] = field(default_factory=dict)
    checksums: CapabilityCompilationChecksums | None = None


@dataclass(frozen=True)
class ModuleReleaseSelection:
    """Normalized module-level release-plan input."""

    version: str
    release_key: str
    modules: dict[str, bool]


@dataclass(frozen=True)
class ResolvedReleaseState:
    """Release target state projected from compiled capability state."""

    release_key: str
    enabled_modules: tuple[str, ...]
    resources: CapabilityResourceState = field(default_factory=CapabilityResourceState)
    runtime_gates: dict[str, CapabilityRuntimeGate] = field(default_factory=dict)
    compiled_checksum: str = ''
    release_plan_checksum: str = ''


def capability_domain_for_entity(entity_type: str) -> CapabilityObjectDomain:
    """Resolve metadata domain for a managed entity type."""

    try:
        return ENTITY_TYPE_TO_CAPABILITY_DOMAIN[entity_type]
    except KeyError as exc:
        raise ValueError(f'unsupported managed entity type: {entity_type}') from exc


def normalize_capability_object_domain(
    object_domain: str | None,
    *,
    owner_scope: str | None = None,
) -> str | None:
    """Normalize legacy workflow scope names to capability object domains."""

    candidate = str(object_domain or owner_scope or '').strip()
    if not candidate:
        return None
    if candidate == 'role_menus':
        return 'role_grants'
    return candidate
