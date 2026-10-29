"""Application services on SQLite + fake storage.

These prove state transitions, commit points and decision logic; row-lock concurrency and real S3
behavior are covered by the opt-in MySQL/MinIO integration tests instead.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import os
import threading
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from botocore.exceptions import ClientError
from PIL import Image
from sqlalchemy import func, select, update
from sqlalchemy.exc import OperationalError

from module_admin.entity.do.user_do import UserDO
from modules.file_assets.application.asset_service import AssetService
from modules.file_assets.application.cleanup_service import CleanupService, object_backoff, unavailable_backoff
from modules.file_assets.application.runtime import FileAssetRuntime, OwnershipState
from modules.file_assets.domain.errors import (
    AssetConflictError,
    AssetInvalidError,
    AssetNotFoundError,
    AssetPermissionDeniedError,
    AssetQuotaExceededError,
    FileAssetError,
    FileAssetsUnavailableError,
)
from modules.file_assets.domain.models import AssetState, OwnerRef, UploadEntry
from modules.file_assets.infrastructure.models import FileAssetDO, FileBindingDO
from modules.file_assets.infrastructure.repository import FileAssetRepository
from modules.file_assets.infrastructure.s3_storage import (
    ObjectMissingError,
    S3ObjectStorage,
    StorageObjectError,
    StorageUnavailableError,
)
from modules.file_assets.tests.conftest import (
    ADMIN,
    EDITOR,
    HOUR,
    NOBODY,
    READER,
    asset_row,
    make_settings,
    shift_asset,
    upload,
)

NOTICE = 'system.notice'
FIELD = 'noticeContent'

pytestmark = pytest.mark.usefixtures('seeded')


async def count_assets(session_factory, **filters) -> int:
    async with session_factory() as session:
        stmt = select(func.count()).select_from(FileAssetDO)
        for key, value in filters.items():
            stmt = stmt.where(getattr(FileAssetDO, key) == value)
        return int(await session.scalar(stmt))


async def bind(session_factory, bindings, actor, owner_id, ids, *, creating=False):
    async with session_factory() as session:
        result = await bindings.replace_field_assets(
            session, actor, OwnerRef.of(NOTICE, owner_id), FIELD, ids, creating=creating
        )
        await session.commit()
        return result


# ------------------------------------------------------------------------ upload ---


async def test_upload_commits_ready_with_server_hash_and_immutable_key(assets, session_factory, storage):
    descriptor = await upload(assets, EDITOR, owner_id='10')
    row = await asset_row(session_factory, descriptor.asset_id)
    assert row.state == AssetState.READY.value and row.uploader_id == 2 and row.intended_owner_id == '10'
    assert row.object_key == f'assets/{row.created_at:%Y}/{row.created_at:%m}/{row.asset_id}'
    assert row.object_key in storage.objects and len(row.sha256) == 64

    assert hashlib.sha256(storage.objects[row.object_key][0]).hexdigest() == row.sha256
    assert row.expires_at - row.uploaded_at == timedelta(hours=24)
    assert descriptor.content_url == f'/file-assets/{row.asset_id}/content'


async def test_precheck_failures_create_no_rows(assets, session_factory):
    with pytest.raises(FileAssetError):
        await upload(assets, EDITOR, filename='x.svg', content_type='image/svg+xml')
    assert await count_assets(session_factory) == 0


async def test_content_failure_after_row_is_failed_and_never_bindable(assets, session_factory, storage):
    with pytest.raises(FileAssetError):
        await upload(assets, EDITOR, data=b'not an image at all', filename='x.png')
    assert await count_assets(session_factory, state='FAILED', last_error_code='VALIDATION_FAILED') == 1
    assert not storage.objects


async def test_storage_failure_marks_failed_and_answers_503(assets, session_factory, storage):
    storage.put_error = StorageUnavailableError('SlowDown', 'put_object')
    with pytest.raises(FileAssetsUnavailableError):
        await upload(assets, EDITOR)
    assert await count_assets(session_factory, state='FAILED', last_error_code='STORAGE_ERROR') == 1


async def test_permission_is_checked_before_any_row(assets, session_factory):
    with pytest.raises(AssetPermissionDeniedError):
        await upload(assets, NOBODY)
    with pytest.raises(AssetNotFoundError):
        await upload(assets, EDITOR, owner_id='999')
    assert await count_assets(session_factory) == 0


async def test_draft_quota_rejects_without_creating_rows(session_factory, storage, registry):
    runtime = FileAssetRuntime(make_settings(file_asset_draft_quota_count=2), storage)
    runtime.ownership.state = OwnershipState.CONFIRMED
    service = AssetService(runtime, registry, session_factory)
    await upload(service, EDITOR)
    await upload(service, EDITOR)
    with pytest.raises(AssetQuotaExceededError) as info:
        await upload(service, EDITOR)
    assert info.value.http_status == 429 and info.value.reason == 'DRAFT_COUNT_EXCEEDED'
    assert await count_assets(session_factory) == 2
    await upload(service, ADMIN)  # quota is per uploader
    await runtime.stop()


async def test_draft_byte_quota_counts_the_incoming_file(session_factory, storage, registry):
    noise = io.BytesIO()
    Image.frombytes('RGB', (500, 500), os.urandom(500 * 500 * 3)).save(noise, 'PNG')  # ~0.7 MiB, incompressible
    runtime = FileAssetRuntime(make_settings(file_asset_draft_quota_bytes=1024 * 1024), storage)
    runtime.ownership.state = OwnershipState.CONFIRMED
    service = AssetService(runtime, registry, session_factory)
    await upload(service, EDITOR, data=noise.getvalue())
    with pytest.raises(AssetQuotaExceededError) as info:
        await upload(service, EDITOR, data=noise.getvalue())  # usage below the cap, but usage + file is above it
    assert info.value.reason == 'DRAFT_BYTES_EXCEEDED'
    assert await count_assets(session_factory) == 1
    await runtime.stop()


async def test_bound_assets_do_not_count_against_draft_quota(session_factory, storage, registry, bindings):
    runtime = FileAssetRuntime(make_settings(file_asset_draft_quota_count=1), storage)
    runtime.ownership.state = OwnershipState.CONFIRMED
    service = AssetService(runtime, registry, session_factory)
    first = await upload(service, EDITOR, owner_id='10')
    await bind(session_factory, bindings, EDITOR, '10', [first.asset_id])
    await upload(service, EDITOR, owner_id='10')
    await runtime.stop()


async def test_cancel_before_ready_commit_marks_failed(assets, session_factory, storage):
    gate = threading.Event()
    storage.before_put = lambda _key: gate.wait(5)
    task = asyncio.create_task(upload(assets, EDITOR))
    for _ in range(100):
        if storage.calls:
            break
        await asyncio.sleep(0.01)
    task.cancel()
    gate.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    for _ in range(100):
        if not assets.runtime.inflight_uploads:
            break
        await asyncio.sleep(0.01)
    assert await count_assets(session_factory, state='FAILED', last_error_code='UPLOAD_CANCELLED') == 1
    assert await count_assets(session_factory, state='READY') == 0
    assert assets.runtime.metrics.in_use['upload'] == 0  # slot released only after the PUT thread ended


async def test_reclaimed_upload_is_not_resurrected_by_late_put(assets, session_factory, storage, cleanup):
    gate = threading.Event()
    started = threading.Event()

    def hold(_key):
        started.set()
        gate.wait(5)

    storage.before_put = hold
    task = asyncio.create_task(upload(assets, EDITOR))
    await asyncio.to_thread(started.wait, 5)
    async with session_factory() as session:
        asset_id = await session.scalar(select(FileAssetDO.asset_id))
    await shift_asset(session_factory, asset_id, upload_deadline=timedelta(minutes=61) + timedelta(seconds=180))
    await cleanup.reclaim()
    assert (await asset_row(session_factory, asset_id)).state == AssetState.DELETING.value
    gate.set()
    with pytest.raises(AssetConflictError) as info:
        await task
    assert info.value.reason == 'UPLOAD_RECLAIMED'
    row = await asset_row(session_factory, asset_id)
    assert row.state == AssetState.DELETING.value and row.sha256 is None
    assert row.object_key in storage.objects  # the late object is left for deletion/sweep, never served


async def test_uploading_rows_inside_recovery_margin_are_kept(assets, session_factory, cleanup, storage):
    gate = threading.Event()
    started = threading.Event()
    storage.before_put = lambda _k: (started.set(), gate.wait(5))
    task = asyncio.create_task(upload(assets, EDITOR))
    await asyncio.to_thread(started.wait, 5)
    async with session_factory() as session:
        asset_id = await session.scalar(select(FileAssetDO.asset_id))
    await shift_asset(session_factory, asset_id, upload_deadline=timedelta(minutes=59) + timedelta(seconds=180))
    await cleanup.reclaim()
    assert (await asset_row(session_factory, asset_id)).state == AssetState.UPLOADING.value
    gate.set()
    await task
    assert (await asset_row(session_factory, asset_id)).state == AssetState.READY.value


async def test_ready_commit_failure_is_resolved_from_committed_state(assets, session_factory, monkeypatch):
    original = FileAssetRepository.mark_ready
    calls = {'n': 0}

    async def flaky(self, *args, **kwargs):
        calls['n'] += 1
        await original(self, *args, **kwargs)
        await self.session.commit()  # the commit happened ...
        raise OperationalError('commit', {}, Exception('lost connection'))  # ... but the answer was lost

    monkeypatch.setattr(FileAssetRepository, 'mark_ready', flaky)
    descriptor = await upload(assets, EDITOR)
    assert (await asset_row(session_factory, descriptor.asset_id)).state == AssetState.READY.value
    assert calls['n'] == 1


async def test_unavailable_storage_or_ownership_blocks_uploads(assets, runtime):
    runtime.ownership.state = OwnershipState.INVALID
    with pytest.raises(FileAssetsUnavailableError) as info:
        runtime.require_available()
    assert info.value.reason == 'OWNERSHIP_INVALID'
    runtime.ownership.state = OwnershipState.UNCONFIRMED
    with pytest.raises(FileAssetsUnavailableError):
        await upload(assets, EDITOR)


async def test_avatar_purpose_is_dedicated_and_self_only(assets, registry):
    with pytest.raises(AssetInvalidError) as info:
        assets.resolve_purpose('user.avatar', entry=UploadEntry.GENERIC)
    assert info.value.reason == 'PURPOSE_ENTRY_MISMATCH'
    with pytest.raises(AssetPermissionDeniedError):
        await upload(assets, EDITOR, purpose='user.avatar', owner_id='3')
    descriptor = await upload(assets, EDITOR, purpose='user.avatar', owner_id='2')
    assert descriptor.media_type == 'image/png'


# ------------------------------------------------------------------------ binding ---


async def test_bind_replace_reorder_release_and_clear(assets, bindings, session_factory):
    a = await upload(assets, EDITOR, owner_id='10')
    b = await upload(assets, EDITOR, owner_id='10')
    assert await bind(session_factory, bindings, EDITOR, '10', [a.asset_id, b.asset_id, a.asset_id]) == [
        a.asset_id,
        b.asset_id,
    ]
    # Another editor may keep and reorder already-bound assets of the same field.
    other = type(EDITOR)(user_id=9, permissions=EDITOR.permissions)
    assert await bind(session_factory, bindings, other, '10', [b.asset_id, a.asset_id]) == [b.asset_id, a.asset_id]
    async with session_factory() as session:
        rows = (await session.scalars(select(FileBindingDO).order_by(FileBindingDO.position))).all()
        assert [row.asset_id for row in rows] == [b.asset_id, a.asset_id]
    await bind(session_factory, bindings, EDITOR, '10', [b.asset_id])
    released = await asset_row(session_factory, a.asset_id)
    assert released.state == AssetState.DELETING.value
    assert released.delete_after - released.updated_at == timedelta(hours=24)
    await bind(session_factory, bindings, EDITOR, '10', [])
    assert (await asset_row(session_factory, b.asset_id)).state == AssetState.DELETING.value


async def test_draft_rules_on_first_bind(assets, bindings, session_factory):
    mine = await upload(assets, EDITOR, owner_id='10')
    create_intent = await upload(assets, EDITOR)
    other_owner = await upload(assets, EDITOR, owner_id='11')
    admins = await upload(assets, ADMIN, owner_id='10')
    with pytest.raises(AssetInvalidError) as info:
        await bind(session_factory, bindings, EDITOR, '10', [admins.asset_id])
    assert info.value.reason == 'ASSET_NOT_AVAILABLE'  # someone else's draft looks like a bad reference
    with pytest.raises(AssetInvalidError) as info:
        await bind(session_factory, bindings, EDITOR, '10', [create_intent.asset_id])
    assert info.value.reason == 'ASSET_CONTEXT_MISMATCH'
    with pytest.raises(AssetInvalidError) as info:
        await bind(session_factory, bindings, EDITOR, '10', [other_owner.asset_id])
    assert info.value.reason == 'ASSET_CONTEXT_MISMATCH'
    await bind(session_factory, bindings, EDITOR, '11', [create_intent.asset_id], creating=True)
    await shift_asset(session_factory, mine.asset_id, expires_at=timedelta(hours=25))
    with pytest.raises(AssetConflictError) as info:
        await bind(session_factory, bindings, EDITOR, '10', [mine.asset_id])
    assert info.value.reason == 'ASSET_EXPIRED'


async def test_cross_owner_and_cross_field_reuse_conflicts(assets, bindings, session_factory):
    a = await upload(assets, EDITOR)
    await bind(session_factory, bindings, EDITOR, '10', [a.asset_id], creating=True)
    with pytest.raises(AssetConflictError) as info:
        await bind(session_factory, bindings, EDITOR, '11', [a.asset_id], creating=True)
    assert info.value.reason == 'ASSET_ALREADY_BOUND'
    avatar = await upload(assets, EDITOR, purpose='user.avatar', owner_id='2')
    with pytest.raises(AssetInvalidError) as info:
        await bind(session_factory, bindings, EDITOR, '10', [avatar.asset_id])
    assert info.value.reason in {'ASSET_PURPOSE_MISMATCH', 'ASSET_CONTEXT_MISMATCH'}


async def test_released_and_failed_assets_never_rebind(assets, bindings, session_factory):
    a = await upload(assets, EDITOR, owner_id='10')
    await bind(session_factory, bindings, EDITOR, '10', [a.asset_id])
    await bind(session_factory, bindings, EDITOR, '10', [])
    with pytest.raises(AssetConflictError) as info:
        await bind(session_factory, bindings, EDITOR, '10', [a.asset_id])
    assert info.value.reason == 'ASSET_NOT_BINDABLE'


async def test_binding_requires_current_write_permission(assets, bindings, session_factory):
    a = await upload(assets, EDITOR, owner_id='10')
    with pytest.raises(AssetPermissionDeniedError):
        await bind(session_factory, bindings, READER, '10', [a.asset_id])


async def test_business_rollback_discards_binding_and_release(assets, bindings, session_factory):
    a = await upload(assets, EDITOR, owner_id='10')
    await bind(session_factory, bindings, EDITOR, '10', [a.asset_id])
    b = await upload(assets, EDITOR, owner_id='10')
    async with session_factory() as session:
        await bindings.replace_field_assets(
            session, EDITOR, OwnerRef.of(NOTICE, '10'), FIELD, [b.asset_id], creating=False
        )
        await session.rollback()  # the business save failed afterwards
    assert (await asset_row(session_factory, a.asset_id)).state == AssetState.READY.value
    assert (await asset_row(session_factory, b.asset_id)).first_bound_at is None
    async with session_factory() as session:
        assert [row.asset_id for row in (await session.scalars(select(FileBindingDO))).all()] == [a.asset_id]


async def test_projection_bounds_each_owner_query(assets, bindings, session_factory, monkeypatch):
    a = await upload(assets, EDITOR, owner_id='10')
    await bind(session_factory, bindings, EDITOR, '10', [a.asset_id])
    sizes = []
    original = FileAssetRepository.bindings_for_owners

    async def recording(self, owner_type, owner_ids, field_key):
        sizes.append(len(list(owner_ids)))
        return await original(self, owner_type, owner_ids, field_key)

    monkeypatch.setattr(FileAssetRepository, 'bindings_for_owners', recording)
    async with session_factory() as session:
        projected = await bindings.project(session, NOTICE, [str(i) for i in range(1, 1201)], FIELD)
    assert sizes == [500, 500, 200]  # an export of 1,200 rows: three bounded queries, not one unbounded IN
    assert [item.asset_id for item in projected['10']] == [a.asset_id]


async def test_release_owner_releases_every_field(assets, bindings, session_factory):
    a = await upload(assets, EDITOR, owner_id='10')
    await bind(session_factory, bindings, EDITOR, '10', [a.asset_id])
    async with session_factory() as session:
        assert await bindings.release_owner(session, OwnerRef.of(NOTICE, 10)) == [a.asset_id]
        await session.commit()
    assert (await asset_row(session_factory, a.asset_id)).state == AssetState.DELETING.value


async def test_too_many_and_malformed_references(bindings, session_factory):
    with pytest.raises(AssetInvalidError) as info:
        await bind(session_factory, bindings, EDITOR, '10', ['not-a-uuid'])
    assert info.value.reason == 'INVALID_ASSET_REFERENCE'

    with pytest.raises(AssetInvalidError) as info:
        await bind(session_factory, bindings, EDITOR, '10', [str(uuid.uuid4()) for _ in range(21)])
    assert info.value.reason == 'TOO_MANY_ASSETS'


# -------------------------------------------------------------------- read access ---


async def test_metadata_visibility_rules(assets, bindings, session_factory):
    draft = await upload(assets, EDITOR, owner_id='10')
    bound = await upload(assets, EDITOR, owner_id='10')
    await bind(session_factory, bindings, EDITOR, '10', [bound.asset_id])
    async with session_factory() as session:
        items, unavailable = await assets.get_metadata(
            session, EDITOR, [draft.asset_id, bound.asset_id, 'x', draft.asset_id]
        )
        assert [i.asset_id for i in items] == [draft.asset_id, bound.asset_id] and unavailable == ['x']
        # Bound notice images follow notice read permission (query-only reader sees them; drafts stay private).
        items, unavailable = await assets.get_metadata(session, READER, [draft.asset_id, bound.asset_id])
        assert [i.asset_id for i in items] == [bound.asset_id] and unavailable == [draft.asset_id]
        items, _ = await assets.get_metadata(session, NOBODY, [bound.asset_id])
        assert items == []
        # The uploader without current permission no longer reads the draft.
        stripped = type(EDITOR)(user_id=2, permissions=frozenset())
        items, _ = await assets.get_metadata(session, stripped, [draft.asset_id])
        assert items == []


async def test_avatar_reads_for_any_signed_in_user_until_owner_is_deleted(assets, bindings, session_factory):
    avatar = await upload(assets, EDITOR, purpose='user.avatar', owner_id='2')
    async with session_factory() as session:
        await bindings.replace_field_assets(
            session, EDITOR, OwnerRef.of('system.user', 2), 'avatar', [avatar.asset_id], creating=False
        )
        await session.commit()
        plan = await assets.authorize_content(session, NOBODY, avatar.asset_id)
        assert plan.inline and plan.media_type == 'image/png'
        await session.execute(update(UserDO).where(UserDO.user_id == 2).values(del_flag='2'))
        await session.commit()
        with pytest.raises(AssetNotFoundError):
            await assets.authorize_content(session, NOBODY, avatar.asset_id)


async def test_released_assets_stop_serving_immediately(assets, bindings, session_factory):
    a = await upload(assets, EDITOR, owner_id='10')
    await bind(session_factory, bindings, EDITOR, '10', [a.asset_id])
    await bind(session_factory, bindings, EDITOR, '10', [])
    async with session_factory() as session:
        with pytest.raises(AssetNotFoundError):
            await assets.authorize_content(session, ADMIN, a.asset_id)


async def test_attachment_disposition_for_file_purposes(assets, session_factory):
    a = await upload(assets, EDITOR, owner_id='10')
    async with session_factory() as session:
        assert (await assets.authorize_content(session, EDITOR, a.asset_id)).inline is True


# ------------------------------------------------------------------------ discard ---


async def test_discard_is_repeatable_and_conflicts_once_bound(assets, bindings, session_factory):
    draft = await upload(assets, EDITOR, owner_id='10')
    for _ in range(2):
        async with session_factory() as session:
            await assets.discard(session, EDITOR, draft.asset_id)
            await session.commit()
    assert (await asset_row(session_factory, draft.asset_id)).state == AssetState.DELETING.value
    bound = await upload(assets, EDITOR, owner_id='10')
    await bind(session_factory, bindings, EDITOR, '10', [bound.asset_id])
    async with session_factory() as session:
        with pytest.raises(AssetConflictError):
            await assets.discard(session, EDITOR, bound.asset_id)
        with pytest.raises(AssetNotFoundError):
            await assets.discard(session, ADMIN, draft.asset_id)  # not the uploader


# ------------------------------------------------------------------------ cleanup ---


async def test_reclaim_expired_drafts_and_failed_rows(assets, session_factory, cleanup):
    draft = await upload(assets, EDITOR)
    with pytest.raises(FileAssetError):
        await upload(assets, EDITOR, data=b'bad', filename='x.png')
    await shift_asset(session_factory, draft.asset_id, expires_at=timedelta(hours=25))
    result = await cleanup.reclaim()
    assert result == {'expiredDrafts': 1, 'abandonedUploads': 0, 'failedToDeleting': 1}
    assert await count_assets(session_factory, state='DELETING') == 2


async def test_deletion_success_marks_deleted_and_is_idempotent(assets, session_factory, cleanup, storage):
    draft = await upload(assets, EDITOR)
    async with session_factory() as session:
        await assets.discard(session, EDITOR, draft.asset_id)
        await session.commit()
    row = await asset_row(session_factory, draft.asset_id)
    del storage.objects[row.object_key]  # already gone: not-found is success
    result = await cleanup.run_deletions()
    assert result['deleted'] == 1
    row = await asset_row(session_factory, draft.asset_id)
    assert row.state == AssetState.DELETED.value and row.delete_next_attempt_at is None and row.deleted_at
    assert (await cleanup.run_deletions())['claimed'] == 0


async def _deleting(assets, session_factory, count=1):
    ids = []
    for _ in range(count):
        draft = await upload(assets, EDITOR)
        async with session_factory() as session:
            await assets.discard(session, EDITOR, draft.asset_id)
            await session.commit()
        ids.append(draft.asset_id)
    return ids


async def test_unavailable_failures_back_off_without_counting_attempts(assets, session_factory, cleanup, storage):
    [asset_id] = await _deleting(assets, session_factory)
    storage.delete_error_all = StorageUnavailableError('InternalError', 'delete_object')
    await cleanup.run_deletions()
    row = await asset_row(session_factory, asset_id)
    assert row.state == AssetState.DELETING.value and row.delete_attempts == 0 and row.delete_failing_since
    assert row.delete_next_attempt_at > row.delete_after and row.last_error_code.startswith('STORAGE_')
    delete_after = row.delete_after
    storage.delete_error_all = None
    assert (await cleanup.run_deletions())['claimed'] == 0  # still backing off
    assert await cleanup.retry_deletes() == 1
    assert (await cleanup.run_deletions())['deleted'] == 1
    row = await asset_row(session_factory, asset_id)
    assert row.delete_after == delete_after and row.delete_failing_since is None


async def test_object_level_failures_count_and_do_not_block_others(assets, session_factory, cleanup, storage):
    bad, good = await _deleting(assets, session_factory, 2)
    bad_key = (await asset_row(session_factory, bad)).object_key
    storage.delete_errors[bad_key] = StorageObjectError('AccessDenied', 'delete_object', status=403)
    result = await cleanup.run_deletions()
    assert result['deleted'] == 1 and result['failed'] == 1
    row = await asset_row(session_factory, bad)
    assert row.delete_attempts == 1 and row.state == AssetState.DELETING.value
    assert (await asset_row(session_factory, good)).state == AssetState.DELETED.value


async def test_three_connection_errors_end_the_round(assets, session_factory, cleanup, storage):
    ids = await _deleting(assets, session_factory, 5)
    storage.delete_error_all = StorageUnavailableError(
        'EndpointConnectionError', 'delete_object', connection_level=True
    )
    result = await cleanup.run_deletions()
    assert result['failed'] == 3
    untouched = [i for i in ids if (await asset_row(session_factory, i)).delete_failing_since is None]
    assert len(untouched) == 2  # lease only; they wait without counting attempts


async def test_single_object_5xx_does_not_end_the_round(assets, session_factory, cleanup, storage):
    ids = await _deleting(assets, session_factory, 3)
    first_key = (await asset_row(session_factory, ids[0])).object_key
    storage.delete_errors[first_key] = StorageUnavailableError('InternalError', 'delete_object')
    result = await cleanup.run_deletions()
    assert result['deleted'] == 2 and result['failed'] == 1


async def test_deletion_skips_while_ownership_unconfirmed(assets, session_factory, cleanup, runtime, storage):
    await _deleting(assets, session_factory)
    runtime.ownership.state = OwnershipState.INVALID
    assert (await cleanup.run_deletions()) == {'skipped': 'invalid'}
    assert not any(call[0] == 'delete' for call in storage.calls)


async def test_ownership_lost_mid_round_stops_before_the_next_delete(
    assets, session_factory, cleanup, runtime, storage
):
    ids = await _deleting(assets, session_factory, 3)
    original_delete = storage.delete

    def delete_then_lose_ownership(key):
        original_delete(key)
        runtime.ownership.state = OwnershipState.INVALID  # e.g. the periodic marker check turned invalid

    storage.delete = delete_then_lose_ownership
    result = await cleanup.run_deletions()
    assert result['deleted'] == 1 and sum(call[0] == 'delete' for call in storage.calls) == 1
    states = [(await asset_row(session_factory, i)).state for i in ids]
    assert states.count(AssetState.DELETED.value) == 1 and states.count(AssetState.DELETING.value) == 2


def test_missing_bucket_is_a_storage_fault_not_a_deleted_object():
    def client_error(code):
        return ClientError({'Error': {'Code': code}, 'ResponseMetadata': {'HTTPStatusCode': 404}}, 'DeleteObject')

    bucket_missing = S3ObjectStorage._classify(client_error('NoSuchBucket'), 'delete_object')
    assert isinstance(bucket_missing, StorageObjectError) and bucket_missing.code == 'NoSuchBucket'
    assert isinstance(S3ObjectStorage._classify(client_error('NoSuchKey'), 'delete_object'), ObjectMissingError)


async def test_missing_bucket_marks_ownership_invalid(runtime, storage):
    storage.marker_error = StorageObjectError('NoSuchBucket', 'get_installation_marker', status=404)
    await runtime.ownership.check_once()
    assert runtime.ownership.state is OwnershipState.INVALID and runtime.ownership.reason == 'BUCKET_MISSING'


async def test_health_reports_a_storage_outage_even_with_confirmed_ownership(runtime, storage):
    runtime.ownership.state = OwnershipState.CONFIRMED
    assert (await runtime.health_probe())['status'] == 'available'
    runtime._storage_probe = None
    storage.marker_error = StorageUnavailableError('EndpointConnectionError', 'get_installation_marker')
    payload = await runtime.health_probe()
    assert payload['status'] == 'unavailable'
    assert payload['storage'] == {'reachable': False, 'reason': 'STORAGE_EndpointConnectionError'}
    assert runtime.ownership.state is OwnershipState.CONFIRMED  # the outage does not rewrite ownership


async def test_bound_deleting_row_is_never_deleted(assets, bindings, session_factory, cleanup, storage):
    a = await upload(assets, EDITOR, owner_id='10')
    await bind(session_factory, bindings, EDITOR, '10', [a.asset_id])

    async with session_factory() as session:
        await session.execute(
            update(FileAssetDO)
            .where(FileAssetDO.asset_id == a.asset_id)
            .values(state='DELETING', delete_after=func.now())
        )
        await session.commit()
    await shift_asset(session_factory, a.asset_id, delete_after=HOUR)
    await cleanup.run_deletions()
    row = await asset_row(session_factory, a.asset_id)
    assert row.state == 'DELETING' and row.last_error_code == 'BINDING_INVARIANT_VIOLATION'
    assert row.object_key in storage.objects


def test_backoff_schedules():
    now = datetime(2026, 1, 1)
    assert unavailable_backoff(now, now) - now == timedelta(minutes=1)
    assert unavailable_backoff(now, now - timedelta(minutes=4)) - now == timedelta(minutes=4)
    assert unavailable_backoff(now, now - timedelta(hours=3)) - now == timedelta(minutes=15)
    assert object_backoff(now, 1) - now == timedelta(minutes=1)
    assert object_backoff(now, 4) - now == timedelta(minutes=8)
    assert object_backoff(now, 20) - now == timedelta(hours=6)


async def test_tombstones_purge_only_old_deleted_rows(assets, session_factory, cleanup):
    old, fresh = await _deleting(assets, session_factory, 2)
    await cleanup.run_deletions()
    await shift_asset(session_factory, old, deleted_at=timedelta(days=31))
    assert await cleanup.purge_tombstones() == 1
    assert await asset_row(session_factory, old) is None
    assert (await asset_row(session_factory, fresh)).state == 'DELETED'


async def test_orphan_sweep_rules(assets, session_factory, cleanup, storage):
    old = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=30)
    failed_key = (await asset_row(session_factory, (await _failed_upload(assets, session_factory, storage)))).object_key
    ready = await upload(assets, EDITOR)
    ready_key = (await asset_row(session_factory, ready.asset_id)).object_key
    prefix = ready_key.rsplit('/', 1)[0] + '/'
    unowned_key = f'{prefix}{uuid.uuid4()}'
    foreign_key = f'{prefix}not-an-asset'
    for key in (failed_key, ready_key, unowned_key, foreign_key):
        storage.objects.setdefault(key, (b'x', old))
        storage.age(key, old)
    report = await cleanup.sweep_orphans([prefix])
    assert report.orphan_deleted == 1 and failed_key not in storage.objects
    assert ready_key in storage.objects and unowned_key in storage.objects and foreign_key in storage.objects
    assert report.unowned == [unowned_key] and report.unexpected_keys == [foreign_key]
    # Fresh objects stay within the grace period.
    fresh_failed = await _failed_upload(assets, session_factory, storage)
    fresh_key = (await asset_row(session_factory, fresh_failed)).object_key
    storage.objects.setdefault(fresh_key, (b'x', datetime.now(UTC).replace(tzinfo=None)))
    assert (await cleanup.sweep_orphans([prefix])).orphan_deleted == 0
    # Explicit unowned deletion needs a prefix and --apply.
    report = await cleanup.sweep_orphans([prefix], include_unowned=True)
    assert unowned_key not in storage.objects and report.orphan_deleted == 1


async def _failed_upload(assets, session_factory, storage):
    """A PUT that succeeded but whose READY never committed (row FAILED, object present)."""

    descriptor = await upload(assets, EDITOR)
    async with session_factory() as session:
        await session.execute(
            update(FileAssetDO).where(FileAssetDO.asset_id == descriptor.asset_id).values(state='FAILED')
        )
        await session.commit()
    return descriptor.asset_id


async def test_sweep_respects_switch_ownership_and_budget(assets, session_factory, storage, runtime):
    class _Redis:
        def __init__(self):
            self.values = {}

        async def get(self, key):
            return self.values.get(key)

        async def set(self, key, value, ex=None):
            self.values[key] = value

        async def delete(self, key):
            self.values.pop(key, None)

    old = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=30)
    keys = []
    for _ in range(3):
        key = (await asset_row(session_factory, await _failed_upload(assets, session_factory, storage))).object_key
        storage.age(key, old)
        keys.append(key)
    prefix = keys[0].rsplit('/', 1)[0] + '/'
    redis = _Redis()
    limited = CleanupService(
        type(runtime)(make_settings(file_asset_orphan_sweep_max_deletes=2), storage), session_factory, redis
    )
    limited.runtime.ownership.state = OwnershipState.CONFIRMED
    first = await limited.sweep_orphans([prefix])
    assert first.truncated and first.orphan_deleted == 2 and redis.values
    second = await limited.sweep_orphans([prefix])
    assert second.orphan_deleted == 1 and not second.truncated and not redis.values
    disabled = CleanupService(
        type(runtime)(make_settings(file_asset_orphan_sweep_enabled=False), storage), session_factory
    )
    assert (await disabled.sweep_orphans(scheduled=True)).skipped_reason == 'DISABLED'
    runtime.ownership.state = OwnershipState.UNCONFIRMED
    assert (
        await CleanupService(runtime, session_factory).sweep_orphans([prefix])
    ).skipped_reason == 'OWNERSHIP_UNCONFIRMED'
    await limited.runtime.stop()
    await disabled.runtime.stop()


async def test_check_consistency_reports_missing_and_unowned(assets, session_factory, cleanup, storage):
    ready = await upload(assets, EDITOR)
    key = (await asset_row(session_factory, ready.asset_id)).object_key
    del storage.objects[key]
    storage.objects[f'assets/2026/01/{uuid.uuid4()}'] = (b'x', datetime(2026, 1, 1))
    report = await cleanup.check_consistency()
    assert report['missingObjects'] == [ready.asset_id] and len(report['unownedObjects']) == 1


# ---------------------------------------------------------------------- ownership ---


async def test_ownership_guard_transitions(runtime, storage):
    guard = runtime.ownership
    guard.state = OwnershipState.UNCONFIRMED
    storage.marker_error = StorageUnavailableError('ReadTimeoutError', 'get_installation_marker')
    assert (await guard.check_once()).outcome == 'transient' and guard.state is OwnershipState.UNCONFIRMED
    storage.marker_error = None
    await guard.check_once()
    assert guard.state is OwnershipState.CONFIRMED
    storage.marker_error = StorageUnavailableError('InternalError', 'get_installation_marker')
    await guard.check_once()
    assert guard.state is OwnershipState.CONFIRMED  # transient errors never change a known conclusion
    storage.marker_error = StorageObjectError('AccessDenied', 'get_installation_marker', status=403)
    await guard.check_once()
    assert guard.state is OwnershipState.INVALID and guard.reason == 'MARKER_ACCESS_DENIED'
    storage.marker_error = None
    storage.installation_id = 'another-environment'
    await guard.check_once()
    assert guard.reason == 'INSTALLATION_MISMATCH'
    storage.installation_id = None
    await guard.check_once()
    assert guard.reason == 'MARKER_MISSING'
    storage.installation_id = 'test-installation'
    await guard.check_once()
    assert guard.state is OwnershipState.CONFIRMED  # recovers without restart


async def test_ownership_startup_tries_three_times(runtime, storage):
    attempts = {'n': 0}

    def failing():
        attempts['n'] += 1
        raise StorageUnavailableError('ConnectTimeoutError', 'get_installation_marker', connection_level=True)

    storage.read_installation_marker = failing
    runtime.ownership.state = OwnershipState.UNCONFIRMED
    await runtime.ownership.startup()
    await runtime.ownership.stop()
    assert attempts['n'] == 3 and runtime.ownership.state is OwnershipState.UNCONFIRMED


async def test_capacity_exhaustion_answers_503(runtime):
    slots = [await runtime.upload_slots.acquire() for _ in range(runtime.upload_slots.capacity)]
    with pytest.raises(FileAssetsUnavailableError) as info:
        await runtime.upload_slots.acquire()
    assert info.value.reason == 'CAPACITY_EXHAUSTED'
    for slot in slots:
        slot.release()
        slot.release()  # idempotent
    assert runtime.metrics.in_use['upload'] == 0
