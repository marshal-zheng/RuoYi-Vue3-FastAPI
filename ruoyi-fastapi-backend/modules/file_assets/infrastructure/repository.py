"""Asset and binding persistence; callers own every transaction boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import and_, delete, exists, func, or_, select, text, update

from modules.file_assets.domain.models import AssetState, OwnerRef
from modules.file_assets.infrastructure.models import FileAssetDO, FileBindingDO

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


async def db_utc_now(session: AsyncSession) -> datetime:
    """All lifecycle times come from the database clock (naive UTC), not from app hosts."""
    dialect = session.get_bind().dialect.name
    if dialect == 'mysql':
        return await session.scalar(text('SELECT UTC_TIMESTAMP(6)'))
    if dialect == 'postgresql':
        return await session.scalar(text("SELECT (now() AT TIME ZONE 'utc')"))
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass(frozen=True)
class DraftUsage:
    count: int
    total_bytes: int


@dataclass(frozen=True)
class AssetWithBinding:
    asset: FileAssetDO
    binding: FileBindingDO | None


class FileAssetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ---- reads -------------------------------------------------------------

    async def get(self, asset_id: str) -> FileAssetDO | None:
        return await self.session.get(FileAssetDO, asset_id)

    async def get_many_with_bindings(self, asset_ids: Sequence[str]) -> dict[str, AssetWithBinding]:
        if not asset_ids:
            return {}
        stmt = (
            select(FileAssetDO, FileBindingDO)
            .outerjoin(FileBindingDO, FileBindingDO.asset_id == FileAssetDO.asset_id)
            .where(FileAssetDO.asset_id.in_(list(asset_ids)))
        )
        rows = (await self.session.execute(stmt)).all()
        return {asset.asset_id: AssetWithBinding(asset, binding) for asset, binding in rows}

    async def draft_usage(self, uploader_id: int) -> DraftUsage:
        """Unbound drafts: UPLOADING plus never-bound READY rows of this uploader."""
        stmt = select(func.count(), func.coalesce(func.sum(FileAssetDO.size_bytes), 0)).where(
            FileAssetDO.uploader_id == uploader_id,
            FileAssetDO.first_bound_at.is_(None),
            FileAssetDO.state.in_((AssetState.UPLOADING.value, AssetState.READY.value)),
        )
        count, total = (await self.session.execute(stmt)).one()
        return DraftUsage(count=int(count or 0), total_bytes=int(total or 0))

    async def bindings_for_owners(
        self, owner_type: str, owner_ids: Iterable[str], field_key: str
    ) -> list[tuple[FileBindingDO, FileAssetDO]]:
        ids = sorted(set(owner_ids))
        if not ids:
            return []
        stmt = (
            select(FileBindingDO, FileAssetDO)
            .join(FileAssetDO, FileAssetDO.asset_id == FileBindingDO.asset_id)
            .where(
                FileBindingDO.owner_type == owner_type,
                FileBindingDO.owner_id.in_(ids),
                FileBindingDO.field_key == field_key,
            )
            .order_by(FileBindingDO.owner_id, FileBindingDO.position)
        )
        return list((await self.session.execute(stmt)).all())

    # ---- upload state transitions (short dedicated sessions) ---------------

    def add(self, asset: FileAssetDO) -> None:
        self.session.add(asset)

    async def mark_ready(
        self,
        asset_id: str,
        *,
        now: datetime,
        expires_at: datetime,
        size_bytes: int,
        sha256: str,
        media_type: str,
        display_name: str,
    ) -> bool:
        stmt = (
            update(FileAssetDO)
            .where(FileAssetDO.asset_id == asset_id, FileAssetDO.state == AssetState.UPLOADING.value)
            .values(
                state=AssetState.READY.value,
                size_bytes=size_bytes,
                sha256=sha256,
                media_type=media_type,
                display_name=display_name,
                uploaded_at=now,
                expires_at=expires_at,
                updated_at=now,
            )
        )
        return (await self.session.execute(stmt)).rowcount == 1

    async def mark_upload_failed(self, asset_id: str, *, now: datetime, error_code: str) -> bool:
        stmt = (
            update(FileAssetDO)
            .where(FileAssetDO.asset_id == asset_id, FileAssetDO.state == AssetState.UPLOADING.value)
            .values(state=AssetState.FAILED.value, last_error_code=error_code, last_error_at=now, updated_at=now)
        )
        return (await self.session.execute(stmt)).rowcount == 1

    # ---- locking -------------------------------------------------------------

    async def lock_assets(self, asset_ids: Iterable[str]) -> dict[str, FileAssetDO]:
        """Record locks on existing asset rows, ascending id order (the lock order shared with cleanup).

        Only primary keys that exist are locked: under REPEATABLE READ a locking read of a missing key
        takes a gap lock, and concurrent inserts into shared gaps are a classic InnoDB deadlock.
        """
        ids = sorted(set(asset_ids))
        if not ids:
            return {}
        existing = sorted(
            (await self.session.scalars(select(FileAssetDO.asset_id).where(FileAssetDO.asset_id.in_(ids)))).all()
        )
        if not existing:
            return {}
        stmt = (
            select(FileAssetDO)
            .where(FileAssetDO.asset_id.in_(existing))
            .order_by(FileAssetDO.asset_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return {row.asset_id: row for row in (await self.session.scalars(stmt)).all()}

    async def owner_bindings(self, owner: OwnerRef, field_key: str | None = None) -> list[FileBindingDO]:
        """Plain read; the business transaction already holds the owner row lock, which serializes every
        writer of this owner's bindings. No range locking read: it would take InnoDB gap locks."""
        conditions = [FileBindingDO.owner_type == owner.owner_type, FileBindingDO.owner_id == owner.owner_id]
        if field_key is not None:
            conditions.append(FileBindingDO.field_key == field_key)
        stmt = (
            select(FileBindingDO)
            .where(*conditions)
            .order_by(FileBindingDO.field_key, FileBindingDO.position)
            .execution_options(populate_existing=True)
        )
        return list((await self.session.scalars(stmt)).all())

    async def bindings_of_assets(self, asset_ids: Iterable[str]) -> dict[str, FileBindingDO]:
        ids = sorted(set(asset_ids))
        if not ids:
            return {}
        stmt = select(FileBindingDO).where(FileBindingDO.asset_id.in_(ids))
        return {row.asset_id: row for row in (await self.session.scalars(stmt)).all()}

    async def delete_bindings(self, binding_ids: Iterable[int]) -> None:
        """Primary-key deletes take record locks only."""
        ids = sorted(set(binding_ids))
        if ids:
            await self.session.execute(delete(FileBindingDO).where(FileBindingDO.binding_id.in_(ids)))

    # ---- cleanup claims --------------------------------------------------------

    @staticmethod
    def _skip_locked(stmt, index: str | None = None):
        """Queue claim: never wait for rows another worker holds; keep the plan index-ordered so a worker
        locks only the rows it returns (tiny tables would otherwise get a table scan + filesort)."""
        if index is not None:
            stmt = stmt.with_hint(FileAssetDO, f'FORCE INDEX ({index})', 'mysql')
        return stmt.with_for_update(skip_locked=True)

    async def claim_expired_drafts(self, now: datetime, limit: int) -> list[FileAssetDO]:
        stmt = self._skip_locked(
            select(FileAssetDO)
            .where(
                FileAssetDO.state == AssetState.READY.value,
                FileAssetDO.first_bound_at.is_(None),
                FileAssetDO.expires_at <= now,
            )
            .order_by(FileAssetDO.expires_at)
            .limit(limit),
            'ix_sys_file_asset_state_expires_at',
        )
        return list((await self.session.scalars(stmt)).all())

    async def claim_abandoned_uploads(self, cutoff: datetime, limit: int) -> list[FileAssetDO]:
        """UPLOADING rows whose deadline plus recovery margin (already folded into cutoff) has passed."""
        stmt = self._skip_locked(
            select(FileAssetDO)
            .where(FileAssetDO.state == AssetState.UPLOADING.value, FileAssetDO.upload_deadline <= cutoff)
            .order_by(FileAssetDO.upload_deadline)
            .limit(limit),
            'ix_sys_file_asset_state_upload_deadline',
        )
        return list((await self.session.scalars(stmt)).all())

    async def claim_failed(self, limit: int) -> list[FileAssetDO]:
        stmt = self._skip_locked(
            select(FileAssetDO)
            .where(FileAssetDO.state == AssetState.FAILED.value)
            .order_by(FileAssetDO.upload_deadline)
            .limit(limit),
            'ix_sys_file_asset_state_upload_deadline',
        )
        return list((await self.session.scalars(stmt)).all())

    async def claim_due_deletions(self, now: datetime, limit: int) -> list[FileAssetDO]:
        stmt = self._skip_locked(
            select(FileAssetDO)
            .where(
                FileAssetDO.state == AssetState.DELETING.value,
                FileAssetDO.delete_after <= now,
                or_(FileAssetDO.delete_next_attempt_at.is_(None), FileAssetDO.delete_next_attempt_at <= now),
            )
            # Index order on (state, delete_after): a sorted expression would make InnoDB lock every due row
            # it filesorts, so parallel workers could not skip to disjoint batches.
            .order_by(FileAssetDO.delete_after)
            .limit(limit),
            'ix_sys_file_asset_state_delete_after',
        )
        return list((await self.session.scalars(stmt)).all())

    async def claim_tombstones(self, cutoff: datetime, limit: int) -> list[str]:
        stmt = self._skip_locked(
            select(FileAssetDO.asset_id)
            .where(FileAssetDO.state == AssetState.DELETED.value, FileAssetDO.deleted_at <= cutoff)
            .order_by(FileAssetDO.deleted_at)
            .limit(limit),
            'ix_sys_file_asset_state_deleted_at',
        )
        return list((await self.session.scalars(stmt)).all())

    async def purge_tombstones(self, asset_ids: Sequence[str]) -> int:
        if not asset_ids:
            return 0
        stmt = delete(FileAssetDO).where(
            FileAssetDO.asset_id.in_(list(asset_ids)),
            FileAssetDO.state == AssetState.DELETED.value,
            ~exists().where(FileBindingDO.asset_id == FileAssetDO.asset_id),
        )
        return (await self.session.execute(stmt)).rowcount

    async def mark_deleted(self, asset_id: str, *, now: datetime) -> bool:
        stmt = (
            update(FileAssetDO)
            .where(FileAssetDO.asset_id == asset_id, FileAssetDO.state == AssetState.DELETING.value)
            .values(
                state=AssetState.DELETED.value,
                deleted_at=now,
                updated_at=now,
                delete_next_attempt_at=None,
                delete_failing_since=None,
            )
        )
        return (await self.session.execute(stmt)).rowcount == 1

    async def record_delete_failure(
        self,
        asset_id: str,
        *,
        now: datetime,
        error_code: str,
        next_attempt_at: datetime,
        count_attempt: bool,
        failing_since: datetime,
    ) -> bool:
        values: dict[str, object] = {
            'last_error_code': error_code,
            'last_error_at': now,
            'delete_next_attempt_at': next_attempt_at,
            'delete_failing_since': func.coalesce(FileAssetDO.delete_failing_since, failing_since),
            'updated_at': now,
        }
        if count_attempt:
            values['delete_attempts'] = FileAssetDO.delete_attempts + 1
        stmt = (
            update(FileAssetDO)
            .where(FileAssetDO.asset_id == asset_id, FileAssetDO.state == AssetState.DELETING.value)
            .values(**values)
        )
        return (await self.session.execute(stmt)).rowcount == 1

    async def assets_for_ids(self, asset_ids: Sequence[str]) -> dict[str, FileAssetDO]:
        if not asset_ids:
            return {}
        stmt = select(FileAssetDO).where(FileAssetDO.asset_id.in_(list(asset_ids)))
        return {row.asset_id: row for row in (await self.session.scalars(stmt)).all()}

    async def deletion_backlog(self, now: datetime, overdue_before: datetime) -> dict[str, object]:
        """Operational gauges; failing rows are reported separately from a stalled executor."""
        due = and_(FileAssetDO.state == AssetState.DELETING.value, FileAssetDO.delete_after <= now)
        backlog_stmt = select(func.count(), func.min(FileAssetDO.delete_after)).where(
            due, FileAssetDO.delete_failing_since.is_(None)
        )
        backlog, oldest_due = (await self.session.execute(backlog_stmt)).one()
        overdue = await self.session.scalar(
            select(func.count()).where(
                due, FileAssetDO.delete_failing_since.is_(None), FileAssetDO.delete_after <= overdue_before
            )
        )
        retrying_stmt = select(
            func.count(),
            func.coalesce(func.max(FileAssetDO.delete_attempts), 0),
            func.min(FileAssetDO.delete_failing_since),
        ).where(FileAssetDO.state == AssetState.DELETING.value, FileAssetDO.delete_failing_since.is_not(None))
        retrying, max_attempts, failing_since = (await self.session.execute(retrying_stmt)).one()
        invariant = await self.session.scalar(
            select(func.count()).where(
                FileAssetDO.state == AssetState.DELETING.value,
                exists().where(FileBindingDO.asset_id == FileAssetDO.asset_id),
            )
        )
        return {
            'delete_backlog': int(backlog or 0),
            'delete_overdue': int(overdue or 0),
            'oldest_delete_due_age_seconds': (now - oldest_due).total_seconds() if oldest_due else 0.0,
            'delete_retrying': int(retrying or 0),
            'max_delete_attempts': int(max_attempts or 0),
            'longest_delete_failing_seconds': (now - failing_since).total_seconds() if failing_since else 0.0,
            'binding_invariant_violation': int(invariant or 0),
        }
