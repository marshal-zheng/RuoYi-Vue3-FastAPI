"""Upload, read authorization, metadata and draft discard use cases.

Commit points (CL-01): an upload succeeds only after READY is committed. Failure or confirmed
cancellation before that marks FAILED; an unclear commit is re-read before deciding; after READY
commits, client disconnects never roll anything back. Storage I/O never holds a database session.
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from sqlalchemy.exc import SQLAlchemyError

from modules.file_assets.application.validation.pipeline import (
    PreparedFile,
    UploadPrecheck,
    precheck_upload,
    prepare_upload,
)
from modules.file_assets.domain.errors import (
    AssetConflictError,
    AssetInvalidError,
    AssetNotFoundError,
    AssetQuotaExceededError,
    FileAssetError,
    FileAssetsUnavailableError,
)
from modules.file_assets.domain.models import (
    AssetDescriptor,
    AssetState,
    UploadEntry,
    new_asset_id,
    normalize_asset_id,
    normalize_owner_id,
    object_key_for,
)
from modules.file_assets.infrastructure.models import FileAssetDO
from modules.file_assets.infrastructure.repository import FileAssetRepository, db_utc_now
from modules.file_assets.infrastructure.s3_storage import StorageError
from utils.log_util import logger

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.file_assets.application.policies import PolicyRegistry
    from modules.file_assets.application.runtime import FileAssetRuntime, Slot
    from modules.file_assets.domain.models import Actor, PurposeSpec
    from modules.file_assets.infrastructure.repository import AssetWithBinding

MAX_BATCH = 100


@dataclass
class IncomingFile:
    """An already spooled multipart file; the upload task owns closing it."""

    stream: BinaryIO
    filename: str | None
    content_type: str | None
    close: Callable[[], object] | None = None


@dataclass(frozen=True)
class ContentPlan:
    asset_id: str
    object_key: str
    media_type: str
    size: int
    sha256: str
    display_name: str
    inline: bool


@dataclass
class _UploadFlags:
    cancelled: bool = False
    started: float = field(default_factory=time.monotonic)


def descriptor_of(asset: FileAssetDO) -> AssetDescriptor:
    return AssetDescriptor(
        asset_id=asset.asset_id,
        name=asset.display_name,
        media_type=asset.media_type or 'application/octet-stream',
        size=int(asset.size_bytes or 0),
    )


class AssetService:
    def __init__(
        self, runtime: FileAssetRuntime, registry: PolicyRegistry, session_factory: Callable[[], AsyncSession]
    ):
        self.runtime = runtime
        self.registry = registry
        self.session_factory = session_factory

    # ------------------------------------------------------------------ upload ----

    def resolve_purpose(self, purpose: str, *, entry: UploadEntry) -> PurposeSpec:
        spec = self.registry.purpose(purpose)
        if spec.upload_entry is not entry:
            # e.g. avatars are uploaded only through the avatar business endpoint.
            raise AssetInvalidError('PURPOSE_ENTRY_MISMATCH', '该用途不能通过此入口上传', field='purpose')
        return spec

    async def upload(
        self,
        *,
        actor: Actor,
        spec: PurposeSpec,
        owner_id: str | None,
        incoming: IncomingFile,
        slot: Slot,
    ) -> AssetDescriptor:
        """Takes ownership of `slot` and `incoming`; both are released when the real work ends."""
        flags = _UploadFlags()
        task = asyncio.create_task(self._run_upload(actor, spec, owner_id, incoming, slot, flags))
        self.runtime.inflight_uploads.add(task)
        task.add_done_callback(self.runtime.inflight_uploads.discard)
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            # The client is gone before we answered: an uncommitted READY must not happen.
            flags.cancelled = True
            raise

    async def _run_upload(
        self,
        actor: Actor,
        spec: PurposeSpec,
        owner_id: str | None,
        incoming: IncomingFile,
        slot: Slot,
        flags: _UploadFlags,
    ) -> AssetDescriptor:
        metrics = self.runtime.metrics
        workdir = Path(tempfile.mkdtemp(prefix='fa-', dir=self.runtime.settings.file_asset_temp_dir or None))
        try:
            precheck = precheck_upload(
                spec, filename=incoming.filename, declared_type=incoming.content_type, size=_stream_size(incoming)
            )
            if flags.cancelled:
                raise asyncio.CancelledError
            asset = await self._create_uploading(actor, spec, owner_id, precheck)
            asset_id = asset.asset_id
            await self._checkpoint(asset_id, flags)
            prepared = await self._validate(asset_id, spec, incoming, precheck, workdir)
            await self._checkpoint(asset_id, flags)
            await self._store(asset, prepared)
            await self._checkpoint(asset_id, flags)
            descriptor = await self._commit_ready(asset_id, prepared)
            metrics.inc('upload_success_total', purpose=spec.purpose)
            logger.info(
                'file_assets.upload ready asset={} purpose={} size={} duration_ms={}',
                asset_id,
                spec.purpose,
                prepared.size,
                int((time.monotonic() - flags.started) * 1000),
            )
            return descriptor
        except asyncio.CancelledError:
            metrics.inc('upload_cancelled_total')
            raise
        except FileAssetError:
            metrics.inc('upload_failure_total')
            raise
        finally:
            if incoming.close is not None:
                result = incoming.close()
                if asyncio.iscoroutine(result):
                    await result
            shutil.rmtree(workdir, ignore_errors=True)
            slot.release()

    async def _checkpoint(self, asset_id: str, flags: _UploadFlags) -> None:
        """Confirmed cancellation before READY becomes FAILED, so the draft can never be bound."""
        if flags.cancelled:
            await self._fail(asset_id, 'UPLOAD_CANCELLED')
            raise asyncio.CancelledError

    async def _validate(
        self, asset_id: str, spec: PurposeSpec, incoming: IncomingFile, precheck: UploadPrecheck, workdir: Path
    ) -> PreparedFile:
        try:
            return await self.runtime.submit_upload(self._prepare, spec, incoming, precheck, workdir)
        except FileAssetError as exc:
            await self._fail(asset_id, 'VALIDATION_FAILED')
            self.runtime.metrics.inc('upload_rejected_total', reason=exc.reason)
            raise
        except Exception:
            await self._fail(asset_id, 'PROCESSING_ERROR')
            raise

    async def _store(self, asset: FileAssetDO, prepared: PreparedFile) -> None:
        storage = self.runtime.require_available()
        try:
            # SDK-bounded retries; the same immutable key and bytes make a repeated PUT harmless.
            await self.runtime.submit_upload(
                storage.put, asset.object_key, prepared.path, prepared.size, prepared.media_type
            )
        except StorageError as exc:
            await self._fail(asset.asset_id, 'STORAGE_ERROR')
            self.runtime.metrics.inc('storage_error_total', operation='put')
            logger.warning('file_assets.upload storage_error asset={} code={}', asset.asset_id, exc.code)
            raise FileAssetsUnavailableError('STORAGE_UNAVAILABLE') from None

    @staticmethod
    def _prepare(spec: PurposeSpec, incoming: IncomingFile, precheck: UploadPrecheck, workdir: Path) -> PreparedFile:
        source = workdir / 'source'
        incoming.stream.seek(0)
        with source.open('wb') as target:
            shutil.copyfileobj(incoming.stream, target, length=1024 * 1024)
        return prepare_upload(spec, source, precheck, workdir=workdir)

    async def _create_uploading(
        self, actor: Actor, spec: PurposeSpec, owner_id: str | None, precheck: UploadPrecheck
    ) -> FileAssetDO:
        settings = self.runtime.settings
        policy = self.registry.require_policy(spec.owner_type)
        async with self.session_factory() as session:
            await policy.authorize_upload(session, actor, spec, owner_id)
            usage = await FileAssetRepository(session).draft_usage(actor.user_id)
            if usage.count >= settings.file_asset_draft_quota_count:
                self.runtime.metrics.inc('upload_quota_rejected_total', kind='count')
                raise AssetQuotaExceededError('DRAFT_COUNT_EXCEEDED', retry_after=60)
            # Count the incoming file too, so serial uploads cannot overshoot the cap by one file each.
            if usage.total_bytes + precheck.size > settings.file_asset_draft_quota_bytes:
                self.runtime.metrics.inc('upload_quota_rejected_total', kind='bytes')
                raise AssetQuotaExceededError('DRAFT_BYTES_EXCEEDED', retry_after=60)
            now = await db_utc_now(session)
            asset_id = new_asset_id()
            storage = self.runtime.require_available()
            asset = FileAssetDO(
                asset_id=asset_id,
                bucket=storage.bucket,
                object_key=object_key_for(asset_id, now),
                original_name=precheck.original_name,
                display_name=precheck.original_name,
                content_disposition='inline' if spec.inline else 'attachment',
                uploader_id=actor.user_id,
                purpose=spec.purpose,
                intended_owner_type=spec.owner_type,
                intended_owner_id=owner_id,
                state=AssetState.UPLOADING.value,
                created_at=now,
                updated_at=now,
                upload_deadline=now + timedelta(seconds=settings.file_asset_upload_state_timeout_seconds),
                delete_attempts=0,
            )
            session.add(asset)
            await session.commit()
            return asset

    async def _fail(self, asset_id: str, error_code: str) -> None:
        try:
            async with self.session_factory() as session:
                now = await db_utc_now(session)
                await FileAssetRepository(session).mark_upload_failed(asset_id, now=now, error_code=error_code)
                await session.commit()
        except SQLAlchemyError:
            # The row stays UPLOADING; reclamation after deadline + margin compensates.
            logger.error('file_assets.upload compensation_failed asset={} code={}', asset_id, error_code)

    async def _commit_ready(self, asset_id: str, prepared: PreparedFile) -> AssetDescriptor:
        settings = self.runtime.settings
        try:
            async with self.session_factory() as session:
                repo = FileAssetRepository(session)
                now = await db_utc_now(session)
                ready = await repo.mark_ready(
                    asset_id,
                    now=now,
                    expires_at=now + timedelta(hours=settings.file_asset_draft_ttl_hours),
                    size_bytes=prepared.size,
                    sha256=prepared.sha256,
                    media_type=prepared.media_type,
                    display_name=prepared.display_name,
                )
                await session.commit()
        except SQLAlchemyError:
            # Outcome unknown: the committed state, not the exception, decides.
            return await self._resolve_ready_outcome(asset_id)
        if not ready:
            # Reclaimed while we were slow: a late write never resurrects the row.
            raise AssetConflictError('UPLOAD_RECLAIMED', '上传超时已被回收，请重新上传')
        return AssetDescriptor(asset_id, prepared.display_name, prepared.media_type, prepared.size)

    async def _resolve_ready_outcome(self, asset_id: str) -> AssetDescriptor:
        for attempt in range(3):
            try:
                async with self.session_factory() as session:
                    asset = await FileAssetRepository(session).get(asset_id)
                    if asset is not None and asset.state == AssetState.READY.value:
                        return descriptor_of(asset)
                    if asset is not None and asset.state == AssetState.UPLOADING.value:
                        now = await db_utc_now(session)
                        await FileAssetRepository(session).mark_upload_failed(
                            asset_id, now=now, error_code='READY_COMMIT_FAILED'
                        )
                        await session.commit()
                    raise FileAssetsUnavailableError('READY_COMMIT_FAILED')
            except SQLAlchemyError:
                await asyncio.sleep(0.2 * (attempt + 1))
        raise FileAssetsUnavailableError('COMMIT_OUTCOME_UNKNOWN')

    # ---------------------------------------------------------- read access ----

    async def _visible(self, session: AsyncSession, actor: Actor, rows: dict[str, AssetWithBinding]) -> set[str]:
        now = await db_utc_now(session)
        visible: set[str] = set()
        bound: dict[tuple[str, str], dict[str, set[str]]] = {}
        for asset_id, row in rows.items():
            asset, binding = row.asset, row.binding
            if asset.state != AssetState.READY.value:
                continue
            if binding is not None:
                bound.setdefault((binding.owner_type, binding.field_key), {}).setdefault(binding.owner_id, set()).add(
                    asset_id
                )
                continue
            if self._draft_visible(actor, asset, now):
                visible.add(asset_id)
        for (owner_type, field_key), by_owner in bound.items():
            policy = self.registry.policy(owner_type)
            if policy is None:
                continue
            readable = await policy.readable_owner_ids(session, actor, set(by_owner), field_key)
            for owner_id in readable & set(by_owner):
                visible |= by_owner[owner_id]
        return visible

    def _draft_visible(self, actor: Actor, asset: FileAssetDO, now) -> bool:
        if asset.uploader_id != actor.user_id:
            return False
        if asset.first_bound_at is not None or asset.expires_at is None or asset.expires_at <= now:
            return False
        policy = self.registry.policy(asset.intended_owner_type)
        try:
            spec = self.registry.purpose(asset.purpose)
        except FileAssetError:
            return False
        if policy is None:
            return False
        can_read_draft = getattr(policy, 'can_read_draft', None)
        if can_read_draft is not None:
            return bool(can_read_draft(actor, spec, asset.intended_owner_id))
        permission = spec.create_permission if asset.intended_owner_id is None else spec.edit_permission
        return permission is not None and actor.has_permission(permission)

    async def describe(self, session: AsyncSession, actor: Actor, raw_id: str) -> AssetDescriptor:
        items, _ = await self.get_metadata(session, actor, [raw_id])
        if not items:
            raise AssetNotFoundError()
        return items[0]

    async def get_metadata(
        self, session: AsyncSession, actor: Actor, raw_ids: Sequence[object]
    ) -> tuple[list[AssetDescriptor], list[str]]:
        if len(raw_ids) > MAX_BATCH:
            raise AssetInvalidError('BATCH_TOO_LARGE', f'一次最多查询 {MAX_BATCH} 个文件', field='assetIds')
        ordered: list[str] = []
        unavailable: list[str] = []
        for raw in raw_ids:
            asset_id = normalize_asset_id(raw)
            key = asset_id or str(raw)
            if key in ordered or key in unavailable:
                continue
            (ordered if asset_id else unavailable).append(key)
        rows = await FileAssetRepository(session).get_many_with_bindings(ordered)
        visible = await self._visible(session, actor, rows)
        items = []
        for asset_id in ordered:
            if asset_id in visible:
                items.append(descriptor_of(rows[asset_id].asset))
            else:
                unavailable.append(asset_id)
        return items, unavailable

    async def authorize_content(self, session: AsyncSession, actor: Actor, raw_id: str) -> ContentPlan:
        asset_id = normalize_asset_id(raw_id)
        if asset_id is None:
            raise AssetNotFoundError()
        rows = await FileAssetRepository(session).get_many_with_bindings([asset_id])
        if asset_id not in await self._visible(session, actor, rows):
            raise AssetNotFoundError()
        asset = rows[asset_id].asset
        return ContentPlan(
            asset_id=asset.asset_id,
            object_key=asset.object_key,
            media_type=asset.media_type or 'application/octet-stream',
            size=int(asset.size_bytes or 0),
            sha256=asset.sha256 or '',
            display_name=asset.display_name,
            inline=asset.content_disposition == 'inline',
        )

    # -------------------------------------------------------------- discard ----

    async def discard(self, session: AsyncSession, actor: Actor, raw_id: str) -> None:
        """Repeatable discard of the actor's own never-bound draft; bound assets conflict."""
        asset_id = normalize_asset_id(raw_id)
        if asset_id is None:
            raise AssetNotFoundError()
        repo = FileAssetRepository(session)
        asset = (await repo.lock_assets([asset_id])).get(asset_id)
        if asset is None or asset.uploader_id != actor.user_id:
            raise AssetNotFoundError()
        if asset.first_bound_at is not None or await repo.bindings_of_assets([asset_id]):
            raise AssetConflictError('ASSET_BOUND', '文件已被业务数据使用，不能删除')
        now = await db_utc_now(session)
        if asset.state == AssetState.UPLOADING.value:
            asset.state = AssetState.FAILED.value
            asset.last_error_code, asset.last_error_at = 'UPLOAD_DISCARDED', now
            asset.updated_at = now
        elif asset.state == AssetState.READY.value:
            asset.state = AssetState.DELETING.value
            asset.delete_after = now
            asset.delete_next_attempt_at = None
            asset.updated_at = now
        # FAILED / DELETING / DELETED: already non-bindable, the repeat succeeds without change.
        await session.flush()


def normalize_upload_owner(owner_id: str | None) -> str | None:
    if owner_id is None or not str(owner_id).strip():
        return None
    try:
        return normalize_owner_id(owner_id)
    except ValueError:
        raise AssetInvalidError('INVALID_OWNER_ID', '关联的业务ID不合法', field='ownerId') from None


def _stream_size(incoming: IncomingFile) -> int:
    position = incoming.stream.tell()
    incoming.stream.seek(0, 2)
    size = incoming.stream.tell()
    incoming.stream.seek(position)
    return size
