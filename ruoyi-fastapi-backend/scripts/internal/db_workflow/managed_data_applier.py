"""Managed data applier for normalized planner operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from module_admin.entity.do.config_do import ConfigDO
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleMenuDO
from modules.system.runtime.menu_registry_loader import MENU_FIELDS

from .managed_data_planner import (
    CONFIG_FIELDS,
    DICT_DATA_FIELDS,
    DICT_TYPE_FIELDS,
    ManagedDataCurrentState,
    ManagedDataManagedScope,
    ManagedDataOperation,
    ManagedDataPlan,
    has_dict_data_business_key_conflict,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class ManagedDataApplyReport:
    """Result of applying or dry-running a managed data plan."""

    dry_run: bool
    applied_operations: int
    skipped_operations: int
    affected_objects: tuple[str, ...]


class ManagedDataApplier:
    """Apply normalized managed data operations to the database."""

    def __init__(self, query_db: AsyncSession, *, actor: str = 'db_workflow') -> None:
        self.query_db = query_db
        self.actor = actor

    async def load_current_state(self, managed_scope: ManagedDataManagedScope | None = None) -> ManagedDataCurrentState:
        menu_rows = (await self.query_db.execute(select(MenuDO))).scalars().all()
        role_menu_rows = (await self.query_db.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
        dict_type_rows = (await self.query_db.execute(select(DictTypeDO))).scalars().all()
        dict_data_rows = (await self.query_db.execute(select(DictDataDO))).scalars().all()
        config_rows = (await self.query_db.execute(select(ConfigDO))).scalars().all()

        menus_by_id = {int(row.menu_id): self._normalize_menu_row(row) for row in menu_rows}
        role_menu_pairs = {(int(row.role_id), int(row.menu_id)) for row in role_menu_rows}
        dict_types_by_id = {int(row.dict_id): self._normalize_dict_type_row(row) for row in dict_type_rows}
        dict_type_ids_by_key = {
            normalized['dict_type']: dict_id
            for dict_id, normalized in dict_types_by_id.items()
        }
        dict_data_by_code = {int(row.dict_code): self._normalize_dict_data_row(row) for row in dict_data_rows}
        # When duplicate business keys exist, prefer the highest dict_code so the
        # legacy duplicate is treated as the managed row and can be pruned later.
        dict_data_codes_by_business_key = {
            (normalized['dict_type'], normalized['dict_value']): dict_code
            for dict_code, normalized in sorted(dict_data_by_code.items())
        }
        configs_by_id = {int(row.config_id): self._normalize_config_row(row) for row in config_rows}
        config_ids_by_key = {
            normalized['config_key']: config_id
            for config_id, normalized in configs_by_id.items()
        }

        explicit_scope = managed_scope or ManagedDataManagedScope()

        return ManagedDataCurrentState(
            menus_by_id=menus_by_id,
            role_menu_pairs=role_menu_pairs,
            dict_types_by_id=dict_types_by_id,
            dict_type_ids_by_key=dict_type_ids_by_key,
            dict_data_by_code=dict_data_by_code,
            dict_data_codes_by_business_key=dict_data_codes_by_business_key,
            configs_by_id=configs_by_id,
            config_ids_by_key=config_ids_by_key,
            managed_scope=ManagedDataManagedScope(
                menu_ids=explicit_scope.menu_ids,
                role_menu_pairs=explicit_scope.role_menu_pairs,
                dict_type_ids=explicit_scope.dict_type_ids,
                dict_data_codes=explicit_scope.dict_data_codes,
                config_ids=explicit_scope.config_ids,
            ),
        )

    async def apply_plan(
        self,
        plan: ManagedDataPlan,
        *,
        dry_run: bool = False,
        managed_scope: ManagedDataManagedScope | None = None,
    ) -> ManagedDataApplyReport:
        has_external_transaction = self.query_db.in_transaction()
        current_state = await self.load_current_state(managed_scope)
        self._precheck_plan(plan, current_state)

        if dry_run:
            return ManagedDataApplyReport(
                dry_run=True,
                applied_operations=0,
                skipped_operations=plan.operation_count,
                affected_objects=tuple(operation.object_key for operation in plan.operations),
            )

        applied_operations = 0
        skipped_operations = 0
        now = datetime.now()

        try:
            if has_external_transaction:
                applied_operations, skipped_operations = await self._execute_plan(plan, now=now)
            else:
                applied_operations, skipped_operations = await self._execute_plan(plan, now=now)
                await self.query_db.commit()
        except Exception:
            if self.query_db.in_transaction():
                await self.query_db.rollback()
            raise

        return ManagedDataApplyReport(
            dry_run=False,
            applied_operations=applied_operations,
            skipped_operations=skipped_operations,
            affected_objects=tuple(operation.object_key for operation in plan.operations),
        )

    def _precheck_plan(self, plan: ManagedDataPlan, current_state: ManagedDataCurrentState) -> None:
        for operation in plan.operations:
            if operation.op_type not in {'delete-row', 'remove-link'}:
                continue

            if operation.entity_type == 'sys_menu':
                menu_id = int(operation.match_fields['menu_id'])
                if menu_id not in current_state.managed_scope.menu_ids and menu_id in current_state.menus_by_id:
                    raise ValueError(f'cannot prune unmanaged menu_id={menu_id}')
            elif operation.entity_type == 'sys_role_menu':
                pair = (int(operation.match_fields['role_id']), int(operation.match_fields['menu_id']))
                if pair not in current_state.managed_scope.role_menu_pairs and pair in current_state.role_menu_pairs:
                    raise ValueError(f'cannot remove unmanaged role_menu pair={pair}')
            elif operation.entity_type == 'sys_dict_type':
                dict_id = int(operation.match_fields['dict_id'])
                if dict_id not in current_state.managed_scope.dict_type_ids and dict_id in current_state.dict_types_by_id:
                    raise ValueError(f'cannot prune unmanaged dict_type dict_id={dict_id}')
            elif operation.entity_type == 'sys_dict_data':
                dict_code = int(operation.match_fields['dict_code'])
                if dict_code not in current_state.managed_scope.dict_data_codes and dict_code in current_state.dict_data_by_code:
                    raise ValueError(f'cannot prune unmanaged dict_data dict_code={dict_code}')
            elif operation.entity_type == 'sys_config':
                config_id = int(operation.match_fields['config_id'])
                if config_id not in current_state.managed_scope.config_ids and config_id in current_state.configs_by_id:
                    raise ValueError(f'cannot prune unmanaged config config_id={config_id}')

        self._precheck_business_key_conflicts(plan, current_state)

    def _precheck_business_key_conflicts(self, plan: ManagedDataPlan, current_state: ManagedDataCurrentState) -> None:
        for operation in plan.operations:
            if operation.op_type != 'upsert-row':
                continue

            values = operation.values
            if operation.entity_type == 'sys_dict_type':
                dict_id = int(values['dict_id'])
                dict_type = str(values['dict_type']).strip()
                existing_id = current_state.dict_type_ids_by_key.get(dict_type)
                if existing_id is not None and existing_id != dict_id:
                    raise ValueError(
                        f'dict_type "{dict_type}" already exists with dict_id={existing_id}, expected dict_id={dict_id}'
                    )
            elif operation.entity_type == 'sys_dict_data':
                dict_code = int(values['dict_code'])
                business_key = (str(values['dict_type']).strip(), str(values['dict_value']).strip())
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
            elif operation.entity_type == 'sys_config':
                config_id = int(values['config_id'])
                config_key = str(values['config_key']).strip()
                existing_id = current_state.config_ids_by_key.get(config_key)
                if existing_id is not None and existing_id != config_id:
                    raise ValueError(
                        f'config_key "{config_key}" already exists with config_id={existing_id}, expected config_id={config_id}'
                    )

    async def _execute_plan(self, plan: ManagedDataPlan, *, now: datetime) -> tuple[int, int]:
        applied_operations = 0
        skipped_operations = 0

        for operation in plan.operations:
            changed = await self._apply_operation(operation, now=now)
            if changed:
                applied_operations += 1
            else:
                skipped_operations += 1

        await self.query_db.flush()
        return applied_operations, skipped_operations

    async def _apply_operation(self, operation: ManagedDataOperation, *, now: datetime) -> bool:
        if operation.entity_type == 'sys_menu':
            return await self._apply_menu_operation(operation, now=now)
        if operation.entity_type == 'sys_role_menu':
            return await self._apply_role_menu_operation(operation)
        if operation.entity_type == 'sys_dict_type':
            return await self._apply_dict_type_operation(operation, now=now)
        if operation.entity_type == 'sys_dict_data':
            return await self._apply_dict_data_operation(operation, now=now)
        if operation.entity_type == 'sys_config':
            return await self._apply_config_operation(operation, now=now)
        raise ValueError(f'unsupported entity_type: {operation.entity_type}')

    async def _apply_menu_operation(self, operation: ManagedDataOperation, *, now: datetime) -> bool:
        menu_id = int(operation.match_fields['menu_id'])
        existing = await self.query_db.get(MenuDO, menu_id)
        if operation.op_type == 'delete-row':
            if existing is None:
                return False
            await self.query_db.delete(existing)
            return True

        if existing is None:
            self.query_db.add(
                MenuDO(
                    **{field: operation.values[field] for field in MENU_FIELDS},
                    managed_by_seed=int(operation.values.get('managed_by_seed', 1)),
                    create_by=self.actor,
                    create_time=now,
                    update_by=self.actor,
                    update_time=now,
                )
            )
            return True

        changed = False
        for field in MENU_FIELDS:
            if getattr(existing, field) != operation.values[field]:
                setattr(existing, field, operation.values[field])
                changed = True
        if int(existing.managed_by_seed or 0) != int(operation.values.get('managed_by_seed', 1)):
            existing.managed_by_seed = int(operation.values.get('managed_by_seed', 1))
            changed = True
        if changed:
            existing.update_by = self.actor
            existing.update_time = now
        return changed

    async def _apply_role_menu_operation(self, operation: ManagedDataOperation) -> bool:
        role_id = int(operation.match_fields['role_id'])
        menu_id = int(operation.match_fields['menu_id'])
        existing = await self.query_db.get(RoleMenuDO, {'role_id': role_id, 'menu_id': menu_id})

        if operation.op_type == 'remove-link':
            if existing is None:
                return False
            await self.query_db.delete(existing)
            return True

        if existing is not None:
            return False

        self.query_db.add(RoleMenuDO(role_id=role_id, menu_id=menu_id))
        return True

    async def _apply_dict_type_operation(self, operation: ManagedDataOperation, *, now: datetime) -> bool:
        dict_id = int(operation.match_fields['dict_id'])
        existing = await self.query_db.get(DictTypeDO, dict_id)
        if operation.op_type == 'delete-row':
            if existing is None:
                return False
            await self.query_db.delete(existing)
            return True

        if existing is None:
            self.query_db.add(
                DictTypeDO(
                    **{field: operation.values[field] for field in DICT_TYPE_FIELDS},
                    create_by=self.actor,
                    create_time=now,
                    update_by=self.actor,
                    update_time=now,
                )
            )
            return True

        changed = False
        for field in DICT_TYPE_FIELDS[1:]:
            if getattr(existing, field) != operation.values[field]:
                setattr(existing, field, operation.values[field])
                changed = True
        if changed:
            existing.update_by = self.actor
            existing.update_time = now
        return changed

    async def _apply_dict_data_operation(self, operation: ManagedDataOperation, *, now: datetime) -> bool:
        dict_code = int(operation.match_fields['dict_code'])
        existing = await self.query_db.get(DictDataDO, dict_code)
        if operation.op_type == 'delete-row':
            if existing is None:
                return False
            await self.query_db.delete(existing)
            return True

        if existing is None:
            self.query_db.add(
                DictDataDO(
                    **{field: operation.values[field] for field in DICT_DATA_FIELDS},
                    create_by=self.actor,
                    create_time=now,
                    update_by=self.actor,
                    update_time=now,
                )
            )
            return True

        changed = False
        for field in DICT_DATA_FIELDS[1:]:
            if getattr(existing, field) != operation.values[field]:
                setattr(existing, field, operation.values[field])
                changed = True
        if changed:
            existing.update_by = self.actor
            existing.update_time = now
        return changed

    async def _apply_config_operation(self, operation: ManagedDataOperation, *, now: datetime) -> bool:
        config_id = int(operation.match_fields['config_id'])
        existing = await self.query_db.get(ConfigDO, config_id)
        if operation.op_type == 'delete-row':
            if existing is None:
                return False
            await self.query_db.delete(existing)
            return True

        if existing is None:
            self.query_db.add(
                ConfigDO(
                    **{field: operation.values[field] for field in CONFIG_FIELDS},
                    create_by=self.actor,
                    create_time=now,
                    update_by=self.actor,
                    update_time=now,
                )
            )
            return True

        changed = False
        for field in CONFIG_FIELDS[1:]:
            if getattr(existing, field) != operation.values[field]:
                setattr(existing, field, operation.values[field])
                changed = True
        if changed:
            existing.update_by = self.actor
            existing.update_time = now
        return changed

    @staticmethod
    def _normalize_menu_row(row: MenuDO) -> dict[str, Any]:
        normalized = {field: getattr(row, field) for field in MENU_FIELDS}
        normalized['managed_by_seed'] = int(row.managed_by_seed or 0)
        return normalized

    @staticmethod
    def _normalize_dict_type_row(row: DictTypeDO) -> dict[str, Any]:
        return {field: getattr(row, field) for field in DICT_TYPE_FIELDS}

    @staticmethod
    def _normalize_dict_data_row(row: DictDataDO) -> dict[str, Any]:
        return {field: getattr(row, field) for field in DICT_DATA_FIELDS}

    @staticmethod
    def _normalize_config_row(row: ConfigDO) -> dict[str, Any]:
        return {field: getattr(row, field) for field in CONFIG_FIELDS}
