"""Business-transaction binding: replace a field's assets or release an owner; never commits.

Lock order shared with cleanup: the business locks its owner row first, then this service locks the
field's binding rows and finally the asset rows in ascending id order. Locking reads always see the
latest committed state; the unique constraint on asset_id is the last line of defense.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

from modules.file_assets.domain.errors import AssetConflictError, AssetInvalidError
from modules.file_assets.domain.models import (
    AssetDescriptor,
    AssetState,
    normalize_asset_id,
    normalize_owner_id,
)
from modules.file_assets.domain.types import type_for_media_type
from modules.file_assets.infrastructure.models import FileBindingDO
from modules.file_assets.infrastructure.repository import FileAssetRepository, db_utc_now

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.file_assets.application.policies import PolicyRegistry
    from modules.file_assets.domain.models import Actor, OwnerRef, PurposeSpec
    from modules.file_assets.infrastructure.models import FileAssetDO

# Exports and tree pages project every row; keep each owner IN list bounded.
PROJECTION_BATCH = 500


def normalize_asset_ids(values: Iterable[object], *, field: str) -> list[str]:
    """Canonical ids in first-occurrence order; a repeated reference binds once."""
    result: list[str] = []
    for value in values:
        asset_id = normalize_asset_id(value)
        if asset_id is None:
            raise AssetInvalidError('INVALID_ASSET_REFERENCE', '文件引用不合法', field=field)
        if asset_id not in result:
            result.append(asset_id)
    return result


class BindingService:
    def __init__(self, registry: PolicyRegistry, *, delete_grace_hours: int):
        self.registry = registry
        self.delete_grace = timedelta(hours=delete_grace_hours)

    async def replace_field_assets(
        self,
        session: AsyncSession,
        actor: Actor,
        owner: OwnerRef,
        field_key: str,
        asset_ids: Sequence[object],
        *,
        creating: bool,
    ) -> list[str]:
        spec = self.registry.field(owner.owner_type, field_key)
        policy = self.registry.require_policy(owner.owner_type)
        await policy.authorize_write(session, actor, owner.owner_id, creating=creating)
        ids = normalize_asset_ids(asset_ids, field=field_key)
        if len(ids) > spec.max_count:
            raise AssetInvalidError('TOO_MANY_ASSETS', f'最多关联 {spec.max_count} 个文件', field=field_key)

        repo = FileAssetRepository(session)
        current = await repo.owner_bindings(owner, field_key)
        existing = [binding.asset_id for binding in current]
        locked = await repo.lock_assets(set(ids) | set(existing))
        now = await db_utc_now(session)
        for asset_id in ids:
            if asset_id not in existing:
                self._check_new_draft(locked.get(asset_id), actor, owner, spec, now, creating)
        if ids == existing:
            return ids

        await repo.delete_bindings(binding.binding_id for binding in current)
        await session.flush()
        for position, asset_id in enumerate(ids):
            session.add(
                FileBindingDO(
                    asset_id=asset_id,
                    owner_type=owner.owner_type,
                    owner_id=owner.owner_id,
                    field_key=field_key,
                    position=position,
                    created_at=now,
                    created_by=actor.user_id,
                )
            )
            asset = locked[asset_id]
            if asset.first_bound_at is None:
                asset.first_bound_at = now
                asset.updated_at = now
        self._release(locked, [asset_id for asset_id in existing if asset_id not in ids], now)
        await self._flush(session)
        return ids

    async def release_owner(
        self, session: AsyncSession, owner: OwnerRef, *, field_keys: Iterable[str] | None = None
    ) -> list[str]:
        """Delete and soft delete both release every binding in the business transaction."""
        repo = FileAssetRepository(session)
        keys = set(field_keys) if field_keys is not None else None
        bindings = [b for b in await repo.owner_bindings(owner) if keys is None or b.field_key in keys]
        if not bindings:
            return []
        released = [binding.asset_id for binding in bindings]
        locked = await repo.lock_assets(released)
        now = await db_utc_now(session)
        await repo.delete_bindings(binding.binding_id for binding in bindings)
        await session.flush()
        self._release(locked, released, now)
        await self._flush(session)
        return released

    async def project(
        self, session: AsyncSession, owner_type: str, owner_ids: Iterable[object], field_key: str
    ) -> dict[str, list[AssetDescriptor]]:
        """Batched read projection for list/detail/export DTOs: one bounded IN query per chunk, never per row."""
        ids = sorted({normalize_owner_id(owner_id) for owner_id in owner_ids})
        result: dict[str, list[AssetDescriptor]] = {owner_id: [] for owner_id in ids}
        repo = FileAssetRepository(session)
        for start in range(0, len(ids), PROJECTION_BATCH):
            chunk = ids[start : start + PROJECTION_BATCH]
            for binding, asset in await repo.bindings_for_owners(owner_type, chunk, field_key):
                if asset.state != AssetState.READY.value:
                    continue
                result[binding.owner_id].append(
                    AssetDescriptor(
                        asset_id=asset.asset_id,
                        name=asset.display_name,
                        media_type=asset.media_type or 'application/octet-stream',
                        size=int(asset.size_bytes or 0),
                    )
                )
        return result

    # ---------------------------------------------------------------- helpers ----

    @staticmethod
    def _check_new_draft(
        asset: FileAssetDO | None,
        actor: Actor,
        owner: OwnerRef,
        spec: PurposeSpec,
        now: datetime,
        creating: bool,
    ) -> None:
        if asset is None or asset.uploader_id != actor.user_id:
            # Someone else's or a missing asset is indistinguishable from an invalid reference.
            raise AssetInvalidError('ASSET_NOT_AVAILABLE', '文件不存在或不可用', field=spec.field_key)
        if asset.first_bound_at is not None and asset.state == AssetState.READY.value:
            # Every bind stamps first_bound_at under this row lock: bound (or once bound) elsewhere.
            raise AssetConflictError('ASSET_ALREADY_BOUND', '文件已被其他数据使用', field=spec.field_key)
        if asset.state != AssetState.READY.value:
            raise AssetConflictError('ASSET_NOT_BINDABLE', '文件状态已变化，请重新上传', field=spec.field_key)
        if asset.expires_at is None or asset.expires_at <= now:
            raise AssetConflictError('ASSET_EXPIRED', '文件已过期，请重新上传', field=spec.field_key)
        if asset.purpose != spec.purpose or asset.intended_owner_type != owner.owner_type:
            raise AssetInvalidError('ASSET_PURPOSE_MISMATCH', '文件用途与字段不符', field=spec.field_key)
        if asset.intended_owner_id is None:
            if not creating:
                # A create-intent draft only binds inside the transaction that creates its owner.
                raise AssetInvalidError('ASSET_CONTEXT_MISMATCH', '文件上传上下文与当前数据不符', field=spec.field_key)
        elif asset.intended_owner_id != owner.owner_id:
            raise AssetInvalidError('ASSET_CONTEXT_MISMATCH', '文件上传上下文与当前数据不符', field=spec.field_key)
        file_type = type_for_media_type(asset.media_type or '')
        if file_type is None or file_type.type_id not in spec.allowed_type_ids:
            raise AssetInvalidError('ASSET_TYPE_NOT_ALLOWED', '文件类型不符合字段要求', field=spec.field_key)

    def _release(self, locked: dict[str, FileAssetDO], asset_ids: Iterable[str], now: datetime) -> None:
        """Released assets stop serving content immediately; physical deletion waits for the grace period."""
        for asset_id in asset_ids:
            asset = locked.get(asset_id)
            if asset is None or asset.state not in {AssetState.READY.value, AssetState.FAILED.value}:
                continue
            asset.state = AssetState.DELETING.value
            asset.delete_after = now + self.delete_grace
            asset.delete_next_attempt_at = None
            asset.updated_at = now

    @staticmethod
    async def _flush(session: AsyncSession) -> None:
        try:
            await session.flush()
        except IntegrityError:
            raise AssetConflictError('ASSET_ALREADY_BOUND', '文件已被其他数据使用') from None
