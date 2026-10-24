"""Declarative dev-menu reconcile service based on menus.registry.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select, tuple_

from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from modules.system.runtime.menu_registry_loader import (
    DEFAULT_MENU_REGISTRY_FILE,
    MenuRegistryLoader,
)
from utils.log_util import logger
from utils.query_cache import get_query_cache

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


MENU_FIELDS = (
    'menu_id',
    'menu_name',
    'parent_id',
    'order_num',
    'path',
    'component',
    'query',
    'route_name',
    'is_frame',
    'is_cache',
    'menu_type',
    'visible',
    'status',
    'perms',
    'icon',
    'remark',
)


@dataclass
class SyncReport:
    success: bool
    trigger: str
    added: int = 0
    updated: int = 0
    deleted: int = 0
    role_menu_deleted: int = 0
    duration_ms: int = 0
    dry_run: bool = False
    error: str | None = None
    synced_at: datetime | None = None


class DevMenuReconcileService:
    """Reconcile menus registry declared target state into database state."""

    def __init__(
        self,
        query_db: AsyncSession | None,
        registry_file: Path | str | None = None,
        registry_loader: MenuRegistryLoader | None = None,
    ) -> None:
        self.query_db = query_db
        self.registry_file = Path(registry_file) if registry_file else DEFAULT_MENU_REGISTRY_FILE
        self.registry_loader = registry_loader or MenuRegistryLoader(self.registry_file)

    async def sync_once(self, trigger: str, dry_run: bool = False) -> SyncReport:
        if self.query_db is None:
            raise RuntimeError('query_db is required for sync operations')

        start = perf_counter()
        report = SyncReport(success=False, trigger=trigger, dry_run=dry_run, synced_at=datetime.now())
        has_external_transaction = self.query_db.in_transaction()
        try:
            target_by_id, target_role_menu_pairs = await self._load_target_state()
            target_ids = set(target_by_id.keys())

            existing_target_rows = await self._load_existing_by_ids(target_ids)
            existing_managed_ids = await self._load_existing_managed_ids()
            scoped_menu_ids = existing_managed_ids | target_ids
            existing_role_menu_pairs = await self._load_managed_role_menu_pairs(scoped_menu_ids)

            prune_ids = existing_managed_ids - target_ids
            role_menu_pairs_to_add = target_role_menu_pairs - existing_role_menu_pairs
            role_menu_pairs_to_delete = existing_role_menu_pairs - target_role_menu_pairs

            report.added, report.updated = self._count_diff(existing_target_rows, target_by_id)
            report.deleted = len(prune_ids)

            if dry_run:
                report.role_menu_deleted = len(role_menu_pairs_to_delete)
            else:
                if has_external_transaction:
                    async with self.query_db.begin_nested():
                        report.role_menu_deleted = await self._apply_changes(
                            existing_rows=existing_target_rows,
                            target_by_id=target_by_id,
                            prune_ids=prune_ids,
                            role_menu_pairs_to_add=role_menu_pairs_to_add,
                            role_menu_pairs_to_delete=role_menu_pairs_to_delete,
                        )
                else:
                    report.role_menu_deleted = await self._apply_changes(
                        existing_rows=existing_target_rows,
                        target_by_id=target_by_id,
                        prune_ids=prune_ids,
                        role_menu_pairs_to_add=role_menu_pairs_to_add,
                        role_menu_pairs_to_delete=role_menu_pairs_to_delete,
                    )
                await self._invalidate_cache()
                if not has_external_transaction:
                    await self.query_db.commit()

            report.success = True
            report.duration_ms = int((perf_counter() - start) * 1000)
            logger.info(
                'Dev menu sync report: trigger={}, dry_run={}, added={}, updated={}, deleted={}, '
                'role_menu_deleted={}, duration_ms={}',
                trigger,
                dry_run,
                report.added,
                report.updated,
                report.deleted,
                report.role_menu_deleted,
                report.duration_ms,
            )
            return report
        except Exception as exc:
            if self.query_db.in_transaction():
                await self.query_db.rollback()
            report.error = str(exc)
            report.duration_ms = int((perf_counter() - start) * 1000)
            logger.error('Dev menu sync failed: trigger={}, dry_run={}, error={}', trigger, dry_run, exc)
            return report

    async def _load_target_state(self) -> tuple[dict[int, dict[str, Any]], set[tuple[int, int]]]:
        payload = self.registry_loader.load_registry(self.registry_file)
        role_key_to_id = await self._load_role_key_to_id()
        target_state = self.registry_loader.build_target_state(payload, role_key_to_id)
        target_menus = {
            menu_id: menu
            for menu_id, menu in target_state.target_menus.items()
            if menu.get('managed_by_seed') == 1
        }
        target_ids = set(target_menus.keys())
        target_role_menu_pairs = {
            (role_id, menu_id)
            for role_id, menu_id in target_state.target_role_menu_pairs
            if menu_id in target_ids
        }
        return target_menus, target_role_menu_pairs

    async def _load_existing_by_ids(self, menu_ids: set[int]) -> dict[int, MenuDO]:
        if not menu_ids:
            return {}
        rows = await self.query_db.execute(select(MenuDO).where(MenuDO.menu_id.in_(menu_ids)))
        return {menu.menu_id: menu for menu in rows.scalars().all()}

    async def _load_existing_managed_ids(self) -> set[int]:
        rows = await self.query_db.execute(select(MenuDO.menu_id).where(MenuDO.managed_by_seed == 1))
        return {int(row.menu_id) for row in rows.all()}

    async def _load_managed_role_menu_pairs(self, managed_menu_ids: set[int]) -> set[tuple[int, int]]:
        if not managed_menu_ids:
            return set()
        rows = await self.query_db.execute(
            select(RoleMenuDO.role_id, RoleMenuDO.menu_id).where(RoleMenuDO.menu_id.in_(managed_menu_ids))
        )
        return {(int(row.role_id), int(row.menu_id)) for row in rows.all()}

    async def _load_role_key_to_id(self) -> dict[str, int]:
        rows = await self.query_db.execute(select(RoleDO.role_key, RoleDO.role_id).where(RoleDO.del_flag != '2'))
        mapping: dict[str, int] = {}
        for row in rows.all():
            role_key = str(row.role_key or '').strip()
            if not role_key:
                continue
            mapping[role_key] = int(row.role_id)
        return mapping

    def _count_diff(self, existing_rows: dict[int, MenuDO], target_by_id: dict[int, dict[str, Any]]) -> tuple[int, int]:
        added = 0
        updated = 0
        for menu_id, target in target_by_id.items():
            existing = existing_rows.get(menu_id)
            if existing is None:
                added += 1
                continue
            if self._is_menu_changed(existing, target):
                updated += 1
        return added, updated

    async def _apply_changes(
        self,
        existing_rows: dict[int, MenuDO],
        target_by_id: dict[int, dict[str, Any]],
        prune_ids: set[int],
        role_menu_pairs_to_add: set[tuple[int, int]],
        role_menu_pairs_to_delete: set[tuple[int, int]],
    ) -> int:
        now = datetime.now()

        for menu_id, target in target_by_id.items():
            existing = existing_rows.get(menu_id)
            if existing is None:
                self.query_db.add(
                    MenuDO(
                        **{field: target[field] for field in MENU_FIELDS},
                        managed_by_seed=1,
                        create_by='seed',
                        create_time=now,
                        update_by='seed',
                        update_time=now,
                    )
                )
                continue

            if self._is_menu_changed(existing, target):
                for field in MENU_FIELDS:
                    setattr(existing, field, target[field])
                existing.managed_by_seed = 1
                existing.update_by = 'seed'
                existing.update_time = now

        if role_menu_pairs_to_delete:
            await self.query_db.execute(
                delete(RoleMenuDO).where(
                    tuple_(RoleMenuDO.role_id, RoleMenuDO.menu_id).in_(sorted(role_menu_pairs_to_delete))
                )
            )

        if role_menu_pairs_to_add:
            for role_id, menu_id in sorted(role_menu_pairs_to_add):
                self.query_db.add(RoleMenuDO(role_id=role_id, menu_id=menu_id))

        if prune_ids:
            await self.query_db.execute(
                delete(MenuDO).where(MenuDO.menu_id.in_(prune_ids), MenuDO.managed_by_seed == 1)
            )

        return len(role_menu_pairs_to_delete)

    @staticmethod
    def _is_menu_changed(existing: MenuDO, target: dict[str, Any]) -> bool:
        if existing.managed_by_seed != 1:
            return True
        return any(getattr(existing, field) != target[field] for field in MENU_FIELDS)

    @staticmethod
    async def _invalidate_cache() -> None:
        cache = get_query_cache()
        await cache.delete_pattern(f'{cache.key_prefix}:menu:*')
        await cache.delete_pattern(f'{cache.key_prefix}:role:*')
