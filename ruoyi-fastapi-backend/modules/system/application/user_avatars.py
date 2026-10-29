"""User avatar binding and read projection (the binding table is the only avatar source of truth)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from config.error_codes import ErrorCode
from exceptions.exception import ResourceNotFoundException
from module_admin.entity.do.user_do import UserDO
from modules.file_assets.ports import OwnerRef, get_binding_service
from modules.system.application.file_asset_policies import USER_AVATAR_FIELD, USER_OWNER_TYPE

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.file_assets.ports import Actor


async def attach_user_avatars(session: AsyncSession, users: Iterable[Any]) -> None:
    """One batched projection for any list/detail/profile model carrying user_id + avatar fields."""
    targets = [user for user in users if user is not None and getattr(user, 'user_id', None) is not None]
    if not targets:
        return
    projection = await get_binding_service().project(
        session, USER_OWNER_TYPE, [user.user_id for user in targets], USER_AVATAR_FIELD
    )
    for user in targets:
        descriptors = projection.get(str(user.user_id)) or []
        user.avatar_asset_id = descriptors[0].asset_id if descriptors else None
        user.avatar_url = descriptors[0].content_url if descriptors else None


async def replace_user_avatar(session: AsyncSession, actor: Actor, user_id: int, asset_id: str) -> None:
    """Avatar business transaction: lock the user, then atomically replace the single avatar binding."""
    locked = await session.scalar(
        select(UserDO.user_id).where(UserDO.user_id == user_id, UserDO.del_flag == '0').with_for_update()
    )
    if locked is None:
        raise ResourceNotFoundException(error_code=ErrorCode.USER_NOT_FOUND, user_message='用户不存在')
    await get_binding_service().replace_field_assets(
        session, actor, OwnerRef.of(USER_OWNER_TYPE, user_id), USER_AVATAR_FIELD, [asset_id], creating=False
    )


async def release_user_assets(session: AsyncSession, user_id: int) -> list[str]:
    """Deleting a user (soft delete included) releases its asset bindings in the same transaction."""
    return await get_binding_service().release_owner(session, OwnerRef.of(USER_OWNER_TYPE, user_id))
