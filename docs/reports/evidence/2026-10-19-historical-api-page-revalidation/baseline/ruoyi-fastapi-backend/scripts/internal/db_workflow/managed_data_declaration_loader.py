"""Managed data declaration loader and module-level release-plan resolver."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from modules.system.runtime.menu_registry_loader import RegistryPayload

from .capability_declaration_compiler import CapabilityDeclarationCompiler, CapabilityDeclarationIssue
from .capability_models import CapabilityResourceState, CapabilityRuntimeGate, ModuleCapabilityDeclaration
from .release_bundle_service import compute_payload_checksum

if TYPE_CHECKING:
    from .capability_models import CompiledCapabilityState

BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SEED_DATA_DIR = BACKEND_ROOT / 'scripts' / 'seed_data'
DEFAULT_RELEASE_PLAN_FILE = DEFAULT_SEED_DATA_DIR / 'release-plan.yaml'
DEFAULT_BOOTSTRAP_ROLES_FILE = DEFAULT_SEED_DATA_DIR / 'base' / 'roles.yaml'
DEFAULT_MODULE_MANIFEST_ROOT = BACKEND_ROOT / 'capabilities' / 'modules'

MANAGED_DECLARATION_SCOPES = (
    'menus',
    'role_menus',
    'dict_types',
    'dict_data',
    'configs',
    'release_visibility',
)
BOOTSTRAP_DECLARATION_SCOPES = (
    'roles',
    'users',
    'depts',
    'posts',
    'user_roles',
    'user_posts',
    'role_depts',
)
LEGACY_DECLARATION_FILES: tuple[tuple[str, str], ...] = (
    ('menus', 'menus.registry.yaml'),
    ('dict_types', 'base/dict_types.yaml'),
    ('dict_data', 'base/dict_data.yaml'),
    ('configs', 'base/configs.yaml'),
)
RELEASE_PLAN_ALLOWED_TOP_LEVEL_KEYS = frozenset({'version', 'release_key', 'modules', 'metadata'})
RELEASE_PLAN_LEGACY_SELECTOR_KEYS = frozenset({'menu_ids', 'role_grants', 'dict_types', 'config_keys'})


@dataclass(frozen=True)
class ManagedDataDeclarationPaths:
    """Physical declaration file paths used by the workflow."""

    menu_registry: Path
    dict_types: Path
    dict_data: Path
    configs: Path
    release_plan: Path
    bootstrap_roles: Path
    module_manifest_root: Path | None = None


@dataclass(frozen=True)
class ManagedDataDeclarationIssue:
    """Unified declaration validation issue."""

    domain: str
    source_path: str
    location: str
    message: str


@dataclass(frozen=True)
class ReleasePlanSelection:
    """Resolved module-level release-plan selectors."""

    version: str
    release_key: str
    menu_ids: tuple[int, ...]
    role_grants: dict[str, tuple[int, ...]]
    dict_types: tuple[str, ...]
    config_keys: tuple[str, ...]
    modules: dict[str, bool] = field(default_factory=dict)
    enabled_modules: tuple[str, ...] = ()
    runtime_gates: dict[str, CapabilityRuntimeGate] = field(default_factory=dict)
    compiled_checksum: str = ''
    release_plan_checksum: str = ''


@dataclass(frozen=True)
class ManagedDataTargetState:
    """Normalized managed declarations for dev/finalize planning."""

    menus: dict[int, dict[str, Any]]
    role_grants: dict[str, tuple[int, ...]]
    dict_types: dict[str, dict[str, Any]]
    dict_data: dict[tuple[str, str], dict[str, Any]]
    configs: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class ManagedDataDeclarationBundle:
    """Validated managed declaration bundle."""

    paths: ManagedDataDeclarationPaths
    managed_scopes: tuple[str, ...]
    bootstrap_scopes: tuple[str, ...]
    bootstrap_role_keys: tuple[str, ...]
    menu_registry: RegistryPayload
    dev_target_state: ManagedDataTargetState
    formal_candidate_state: ManagedDataTargetState
    release_selection: ReleasePlanSelection
    compiled_capability_state: CompiledCapabilityState | None = None


@dataclass(frozen=True)
class _LoadedDeclarations:
    paths: ManagedDataDeclarationPaths
    release_plan: dict[str, Any] | None
    bootstrap_role_keys: set[str]


class ManagedDataDeclarationLoader:
    """Load and validate module declarations plus module-level release plan."""

    def __init__(
        self,
        *,
        seed_data_dir: str | Path | None = None,
        menu_registry_path: str | Path | None = None,
        dict_types_path: str | Path | None = None,
        dict_data_path: str | Path | None = None,
        configs_path: str | Path | None = None,
        release_plan_path: str | Path | None = None,
        bootstrap_roles_path: str | Path | None = None,
        module_manifest_root: str | Path | None = None,
    ) -> None:
        seed_dir = Path(seed_data_dir) if seed_data_dir else DEFAULT_SEED_DATA_DIR
        if seed_data_dir:
            project_root = seed_dir.parents[1] if seed_dir.parent.name == 'scripts' else seed_dir.parent
        else:
            project_root = BACKEND_ROOT
        resolved_module_root = (
            Path(module_manifest_root) if module_manifest_root else project_root / 'capabilities' / 'modules'
        )
        self.paths = ManagedDataDeclarationPaths(
            menu_registry=Path(menu_registry_path) if menu_registry_path else seed_dir / 'menus.registry.yaml',
            dict_types=Path(dict_types_path) if dict_types_path else seed_dir / 'base' / 'dict_types.yaml',
            dict_data=Path(dict_data_path) if dict_data_path else seed_dir / 'base' / 'dict_data.yaml',
            configs=Path(configs_path) if configs_path else seed_dir / 'base' / 'configs.yaml',
            release_plan=Path(release_plan_path) if release_plan_path else seed_dir / 'release-plan.yaml',
            bootstrap_roles=Path(bootstrap_roles_path) if bootstrap_roles_path else seed_dir / 'base' / 'roles.yaml',
            module_manifest_root=resolved_module_root,
        )
        self.module_manifest_root = resolved_module_root

    def validate(self) -> list[ManagedDataDeclarationIssue]:
        loaded, issues = self._load_declarations()
        if issues:
            return issues

        compiler_issues = self._build_capability_compiler(loaded.bootstrap_role_keys).validate()
        issues.extend(self._wrap_capability_issues(compiler_issues))
        if issues:
            return issues

        compiled_state = self._build_capability_compiler(loaded.bootstrap_role_keys).compile()
        _, resolver_issues = self._resolve_release_plan(loaded.release_plan, compiled_state)
        return resolver_issues

    def load(self) -> ManagedDataDeclarationBundle:
        loaded, issues = self._load_declarations()
        if issues:
            raise ValueError(format_managed_data_issues(issues))

        compiler = self._build_capability_compiler(loaded.bootstrap_role_keys)
        issues = self._wrap_capability_issues(compiler.validate())
        if issues:
            raise ValueError(format_managed_data_issues(issues))

        compiled_state = compiler.compile()
        release_selection, resolve_issues = self._resolve_release_plan(loaded.release_plan, compiled_state)
        if resolve_issues:
            raise ValueError(format_managed_data_issues(resolve_issues))
        assert release_selection is not None

        dev_target_state = _target_state_from_resources(compiled_state.resources)
        formal_target_state = _target_state_from_resources(
            _resources_for_enabled_modules(
                compiled_state.modules,
                set(release_selection.enabled_modules),
            )
        )
        return ManagedDataDeclarationBundle(
            paths=loaded.paths,
            managed_scopes=MANAGED_DECLARATION_SCOPES,
            bootstrap_scopes=BOOTSTRAP_DECLARATION_SCOPES,
            bootstrap_role_keys=tuple(sorted(loaded.bootstrap_role_keys)),
            menu_registry=_registry_payload_from_resources(compiled_state.resources),
            dev_target_state=dev_target_state,
            formal_candidate_state=formal_target_state,
            release_selection=release_selection,
            compiled_capability_state=compiled_state,
        )

    def _load_declarations(self) -> tuple[_LoadedDeclarations, list[ManagedDataDeclarationIssue]]:
        issues = self._validate_legacy_declarations_absent()
        release_plan, release_plan_issues = self._load_yaml_mapping(self.paths.release_plan, domain='release_visibility')
        bootstrap_role_keys, bootstrap_role_issues = self._load_bootstrap_role_keys()
        issues.extend(release_plan_issues)
        issues.extend(bootstrap_role_issues)
        return (
            _LoadedDeclarations(
                paths=self.paths,
                release_plan=release_plan,
                bootstrap_role_keys=bootstrap_role_keys,
            ),
            issues,
        )

    def _validate_legacy_declarations_absent(self) -> list[ManagedDataDeclarationIssue]:
        issues: list[ManagedDataDeclarationIssue] = []
        for domain, relative_path in LEGACY_DECLARATION_FILES:
            path = self.paths.menu_registry.parent / relative_path
            if not path.exists():
                continue
            try:
                payload = yaml.safe_load(path.read_text(encoding='utf-8'))
            except yaml.YAMLError as exc:
                issues.append(
                    self._issue(domain, path, 'file', f'legacy declaration file is invalid YAML: {exc}')
                )
                continue
            if _legacy_payload_is_empty(relative_path, payload):
                continue
            issues.append(
                self._issue(
                    domain,
                    path,
                    'file',
                    'legacy declaration file is no longer supported; migrate content into capabilities/modules/*.module.yaml',
                )
            )
        return issues

    def _load_yaml_mapping(
        self,
        path: Path,
        *,
        domain: str,
    ) -> tuple[dict[str, Any] | None, list[ManagedDataDeclarationIssue]]:
        if not path.exists():
            return None, [self._issue(domain, path, 'file', 'declaration file does not exist')]
        try:
            payload = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
        except yaml.YAMLError as exc:
            return None, [self._issue(domain, path, 'file', f'invalid YAML: {exc}')]
        if not isinstance(payload, dict):
            return None, [self._issue(domain, path, 'root', 'YAML payload must be a mapping')]
        return payload, []

    def _load_bootstrap_role_keys(self) -> tuple[set[str], list[ManagedDataDeclarationIssue]]:
        payload, issues = self._load_yaml_mapping(self.paths.bootstrap_roles, domain='bootstrap_roles')
        if payload is None:
            return set(), issues

        role_rows = payload.get('roles', [])
        if not isinstance(role_rows, list):
            issues.append(self._issue('bootstrap_roles', self.paths.bootstrap_roles, 'roles', 'roles must be a list'))
            return set(), issues

        role_keys: set[str] = set()
        for index, role in enumerate(role_rows):
            prefix = f'roles[{index}]'
            if not isinstance(role, dict):
                issues.append(self._issue('bootstrap_roles', self.paths.bootstrap_roles, prefix, 'role item must be a mapping'))
                continue
            role_key = role.get('role_key')
            if not isinstance(role_key, str) or not role_key.strip():
                issues.append(
                    self._issue('bootstrap_roles', self.paths.bootstrap_roles, f'{prefix}.role_key', 'role_key must be a non-empty string')
                )
                continue
            normalized_role_key = role_key.strip()
            if normalized_role_key in role_keys:
                issues.append(
                    self._issue(
                        'bootstrap_roles',
                        self.paths.bootstrap_roles,
                        f'{prefix}.role_key',
                        f'duplicate role_key: {normalized_role_key}',
                    )
                )
                continue
            role_keys.add(normalized_role_key)
        return role_keys, issues

    def _build_capability_compiler(self, known_role_keys: set[str]) -> CapabilityDeclarationCompiler:
        return CapabilityDeclarationCompiler(
            modules_root=self.module_manifest_root,
            known_role_keys=frozenset(known_role_keys),
        )

    def _resolve_release_plan(
        self,
        payload: dict[str, Any] | None,
        compiled_state: CompiledCapabilityState,
    ) -> tuple[ReleasePlanSelection | None, list[ManagedDataDeclarationIssue]]:
        if payload is None:
            return None, [self._issue('release_visibility', self.paths.release_plan, 'file', 'declaration file does not exist')]

        issues: list[ManagedDataDeclarationIssue] = []
        unexpected_keys = sorted(
            key
            for key in payload
            if key not in RELEASE_PLAN_ALLOWED_TOP_LEVEL_KEYS and key != 'include'
        )
        for key in unexpected_keys:
            if key in RELEASE_PLAN_LEGACY_SELECTOR_KEYS:
                issues.append(
                    self._issue(
                        'release_visibility',
                        self.paths.release_plan,
                        key,
                        f'object-level selector "{key}" is no longer supported; use modules: {{<module>: true|false}}',
                    )
                )
                continue
            issues.append(
                self._issue(
                    'release_visibility',
                    self.paths.release_plan,
                    key,
                    f'unsupported release-plan key: {key}; only version, release_key, modules, metadata are allowed',
                )
            )

        version = str(payload.get('version') or '').strip()
        if version != '2':
            issues.append(self._issue('release_visibility', self.paths.release_plan, 'version', 'version must be "2"'))

        release_key = str(payload.get('release_key') or '').strip()
        if not release_key:
            issues.append(self._issue('release_visibility', self.paths.release_plan, 'release_key', 'release_key is required'))

        if 'include' in payload:
            issues.append(
                self._issue(
                    'release_visibility',
                    self.paths.release_plan,
                    'include',
                    'object-level include selectors are no longer supported; use modules: {<module>: true|false}',
                )
            )

        metadata_payload = payload.get('metadata')
        if metadata_payload is not None and not isinstance(metadata_payload, dict):
            issues.append(
                self._issue(
                    'release_visibility',
                    self.paths.release_plan,
                    'metadata',
                    'metadata must be a mapping when present',
                )
            )

        modules_payload = payload.get('modules')
        if not isinstance(modules_payload, dict):
            issues.append(self._issue('release_visibility', self.paths.release_plan, 'modules', 'modules must be a mapping'))
            return None, issues

        normalized_modules: dict[str, bool] = {}
        for raw_module_key, enabled in modules_payload.items():
            location = f'modules.{raw_module_key}'
            if not isinstance(raw_module_key, str) or not raw_module_key.strip():
                issues.append(self._issue('release_visibility', self.paths.release_plan, location, 'module key must be a non-empty string'))
                continue
            module_key = raw_module_key.strip()
            if not isinstance(enabled, bool):
                issues.append(self._issue('release_visibility', self.paths.release_plan, location, 'module value must be true or false'))
                continue
            if module_key in normalized_modules:
                issues.append(self._issue('release_visibility', self.paths.release_plan, location, f'duplicate module key: {module_key}'))
                continue
            normalized_modules[module_key] = enabled
            if module_key not in compiled_state.modules:
                issues.append(self._issue('release_visibility', self.paths.release_plan, location, f'unknown module: {module_key}'))

        if issues:
            return None, issues

        enabled_modules, dependency_issues = self._expand_enabled_modules(normalized_modules, compiled_state.modules)
        issues.extend(dependency_issues)
        if issues:
            return None, issues

        resolved_resources = _resources_for_enabled_modules(compiled_state.modules, enabled_modules)
        resolved_runtime_gates = {
            module_key: compiled_state.runtime_gates[module_key]
            for module_key in sorted(enabled_modules)
            if module_key in compiled_state.runtime_gates
        }
        release_plan_checksum = compute_payload_checksum(payload)
        compiled_checksum = compiled_state.checksums.compiled_checksum if compiled_state.checksums else ''
        return (
            ReleasePlanSelection(
                version=version,
                release_key=release_key,
                menu_ids=tuple(sorted(resolved_resources.menus)),
                role_grants=resolved_resources.role_grants,
                dict_types=tuple(sorted(resolved_resources.dict_types)),
                config_keys=tuple(sorted(resolved_resources.configs)),
                modules={module_key: normalized_modules.get(module_key, False) for module_key in sorted(compiled_state.modules)},
                enabled_modules=tuple(sorted(enabled_modules)),
                runtime_gates=resolved_runtime_gates,
                compiled_checksum=compiled_checksum,
                release_plan_checksum=release_plan_checksum,
            ),
            issues,
        )

    def _expand_enabled_modules(
        self,
        requested_modules: dict[str, bool],
        modules: dict[str, ModuleCapabilityDeclaration],
    ) -> tuple[set[str], list[ManagedDataDeclarationIssue]]:
        enabled_modules: set[str] = set()
        issues: list[ManagedDataDeclarationIssue] = []

        def enable(module_key: str, chain: tuple[str, ...]) -> None:
            if module_key in enabled_modules:
                return
            declaration = modules[module_key]
            for dependency in declaration.dependencies:
                if requested_modules.get(dependency) is False:
                    issues.append(
                        self._issue(
                            'release_visibility',
                            self.paths.release_plan,
                            f'modules.{module_key}',
                            f'module dependency is explicitly disabled: {dependency}',
                        )
                    )
                    continue
                enable(dependency, (*chain, dependency))
            enabled_modules.add(module_key)

        for module_key, enabled in sorted(requested_modules.items()):
            if enabled and module_key in modules:
                enable(module_key, (module_key,))
        return enabled_modules, issues

    def _wrap_capability_issues(self, issues: list[CapabilityDeclarationIssue]) -> list[ManagedDataDeclarationIssue]:
        return [
            ManagedDataDeclarationIssue(
                domain=issue.domain,
                source_path=issue.source_path,
                location=issue.location,
                message=issue.message,
            )
            for issue in issues
        ]

    @staticmethod
    def _issue(domain: str, path: Path, location: str, message: str) -> ManagedDataDeclarationIssue:
        return ManagedDataDeclarationIssue(domain=domain, source_path=str(path), location=location, message=message)


def _legacy_payload_is_empty(relative_path: str, payload: Any) -> bool:
    if payload in (None, {}):
        return True
    if not isinstance(payload, dict):
        return False
    legacy_key_by_path = {
        'menus.registry.yaml': ('menus', 'role_grants'),
        'base/dict_types.yaml': ('dict_types',),
        'base/dict_data.yaml': ('dict_data',),
        'base/configs.yaml': ('configs',),
    }
    payload_keys = legacy_key_by_path.get(relative_path, ())
    return bool(payload_keys) and all(not payload.get(key) for key in payload_keys)


def _target_state_from_resources(resources: CapabilityResourceState) -> ManagedDataTargetState:
    return ManagedDataTargetState(
        menus={menu_id: dict(row) for menu_id, row in resources.menus.items()},
        role_grants={role_key: tuple(menu_ids) for role_key, menu_ids in resources.role_grants.items()},
        dict_types={dict_type: dict(row) for dict_type, row in resources.dict_types.items()},
        dict_data={key: dict(row) for key, row in resources.dict_data.items()},
        configs={config_key: dict(row) for config_key, row in resources.configs.items()},
    )


def _registry_payload_from_resources(resources: CapabilityResourceState) -> RegistryPayload:
    return RegistryPayload(
        version='2',
        menus=[dict(resources.menus[menu_id]) for menu_id in sorted(resources.menus)],
        role_grants=[
            {'role_key': role_key, 'menu_ids': list(menu_ids)}
            for role_key, menu_ids in sorted(resources.role_grants.items())
        ],
    )


def _resources_for_enabled_modules(
    modules: dict[str, ModuleCapabilityDeclaration],
    enabled_modules: set[str],
) -> CapabilityResourceState:
    menus: dict[int, dict[str, Any]] = {}
    role_grants: dict[str, set[int]] = {}
    dict_types: dict[str, dict[str, Any]] = {}
    dict_data: dict[tuple[str, str], dict[str, Any]] = {}
    configs: dict[str, dict[str, Any]] = {}

    for module_key in sorted(enabled_modules):
        declaration = modules[module_key]
        menus.update({menu_id: dict(row) for menu_id, row in declaration.resources.menus.items()})
        dict_types.update({dict_type: dict(row) for dict_type, row in declaration.resources.dict_types.items()})
        dict_data.update({key: dict(row) for key, row in declaration.resources.dict_data.items()})
        configs.update({config_key: dict(row) for config_key, row in declaration.resources.configs.items()})
        for role_key, menu_ids in declaration.resources.role_grants.items():
            role_grants.setdefault(role_key, set()).update(menu_ids)

    return CapabilityResourceState(
        menus={menu_id: menus[menu_id] for menu_id in sorted(menus)},
        role_grants={role_key: tuple(sorted(menu_ids)) for role_key, menu_ids in sorted(role_grants.items())},
        dict_types={dict_type: dict_types[dict_type] for dict_type in sorted(dict_types)},
        dict_data={key: dict_data[key] for key in sorted(dict_data)},
        configs={config_key: configs[config_key] for config_key in sorted(configs)},
    )


def format_managed_data_issues(issues: list[ManagedDataDeclarationIssue]) -> str:
    """Render validation issues as one readable error string."""

    return '; '.join(
        f'[{issue.domain}] {issue.source_path}:{issue.location}: {issue.message}'
        for issue in sorted(issues, key=lambda item: (item.domain, item.source_path, item.location, item.message))
    )
