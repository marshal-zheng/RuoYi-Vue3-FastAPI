"""Managed data planner for normalized database operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from modules.system.runtime.menu_registry_loader import MENU_FIELDS

if TYPE_CHECKING:
    from .managed_data_declaration_loader import ManagedDataTargetState

ManagedDataEntityType = Literal['sys_menu', 'sys_role_menu', 'sys_dict_type', 'sys_dict_data', 'sys_config']
ManagedDataOperationType = Literal['upsert-row', 'delete-row', 'ensure-link', 'remove-link']

DICT_TYPE_FIELDS = ('dict_id', 'dict_name', 'dict_type', 'status', 'remark')
DICT_DATA_FIELDS = (
    'dict_code',
    'dict_sort',
    'dict_label',
    'dict_value',
    'dict_type',
    'css_class',
    'list_class',
    'is_default',
    'status',
    'remark',
)
CONFIG_FIELDS = ('config_id', 'config_name', 'config_key', 'config_value', 'config_type', 'remark')


@dataclass(frozen=True)
class ManagedDataOperation:
    """A normalized operation emitted by the managed data planner."""

    op_type: ManagedDataOperationType
    entity_type: ManagedDataEntityType
    object_key: str
    match_fields: dict[str, Any]
    values: dict[str, Any]


@dataclass(frozen=True)
class ManagedDataManagedScope:
    """Explicitly managed object identities that may be pruned."""

    menu_ids: frozenset[int] = frozenset()
    role_menu_pairs: frozenset[tuple[int, int]] = frozenset()
    dict_type_ids: frozenset[int] = frozenset()
    dict_data_codes: frozenset[int] = frozenset()
    config_ids: frozenset[int] = frozenset()


@dataclass(frozen=True)
class ManagedDataCurrentState:
    """Normalized current database state for planner diffing."""

    menus_by_id: dict[int, dict[str, Any]]
    role_menu_pairs: set[tuple[int, int]]
    dict_types_by_id: dict[int, dict[str, Any]]
    dict_type_ids_by_key: dict[str, int]
    dict_data_by_code: dict[int, dict[str, Any]]
    dict_data_codes_by_business_key: dict[tuple[str, str], int]
    configs_by_id: dict[int, dict[str, Any]]
    config_ids_by_key: dict[str, int]
    managed_scope: ManagedDataManagedScope


@dataclass(frozen=True)
class ManagedDataPlan:
    """Normalized operation plan."""

    operations: tuple[ManagedDataOperation, ...]

    @property
    def operation_count(self) -> int:
        return len(self.operations)

    def count(self, *, op_type: ManagedDataOperationType | None = None, entity_type: ManagedDataEntityType | None = None) -> int:
        return sum(
            1
            for operation in self.operations
            if (op_type is None or operation.op_type == op_type)
            and (entity_type is None or operation.entity_type == entity_type)
        )


def has_dict_data_business_key_conflict(
    current_state: ManagedDataCurrentState,
    *,
    business_key: tuple[str, str],
    expected_dict_code: int,
) -> bool:
    """Return whether a dict_data business key points to an incompatible code."""

    existing_code = current_state.dict_data_codes_by_business_key.get(business_key)
    if existing_code is None or existing_code == expected_dict_code:
        return False

    expected_row = current_state.dict_data_by_code.get(expected_dict_code)
    if expected_row is None:
        return True

    return (
        str(expected_row.get('dict_type')).strip(),
        str(expected_row.get('dict_value')).strip(),
    ) != business_key


class ManagedDataPlanner:
    """Build normalized operations for managed menus, dicts, configs, and visibility links."""

    def plan(
        self,
        *,
        current_state: ManagedDataCurrentState,
        target_state: ManagedDataTargetState,
        role_key_to_id: dict[str, int],
    ) -> ManagedDataPlan:
        self._validate_target_state(current_state=current_state, target_state=target_state, role_key_to_id=role_key_to_id)

        upserts: list[ManagedDataOperation] = []
        ensures: list[ManagedDataOperation] = []
        removals: list[ManagedDataOperation] = []
        deletions: list[ManagedDataOperation] = []

        target_menu_ids = set(target_state.menus.keys())
        for menu_id, target_menu in sorted(target_state.menus.items()):
            existing = current_state.menus_by_id.get(menu_id)
            normalized_target = {**target_menu, 'managed_by_seed': 1}
            if existing is None or self._is_row_changed(existing, normalized_target, (*MENU_FIELDS, 'managed_by_seed')):
                upserts.append(
                    ManagedDataOperation(
                        op_type='upsert-row',
                        entity_type='sys_menu',
                        object_key=f'sys_menu:{menu_id}',
                        match_fields={'menu_id': menu_id},
                        values=normalized_target,
                    )
                )

        target_dict_type_ids = set()
        for row in sorted(target_state.dict_types.values(), key=lambda item: int(item['dict_id'])):
            dict_id = int(row['dict_id'])
            target_dict_type_ids.add(dict_id)
            existing = current_state.dict_types_by_id.get(dict_id)
            if existing is None or self._is_row_changed(existing, row, DICT_TYPE_FIELDS):
                upserts.append(
                    ManagedDataOperation(
                        op_type='upsert-row',
                        entity_type='sys_dict_type',
                        object_key=f'sys_dict_type:{dict_id}',
                        match_fields={'dict_id': dict_id},
                        values=row,
                    )
                )

        target_dict_data_codes = set()
        for row in sorted(target_state.dict_data.values(), key=lambda item: int(item['dict_code'])):
            dict_code = int(row['dict_code'])
            target_dict_data_codes.add(dict_code)
            existing = current_state.dict_data_by_code.get(dict_code)
            if existing is None or self._is_row_changed(existing, row, DICT_DATA_FIELDS):
                upserts.append(
                    ManagedDataOperation(
                        op_type='upsert-row',
                        entity_type='sys_dict_data',
                        object_key=f'sys_dict_data:{dict_code}',
                        match_fields={'dict_code': dict_code},
                        values=row,
                    )
                )

        target_config_ids = set()
        for row in sorted(target_state.configs.values(), key=lambda item: int(item['config_id'])):
            config_id = int(row['config_id'])
            target_config_ids.add(config_id)
            existing = current_state.configs_by_id.get(config_id)
            if existing is None or self._is_row_changed(existing, row, CONFIG_FIELDS):
                upserts.append(
                    ManagedDataOperation(
                        op_type='upsert-row',
                        entity_type='sys_config',
                        object_key=f'sys_config:{config_id}',
                        match_fields={'config_id': config_id},
                        values=row,
                    )
                )

        target_role_menu_pairs = self._resolve_role_menu_pairs(target_state.role_grants, role_key_to_id)
        for role_id, menu_id in sorted(target_role_menu_pairs - current_state.role_menu_pairs):
            ensures.append(
                ManagedDataOperation(
                    op_type='ensure-link',
                    entity_type='sys_role_menu',
                    object_key=f'sys_role_menu:{role_id}:{menu_id}',
                    match_fields={'role_id': role_id, 'menu_id': menu_id},
                    values={'role_id': role_id, 'menu_id': menu_id},
                )
            )

        for role_id, menu_id in sorted(current_state.managed_scope.role_menu_pairs - target_role_menu_pairs):
            removals.append(
                ManagedDataOperation(
                    op_type='remove-link',
                    entity_type='sys_role_menu',
                    object_key=f'sys_role_menu:{role_id}:{menu_id}',
                    match_fields={'role_id': role_id, 'menu_id': menu_id},
                    values={},
                )
            )

        deletions.extend(
            ManagedDataOperation(
                op_type='delete-row',
                entity_type='sys_dict_data',
                object_key=f'sys_dict_data:{dict_code}',
                match_fields={'dict_code': dict_code},
                values={},
            )
            for dict_code in sorted(current_state.managed_scope.dict_data_codes - target_dict_data_codes)
        )

        deletions.extend(
            ManagedDataOperation(
                op_type='delete-row',
                entity_type='sys_dict_type',
                object_key=f'sys_dict_type:{dict_id}',
                match_fields={'dict_id': dict_id},
                values={},
            )
            for dict_id in sorted(current_state.managed_scope.dict_type_ids - target_dict_type_ids)
        )

        deletions.extend(
            ManagedDataOperation(
                op_type='delete-row',
                entity_type='sys_config',
                object_key=f'sys_config:{config_id}',
                match_fields={'config_id': config_id},
                values={},
            )
            for config_id in sorted(current_state.managed_scope.config_ids - target_config_ids)
        )

        deletions.extend(
            ManagedDataOperation(
                op_type='delete-row',
                entity_type='sys_menu',
                object_key=f'sys_menu:{menu_id}',
                match_fields={'menu_id': menu_id},
                values={},
            )
            for menu_id in sorted(current_state.managed_scope.menu_ids - target_menu_ids)
        )

        return ManagedDataPlan(operations=(*upserts, *ensures, *removals, *deletions))

    def _validate_target_state(
        self,
        *,
        current_state: ManagedDataCurrentState,
        target_state: ManagedDataTargetState,
        role_key_to_id: dict[str, int],
    ) -> None:
        self._resolve_role_menu_pairs(target_state.role_grants, role_key_to_id)

        for row in target_state.dict_types.values():
            dict_id = int(row['dict_id'])
            dict_type = str(row['dict_type']).strip()
            existing_id = current_state.dict_type_ids_by_key.get(dict_type)
            if existing_id is not None and existing_id != dict_id:
                raise ValueError(
                    f'dict_type "{dict_type}" already exists with dict_id={existing_id}, expected dict_id={dict_id}'
                )

        for row in target_state.dict_data.values():
            dict_code = int(row['dict_code'])
            business_key = (str(row['dict_type']).strip(), str(row['dict_value']).strip())
            if has_dict_data_business_key_conflict(
                current_state,
                business_key=business_key,
                expected_dict_code=dict_code,
            ):
                existing_code = current_state.dict_data_codes_by_business_key.get(business_key)
                raise ValueError(
                    'dict_data business key already exists with a different dict_code: '
                    f'{business_key[0]}/{business_key[1]} -> {existing_code}, expected {dict_code}'
                )

        for row in target_state.configs.values():
            config_id = int(row['config_id'])
            config_key = str(row['config_key']).strip()
            existing_id = current_state.config_ids_by_key.get(config_key)
            if existing_id is not None and existing_id != config_id:
                raise ValueError(
                    f'config_key "{config_key}" already exists with config_id={existing_id}, expected config_id={config_id}'
                )

    @staticmethod
    def _resolve_role_menu_pairs(
        role_grants: dict[str, tuple[int, ...]],
        role_key_to_id: dict[str, int],
    ) -> set[tuple[int, int]]:
        resolved_pairs: set[tuple[int, int]] = set()
        for role_key, menu_ids in role_grants.items():
            if role_key not in role_key_to_id:
                raise ValueError(f'role_key not found in current database state: {role_key}')
            role_id = int(role_key_to_id[role_key])
            for menu_id in menu_ids:
                resolved_pairs.add((role_id, int(menu_id)))
        return resolved_pairs

    @staticmethod
    def _is_row_changed(existing: dict[str, Any], target: dict[str, Any], fields: tuple[str, ...]) -> bool:
        return any(existing.get(field) != target.get(field) for field in fields)
