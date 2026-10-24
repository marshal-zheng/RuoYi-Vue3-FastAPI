from __future__ import annotations

from pathlib import Path

import pytest

from scripts.internal.db_workflow.capability_models import (
    CAPABILITY_MANAGED_OBJECT_DOMAINS,
    LEGACY_CAPABILITY_MODULE_KEY,
    CapabilityCompilationChecksums,
    CapabilityResourceState,
    CapabilityRuntimeGate,
    CompiledCapabilityState,
    ModuleCapabilityDeclaration,
    ModuleReleaseSelection,
    ResolvedReleaseState,
    capability_domain_for_entity,
    normalize_capability_object_domain,
)


def test_capability_models_capture_compiled_and_release_state() -> None:
    resources = CapabilityResourceState(
        menus={100: {'menu_id': 100, 'menu_name': '参数配置'}},
        role_grants={'common': (100,)},
        configs={'capability.generator.enabled': {'config_key': 'capability.generator.enabled'}},
    )
    runtime_gate = CapabilityRuntimeGate(
        module_key='generator',
        config_key='capability.generator.enabled',
        default_enabled=False,
    )
    declaration = ModuleCapabilityDeclaration(
        module_key='generator',
        source_path=Path('capabilities/modules/generator.module.yaml'),
        dependencies=('system',),
        resources=resources,
        runtime_gate=runtime_gate,
    )
    compiled = CompiledCapabilityState(
        modules={'generator': declaration},
        resources=resources,
        runtime_gates={'generator': runtime_gate},
        checksums=CapabilityCompilationChecksums(
            source_checksum='source-sha',
            compiled_checksum='compiled-sha',
        ),
    )
    release_selection = ModuleReleaseSelection(
        version='2',
        release_key='standard-2026-04-05',
        modules={'generator': True, 'system': True},
    )
    resolved = ResolvedReleaseState(
        release_key=release_selection.release_key,
        enabled_modules=('generator', 'system'),
        resources=compiled.resources,
        runtime_gates=compiled.runtime_gates,
        compiled_checksum=compiled.checksums.compiled_checksum,
        release_plan_checksum='release-plan-sha',
    )

    assert compiled.modules['generator'].runtime_gate == runtime_gate
    assert resolved.enabled_modules == ('generator', 'system')
    assert resolved.compiled_checksum == 'compiled-sha'


@pytest.mark.parametrize(
    ('entity_type', 'expected_domain'),
    [
        ('sys_menu', 'menus'),
        ('sys_role_menu', 'role_grants'),
        ('sys_dict_type', 'dict_types'),
        ('sys_dict_data', 'dict_data'),
        ('sys_config', 'configs'),
    ],
)
def test_capability_domain_helpers_normalize_legacy_scope_names(entity_type: str, expected_domain: str) -> None:
    assert capability_domain_for_entity(entity_type) == expected_domain
    assert normalize_capability_object_domain(expected_domain) == expected_domain

    if entity_type == 'sys_role_menu':
        assert normalize_capability_object_domain(None, owner_scope='role_menus') == 'role_grants'

    assert expected_domain in CAPABILITY_MANAGED_OBJECT_DOMAINS


def test_legacy_module_key_is_stable() -> None:
    assert LEGACY_CAPABILITY_MODULE_KEY == 'legacy.seed-data'
