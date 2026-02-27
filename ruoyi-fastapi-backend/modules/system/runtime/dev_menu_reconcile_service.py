"""Declarative dev-menu reconcile service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleMenuDO
from utils.log_util import logger
from utils.query_cache import get_query_cache


BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE_MENU_FILE = BACKEND_ROOT / 'scripts' / 'seed_data' / 'base' / 'menus.yaml'
DEFAULT_OVERLAY_FILE = BACKEND_ROOT / 'scripts' / 'seed_data' / 'overlays' / 'dev.yaml'

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

INTEGER_FIELDS = {'menu_id', 'parent_id', 'order_num', 'is_frame', 'is_cache'}


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
    """Reconcile menus.yaml/dev.yaml declared menus into database state."""

    def __init__(
        self,
        query_db: AsyncSession | None,
        base_menu_file: Path | str | None = None,
        overlay_file: Path | str | None = None,
    ) -> None:
        self.query_db = query_db
        self.base_menu_file = Path(base_menu_file) if base_menu_file else DEFAULT_BASE_MENU_FILE
        self.overlay_file = Path(overlay_file) if overlay_file else DEFAULT_OVERLAY_FILE

    def load_target_menus(self) -> list[dict[str, Any]]:
        base_payload = self._load_yaml(self.base_menu_file)
        overlay_payload = self._load_yaml(self.overlay_file)

        base_menus = self._ensure_menu_list(base_payload.get('menus', []))
        overlay_menus = self._ensure_menu_list(overlay_payload.get('menus', []))

        merged: dict[int, dict[str, Any]] = {}
        for item in base_menus:
            normalized = self._normalize_menu_payload(item, allow_partial=False)
            merged[normalized['menu_id']] = normalized
        for item in overlay_menus:
            normalized = self._normalize_menu_payload(item, allow_partial=True)
            menu_id = normalized['menu_id']
            existing = merged.get(menu_id)
            if existing is None:
                # Overlay may introduce brand-new menus; in this case full payload is required.
                merged[menu_id] = self._normalize_menu_payload(item, allow_partial=False)
            else:
                for field, value in normalized.items():
                    if field == 'menu_id':
                        continue
                    existing[field] = value

        return [merged[key] for key in sorted(merged.keys())]

    async def sync_once(self, trigger: str, dry_run: bool = False) -> SyncReport:
        if self.query_db is None:
            raise RuntimeError('query_db is required for sync operations')

        start = perf_counter()
        report = SyncReport(success=False, trigger=trigger, dry_run=dry_run, synced_at=datetime.now())
        try:
            target_menus = [menu for menu in self.load_target_menus() if menu['managed_by_seed'] == 1]
            target_by_id = {menu['menu_id']: menu for menu in target_menus}
            target_ids = set(target_by_id.keys())

            existing_target_rows = await self._load_existing_by_ids(target_ids)
            existing_managed_ids = await self._load_existing_managed_ids()
            prune_ids = existing_managed_ids - target_ids

            report.added, report.updated = self._count_diff(existing_target_rows, target_by_id)
            report.deleted = len(prune_ids)

            if dry_run:
                report.role_menu_deleted = await self._count_role_menus(prune_ids)
            else:
                transaction_cm = self.query_db.begin_nested() if self.query_db.in_transaction() else self.query_db.begin()
                async with transaction_cm:
                    report.role_menu_deleted = await self._apply_changes(existing_target_rows, target_by_id, prune_ids)
                await self._invalidate_cache()

            report.success = True
            report.duration_ms = int((perf_counter() - start) * 1000)
            logger.info(
                'Dev menu sync report: trigger={}, dry_run={}, added={}, updated={}, deleted={}, role_menu_deleted={}, duration_ms={}',
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

    async def _load_existing_by_ids(self, menu_ids: set[int]) -> dict[int, MenuDO]:
        if not menu_ids:
            return {}
        rows = await self.query_db.execute(select(MenuDO).where(MenuDO.menu_id.in_(menu_ids)))
        return {menu.menu_id: menu for menu in rows.scalars().all()}

    async def _load_existing_managed_ids(self) -> set[int]:
        rows = await self.query_db.execute(
            select(MenuDO.menu_id).where(MenuDO.managed_by_seed == 1)
        )
        return {row.menu_id for row in rows.all()}

    async def _count_role_menus(self, menu_ids: set[int]) -> int:
        if not menu_ids:
            return 0
        rows = await self.query_db.execute(
            select(func.count())
            .select_from(RoleMenuDO)
            .where(RoleMenuDO.menu_id.in_(menu_ids))
        )
        return int(rows.scalar() or 0)

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
    ) -> int:
        now = datetime.now()
        role_menu_deleted = 0

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

        if prune_ids:
            role_delete_result = await self.query_db.execute(
                delete(RoleMenuDO).where(RoleMenuDO.menu_id.in_(prune_ids))
            )
            role_menu_deleted = int(role_delete_result.rowcount or 0)
            await self.query_db.execute(
                delete(MenuDO).where(MenuDO.menu_id.in_(prune_ids), MenuDO.managed_by_seed == 1)
            )

        return role_menu_deleted

    @staticmethod
    def _is_menu_changed(existing: MenuDO, target: dict[str, Any]) -> bool:
        if existing.managed_by_seed != 1:
            return True
        for field in MENU_FIELDS:
            if getattr(existing, field) != target[field]:
                return True
        return False

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'on', 'yes'}
        return False

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with path.open('r', encoding='utf-8') as handle:
            payload = yaml.safe_load(handle) or {}
            if not isinstance(payload, dict):
                return {}
            return payload

    @staticmethod
    def _ensure_menu_list(raw: Any) -> list[dict[str, Any]]:
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    def _normalize_menu_payload(self, raw: dict[str, Any], *, allow_partial: bool = False) -> dict[str, Any]:
        if raw.get('menu_id') is None:
            raise ValueError('menu_id is required for dev menu sync')
        normalized: dict[str, Any] = {'menu_id': int(raw['menu_id'])}
        for field in MENU_FIELDS:
            if field == 'menu_id':
                continue
            if allow_partial and field not in raw:
                continue
            value = raw.get(field)
            if field in INTEGER_FIELDS and value is not None:
                value = int(value)
            normalized[field] = value

        if not allow_partial and normalized.get('menu_name') is None:
            raise ValueError(f'menu_name is required for menu_id={normalized["menu_id"]}')

        if 'managed_by_seed' in raw:
            normalized['managed_by_seed'] = 1 if self._to_bool(raw.get('managed_by_seed')) else 0
        elif not allow_partial:
            normalized['managed_by_seed'] = 0
        return normalized

    @staticmethod
    async def _invalidate_cache() -> None:
        cache = get_query_cache()
        await cache.delete_pattern(f'{cache.key_prefix}:menu:*')
        await cache.delete_pattern(f'{cache.key_prefix}:role:*')
