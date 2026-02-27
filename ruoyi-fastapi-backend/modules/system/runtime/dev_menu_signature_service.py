"""Development-mode authorization signature service."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.enums import StatusEnum
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from module_admin.entity.do.user_do import UserDO, UserRoleDO
from utils.db_filters import not_deleted

MENU_SIGNATURE_FIELDS = (
    'menu_id',
    'parent_id',
    'path',
    'component',
    'perms',
    'status',
    'visible',
    'order_num',
)


class DevMenuSignatureService:
    """Build deterministic authorization signature for one user session."""

    def __init__(self, query_db: AsyncSession | None) -> None:
        self.query_db = query_db

    async def get_user_signature(self, user_id: int) -> str:
        snapshot = await self.build_user_snapshot(user_id)
        payload = json.dumps(snapshot, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    async def build_user_snapshot(self, user_id: int) -> dict[str, Any]:
        query_db = self._require_query_db()

        role_ids = await self._load_user_role_ids(query_db, user_id)
        role_menus = await self._load_role_menu_pairs(query_db, role_ids)
        menu_ids = sorted({item[1] for item in role_menus})

        if 1 in role_ids:
            menu_rows = await self._load_all_active_menus(query_db)
        else:
            menu_rows = await self._load_effective_menus(query_db, menu_ids)

        menus = [
            {field: getattr(menu, field) for field in MENU_SIGNATURE_FIELDS}
            for menu in menu_rows
        ]
        return {
            'userId': user_id,
            'roles': role_ids,
            'roleMenus': [[role_id, menu_id] for role_id, menu_id in role_menus],
            'menus': menus,
        }

    def _require_query_db(self) -> AsyncSession:
        if self.query_db is None:
            raise RuntimeError('query_db is required for signature operations')
        return self.query_db

    @staticmethod
    async def _load_user_role_ids(query_db: AsyncSession, user_id: int) -> list[int]:
        rows = await query_db.execute(
            select(UserRoleDO.role_id)
            .select_from(UserRoleDO)
            .join(UserDO, UserDO.user_id == UserRoleDO.user_id)
            .join(RoleDO, RoleDO.role_id == UserRoleDO.role_id)
            .where(
                UserRoleDO.user_id == user_id,
                UserDO.status == StatusEnum.NORMAL.value,
                not_deleted(UserDO.del_flag),
                RoleDO.status == StatusEnum.NORMAL.value,
                not_deleted(RoleDO.del_flag),
            )
            .distinct()
            .order_by(UserRoleDO.role_id)
        )
        return [int(row.role_id) for row in rows.all()]

    @staticmethod
    async def _load_role_menu_pairs(query_db: AsyncSession, role_ids: list[int]) -> list[tuple[int, int]]:
        if not role_ids:
            return []

        rows = await query_db.execute(
            select(RoleMenuDO.role_id, RoleMenuDO.menu_id)
            .select_from(RoleMenuDO)
            .join(RoleDO, RoleDO.role_id == RoleMenuDO.role_id)
            .join(MenuDO, MenuDO.menu_id == RoleMenuDO.menu_id)
            .where(
                RoleMenuDO.role_id.in_(role_ids),
                RoleDO.status == StatusEnum.NORMAL.value,
                not_deleted(RoleDO.del_flag),
                MenuDO.status == StatusEnum.NORMAL.value,
            )
            .distinct()
            .order_by(RoleMenuDO.role_id, RoleMenuDO.menu_id)
        )
        return [(int(row.role_id), int(row.menu_id)) for row in rows.all()]

    @staticmethod
    async def _load_all_active_menus(query_db: AsyncSession) -> list[MenuDO]:
        rows = await query_db.execute(
            select(MenuDO)
            .where(MenuDO.status == StatusEnum.NORMAL.value)
            .order_by(MenuDO.menu_id)
        )
        return list(rows.scalars().all())

    @staticmethod
    async def _load_effective_menus(query_db: AsyncSession, menu_ids: list[int]) -> list[MenuDO]:
        if not menu_ids:
            return []
        rows = await query_db.execute(
            select(MenuDO)
            .where(
                MenuDO.menu_id.in_(menu_ids),
                MenuDO.status == StatusEnum.NORMAL.value,
            )
            .order_by(MenuDO.menu_id)
        )
        return list(rows.scalars().all())
