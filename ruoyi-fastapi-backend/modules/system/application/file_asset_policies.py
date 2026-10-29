"""File asset owner policies of the system context (user avatar, notice images)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from module_admin.entity.do.notice_do import NoticeDO
from module_admin.entity.do.user_do import UserDO
from modules.file_assets.ports import (
    IMAGE_TYPE_IDS,
    MAX_IMAGE_BYTES,
    AssetKind,
    AssetPermissionDeniedError,
    ImageProfile,
    PermissionOwnerPolicy,
    PurposeSpec,
    UploadEntry,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.file_assets.ports import Actor

USER_OWNER_TYPE = 'system.user'
USER_AVATAR_FIELD = 'avatar'
USER_AVATAR_PURPOSE = 'user.avatar'
NOTICE_OWNER_TYPE = 'system.notice'
NOTICE_CONTENT_FIELD = 'noticeContent'
NOTICE_IMAGE_PURPOSE = 'notice.image'
NOTICE_MAX_IMAGES = 20

USER_AVATAR = PurposeSpec(
    purpose=USER_AVATAR_PURPOSE,
    owner_type=USER_OWNER_TYPE,
    field_key=USER_AVATAR_FIELD,
    kind=AssetKind.IMAGE,
    allowed_type_ids=IMAGE_TYPE_IDS,
    max_bytes=MAX_IMAGE_BYTES,
    max_count=1,
    upload_entry=UploadEntry.DEDICATED,
    image_profile=ImageProfile.AVATAR,
)

NOTICE_IMAGE = PurposeSpec(
    purpose=NOTICE_IMAGE_PURPOSE,
    owner_type=NOTICE_OWNER_TYPE,
    field_key=NOTICE_CONTENT_FIELD,
    kind=AssetKind.IMAGE,
    allowed_type_ids=IMAGE_TYPE_IDS,
    max_bytes=MAX_IMAGE_BYTES,
    max_count=NOTICE_MAX_IMAGES,
    upload_entry=UploadEntry.GENERIC,
    image_profile=ImageProfile.STANDARD,
    create_permission='system:notice:add',
    edit_permission='system:notice:edit',
)


class UserAvatarPolicy:
    """Avatars: self-service writes; a bound avatar of a non-deleted user is readable by any signed-in user."""

    owner_type = USER_OWNER_TYPE
    purposes = (USER_AVATAR,)

    async def authorize_upload(
        self, session: AsyncSession, actor: Actor, purpose: PurposeSpec, owner_id: str | None
    ) -> None:
        if owner_id != str(actor.user_id):
            raise AssetPermissionDeniedError()

    async def authorize_write(self, session: AsyncSession, actor: Actor, owner_id: str, *, creating: bool) -> None:
        if creating or owner_id != str(actor.user_id):
            raise AssetPermissionDeniedError()

    def can_read_draft(self, actor: Actor, purpose: PurposeSpec, intended_owner_id: str | None) -> bool:
        return intended_owner_id == str(actor.user_id)

    async def readable_owner_ids(
        self, session: AsyncSession, actor: Actor, owner_ids: set[str], field_key: str
    ) -> set[str]:
        # Soft-deleted users are filtered by the global del_flag criteria; no department/data scope in v1.
        ids = [int(owner_id) for owner_id in owner_ids if owner_id.isdigit()]
        if not ids:
            return set()
        rows = await session.scalars(select(UserDO.user_id).where(UserDO.user_id.in_(ids), UserDO.del_flag == '0'))
        return {str(user_id) for user_id in rows.all()}


class NoticeImagePolicy(PermissionOwnerPolicy):
    """Notice images follow the notice's real read paths: list returns full content, query the detail."""

    owner_type = NOTICE_OWNER_TYPE
    purposes = (NOTICE_IMAGE,)

    async def existing_owner_ids(self, session: AsyncSession, owner_ids: set[str]) -> set[str]:
        ids = [int(owner_id) for owner_id in owner_ids if owner_id.isdigit()]
        if not ids:
            return set()
        rows = await session.scalars(select(NoticeDO.notice_id).where(NoticeDO.notice_id.in_(ids)))
        return {str(notice_id) for notice_id in rows.all()}

    async def readable_owner_ids(
        self, session: AsyncSession, actor: Actor, owner_ids: set[str], field_key: str
    ) -> set[str]:
        if not (actor.has_permission('system:notice:list') or actor.has_permission('system:notice:query')):
            return set()
        return await self.existing_owner_ids(session, owner_ids)
