"""Scheduled reclamation driven only by asset row state (no Outbox, no per-write evidence).

* reclaim: expired drafts and FAILED rows become DELETING; UPLOADING rows only after their deadline
  plus the recovery margin, so normal and slow uploads have finished long before.
* delete: claim due DELETING rows with a lease, delete idempotently, retry forever with persisted
  backoff; storage-unavailable failures never count as attempts.
* sweep: recent month prefixes only; an object is deleted only when its row is FAILED/DELETED with the
  same bucket/key and the object is older than the grace period. Unowned objects and foreign keys are
  only reported.
* tombstones: DELETED rows are purged after the retention period.

Every object deletion first requires the bucket ownership guard to be confirmed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, update

from modules.file_assets.application.runtime import alert
from modules.file_assets.domain.models import META_PREFIX, AssetState, month_prefix, parse_object_key
from modules.file_assets.infrastructure.models import FileAssetDO
from modules.file_assets.infrastructure.repository import FileAssetRepository, db_utc_now
from modules.file_assets.infrastructure.s3_storage import StorageObjectError, StorageUnavailableError
from utils.log_util import logger

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.file_assets.application.runtime import FileAssetRuntime

LEASE = timedelta(minutes=5)
CLAIM_EXECUTION_WINDOW_SECONDS = 180
BINDING_VIOLATION_DEFER = timedelta(hours=1)
UNAVAILABLE_BACKOFF_MIN = timedelta(minutes=1)
UNAVAILABLE_BACKOFF_MAX = timedelta(minutes=15)
OBJECT_BACKOFF_BASE = timedelta(minutes=1)
OBJECT_BACKOFF_MAX = timedelta(hours=6)
CONNECTION_ERRORS_TO_STOP = 3
SWEEP_PAGE = 1000
SWEEP_CURSOR_TTL_SECONDS = 7 * 24 * 3600
TOMBSTONE_BATCH = 1000
ATTEMPT_ALERT_THRESHOLD = 5
SWEEP_TRUNCATION_ALERT_RUNS = 3
FAILING_ALERT_AFTER = timedelta(hours=1)


def unavailable_backoff(now: datetime, failing_since: datetime | None) -> datetime:
    """Approximately doubles with the failure duration: 1, 1, 2, 4, 8 ... capped at 15 minutes."""
    elapsed = now - (failing_since or now)
    return now + min(max(UNAVAILABLE_BACKOFF_MIN, elapsed), UNAVAILABLE_BACKOFF_MAX)


def object_backoff(now: datetime, attempts: int) -> datetime:
    return now + min(OBJECT_BACKOFF_BASE * (2 ** max(attempts - 1, 0)), OBJECT_BACKOFF_MAX)


@dataclass
class SweepReport:
    prefixes: list[str] = field(default_factory=list)
    listed: int = 0
    orphan_found: int = 0
    orphan_deleted: int = 0
    unowned: list[str] = field(default_factory=list)
    unexpected_keys: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)
    delete_failures: int = 0
    truncated: bool = False
    skipped_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'prefixes': self.prefixes,
            'listed': self.listed,
            'orphanFound': self.orphan_found,
            'orphanDeleted': self.orphan_deleted,
            'unownedObjects': self.unowned,
            'unexpectedKeys': self.unexpected_keys,
            'mismatchedObjects': self.mismatched,
            'deleteFailures': self.delete_failures,
            'truncated': self.truncated,
            'skippedReason': self.skipped_reason,
        }


class CleanupService:
    def __init__(
        self,
        runtime: FileAssetRuntime,
        session_factory: Callable[[], AsyncSession],
        redis_client: Any | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.runtime = runtime
        self.settings = runtime.settings
        self.session_factory = session_factory
        self.redis = redis_client
        self.clock = clock

    # ---------------------------------------------------------------- reclaim ----

    async def reclaim(self) -> dict[str, int]:
        batch = self.settings.file_asset_gc_batch_size
        margin = timedelta(minutes=self.settings.file_asset_upload_recovery_margin_minutes)
        async with self.session_factory() as session:
            repo = FileAssetRepository(session)
            now = await db_utc_now(session)
            drafts = await repo.claim_expired_drafts(now, batch)
            for asset in drafts:
                asset.state, asset.delete_after, asset.delete_next_attempt_at = AssetState.DELETING.value, now, None
                asset.updated_at = now
            abandoned = await repo.claim_abandoned_uploads(now - margin, batch)
            for asset in abandoned:
                asset.state = AssetState.FAILED.value
                asset.last_error_code, asset.last_error_at, asset.updated_at = 'UPLOAD_ABANDONED', now, now
            await session.commit()
        async with self.session_factory() as session:
            repo = FileAssetRepository(session)
            now = await db_utc_now(session)
            failed = await repo.claim_failed(batch)
            for asset in failed:
                asset.state, asset.delete_after, asset.delete_next_attempt_at = AssetState.DELETING.value, now, None
                asset.updated_at = now
            await session.commit()
        result = {'expiredDrafts': len(drafts), 'abandonedUploads': len(abandoned), 'failedToDeleting': len(failed)}
        if any(result.values()):
            logger.info('file_assets.reclaim {}', result)
        return result

    # ------------------------------------------------------------------ delete ----

    async def run_deletions(self) -> dict[str, Any]:
        runtime = self.runtime
        if runtime.storage is None or not runtime.ownership.confirmed:
            # Unconfirmed or invalid ownership: skip the round without counting attempts.
            return {'skipped': runtime.ownership.state.value}
        storage = runtime.storage
        claims = await self._claim_deletions()
        claimed_at = self.clock()
        deleted = failed = 0
        connection_errors = 0
        for asset_id, bucket, object_key in claims:
            if self.clock() - claimed_at > CLAIM_EXECUTION_WINDOW_SECONDS:
                break  # remaining rows wait for their lease; no DELETE may outlive the lease
            if not runtime.ownership.confirmed:
                break  # ownership turned invalid mid-round: stop before the next DELETE, rows wait for the lease
            if bucket != storage.bucket:
                await self._record_failure(asset_id, 'BUCKET_MISMATCH', count_attempt=True)
                failed += 1
                continue
            started = self.clock()
            try:
                await runtime.run_maintenance(storage.delete, object_key)
            except StorageUnavailableError as exc:
                failed += 1
                await self._record_failure(asset_id, f'STORAGE_{exc.code}'[:64], count_attempt=False)
                connection_errors = connection_errors + 1 if exc.connection_level else 0
                if connection_errors >= CONNECTION_ERRORS_TO_STOP:
                    break  # storage as a whole is unreachable; single-object 5xx only backs off that row
                continue
            except StorageObjectError as exc:
                failed += 1
                connection_errors = 0
                await self._record_failure(asset_id, f'OBJECT_{exc.code}'[:64], count_attempt=True)
                continue
            connection_errors = 0
            await self._mark_deleted(asset_id)
            deleted += 1
            runtime.metrics.inc('delete_success_total')
            logger.info(
                'file_assets.delete deleted asset={} duration_ms={}', asset_id, int((self.clock() - started) * 1000)
            )
        result = {'claimed': len(claims), 'deleted': deleted, 'failed': failed}
        await self.refresh_gauges()
        return result

    async def _claim_deletions(self) -> list[tuple[str, str, str]]:
        claims: list[tuple[str, str, str]] = []
        async with self.session_factory() as session:
            repo = FileAssetRepository(session)
            now = await db_utc_now(session)
            rows = await repo.claim_due_deletions(now, self.settings.file_asset_gc_batch_size)
            bound = await repo.bindings_of_assets([row.asset_id for row in rows])
            for row in rows:
                if row.asset_id in bound:
                    # "Released means unbound" was violated; never delete, keep it off the batch head.
                    row.delete_next_attempt_at = now + BINDING_VIOLATION_DEFER
                    row.last_error_code, row.last_error_at = 'BINDING_INVARIANT_VIOLATION', now
                    self.runtime.metrics.inc('binding_invariant_violation_total')
                    alert('binding_invariant_violation', 'DELETING asset still bound', asset=row.asset_id)
                    continue
                row.delete_next_attempt_at = now + LEASE  # lease only; delete_after stays unchanged
                claims.append((row.asset_id, row.bucket, row.object_key))
            await session.commit()
        return claims

    async def _mark_deleted(self, asset_id: str) -> None:
        async with self.session_factory() as session:
            now = await db_utc_now(session)
            await FileAssetRepository(session).mark_deleted(asset_id, now=now)
            await session.commit()

    async def _record_failure(self, asset_id: str, error_code: str, *, count_attempt: bool) -> None:
        metrics = self.runtime.metrics
        metrics.inc('delete_retry_total', kind='object' if count_attempt else 'unavailable')
        async with self.session_factory() as session:
            repo = FileAssetRepository(session)
            now = await db_utc_now(session)
            asset = await repo.get(asset_id)
            if asset is None or asset.state != AssetState.DELETING.value:
                return
            failing_since = asset.delete_failing_since or now
            if count_attempt:
                next_attempt = object_backoff(now, int(asset.delete_attempts or 0) + 1)
            else:
                next_attempt = unavailable_backoff(now, failing_since)
            await repo.record_delete_failure(
                asset_id,
                now=now,
                error_code=error_code,
                next_attempt_at=next_attempt,
                count_attempt=count_attempt,
                failing_since=failing_since,
            )
            await session.commit()
        attempts = int(asset.delete_attempts or 0) + (1 if count_attempt else 0)
        logger.warning(
            'file_assets.delete failed asset={} code={} attempts={} next={}',
            asset_id,
            error_code,
            attempts,
            next_attempt,
        )
        if attempts >= ATTEMPT_ALERT_THRESHOLD:
            alert('delete_attempts_exceeded', 'asset deletion keeps failing', asset=asset_id, attempts=attempts)
        if now - failing_since >= FAILING_ALERT_AFTER:
            alert('delete_failing_over_1h', 'asset deletion failing for over an hour', asset=asset_id)

    async def retry_deletes(self, asset_ids: Iterable[str] | None = None) -> int:
        """Operator retry: only failing rows are moved forward; delete_after (grace) is untouched."""
        async with self.session_factory() as session:
            now = await db_utc_now(session)
            stmt = (
                update(FileAssetDO)
                .where(FileAssetDO.state == AssetState.DELETING.value, FileAssetDO.delete_failing_since.is_not(None))
                .values(delete_next_attempt_at=now)
            )
            ids = list(asset_ids or [])
            if ids:
                stmt = stmt.where(FileAssetDO.asset_id.in_(ids))
            count = (await session.execute(stmt)).rowcount
            await session.commit()
        return int(count or 0)

    async def refresh_gauges(self) -> dict[str, object]:
        async with self.session_factory() as session:
            now = await db_utc_now(session)
            gauges = await FileAssetRepository(session).deletion_backlog(now, now - timedelta(minutes=15))
        metrics = self.runtime.metrics
        for name, value in gauges.items():
            metrics.set_gauge(name, float(value))
        if gauges['delete_overdue']:
            alert('delete_backlog', 'due deletions are not being executed', overdue=gauges['delete_overdue'])
        return gauges

    # ------------------------------------------------------------------ sweep ----

    def _cursor_key(self, prefix: str) -> str:
        return f'file_assets:sweep:cursor:{prefix}'

    async def _get_cursor(self, prefix: str) -> str | None:
        if self.redis is None:
            return None
        try:
            value = await self.redis.get(self._cursor_key(prefix))
        except Exception:
            return None  # a lost cursor only restarts the prefix
        return value.decode() if isinstance(value, bytes) else value

    async def _set_cursor(self, prefix: str, value: str | None) -> None:
        if self.redis is None:
            return
        try:
            if value is None:
                await self.redis.delete(self._cursor_key(prefix))
            else:
                await self.redis.set(self._cursor_key(prefix), value, ex=SWEEP_CURSOR_TTL_SECONDS)
        except Exception:
            logger.warning('file_assets.sweep cursor_write_failed prefix={}', prefix)

    async def default_prefixes(self) -> list[str]:
        async with self.session_factory() as session:
            now = await db_utc_now(session)
        previous = now.replace(day=1) - timedelta(days=1)
        return [month_prefix(now), month_prefix(previous)]

    async def sweep_orphans(
        self,
        prefixes: list[str] | None = None,
        *,
        apply: bool = True,
        include_unowned: bool = False,
        use_cursor: bool = True,
        scheduled: bool = False,
    ) -> SweepReport:
        report = SweepReport()
        runtime = self.runtime
        if scheduled and not self.settings.file_asset_orphan_sweep_enabled:
            report.skipped_reason = 'DISABLED'
            return report
        if runtime.storage is None:
            report.skipped_reason = 'NOT_CONFIGURED'
            return report
        if apply and not runtime.ownership.confirmed:
            report.skipped_reason = f'OWNERSHIP_{runtime.ownership.state.value.upper()}'
            return report
        if include_unowned and not (apply and prefixes):
            raise ValueError('--include-unowned requires an explicit prefix and --apply')
        storage = runtime.storage
        report.prefixes = prefixes or await self.default_prefixes()
        deadline = self.clock() + self.settings.file_asset_orphan_sweep_max_seconds
        budget = self.settings.file_asset_orphan_sweep_max_deletes
        async with self.session_factory() as session:
            cutoff = await db_utc_now(session) - timedelta(hours=self.settings.file_asset_orphan_grace_hours)
        for prefix in report.prefixes:
            if prefix.startswith(META_PREFIX):
                continue  # the ownership marker is never listed or swept
            start_after = await self._get_cursor(prefix) if use_cursor else None
            while True:
                page = await runtime.run_maintenance(storage.list, prefix, start_after, SWEEP_PAGE)
                report.listed += len(page.objects)
                last_key = await self._sweep_page(page.objects, cutoff, report, apply, include_unowned, budget)
                budget_left = budget - report.orphan_deleted
                if budget_left <= 0 or self.clock() > deadline:
                    report.truncated = True
                    if use_cursor:
                        await self._set_cursor(prefix, last_key or start_after)
                    break
                if not page.is_truncated:
                    if use_cursor:
                        await self._set_cursor(prefix, None)
                    break
                start_after = page.next_start_after
            if report.truncated or report.skipped_reason:
                break
        await self._track_truncations(report, scheduled=scheduled)
        self._report_sweep(report)
        return report

    async def _track_truncations(self, report: SweepReport, *, scheduled: bool) -> None:
        """Consecutive truncated scheduled runs mean the daily budget cannot keep up."""
        if not scheduled or self.redis is None:
            return
        key = 'file_assets:sweep:truncated_runs'
        try:
            if not report.truncated:
                await self.redis.delete(key)
                return
            runs = int(await self.redis.incr(key))
            await self.redis.expire(key, SWEEP_CURSOR_TTL_SECONDS)
        except Exception:
            logger.warning('file_assets.sweep truncation_counter_failed')
            return
        if runs >= SWEEP_TRUNCATION_ALERT_RUNS:
            alert('orphan_sweep_truncated_repeatedly', 'orphan sweep hit its budget on consecutive runs', runs=runs)

    async def _sweep_page(self, objects, cutoff, report: SweepReport, apply: bool, include_unowned: bool, budget: int):
        storage = self.runtime.storage
        by_id: dict[str, Any] = {}
        last_key = None
        for obj in objects:
            if obj.key.startswith(META_PREFIX):
                continue
            asset_id = parse_object_key(obj.key)
            if asset_id is None:
                report.unexpected_keys.append(obj.key)
                continue
            by_id[asset_id] = obj
        async with self.session_factory() as session:
            rows = await FileAssetRepository(session).assets_for_ids(list(by_id))
        for obj in objects:
            last_key = obj.key
            asset_id = parse_object_key(obj.key)
            if asset_id is None:
                continue
            row = rows.get(asset_id)
            delete = False
            if row is None:
                report.unowned.append(obj.key)
                delete = include_unowned and apply
            elif row.bucket != storage.bucket or row.object_key != obj.key:
                report.mismatched.append(obj.key)
            elif row.state in {AssetState.FAILED.value, AssetState.DELETED.value} and obj.last_modified <= cutoff:
                report.orphan_found += 1
                delete = apply
            if delete and not self.runtime.ownership.confirmed:
                report.skipped_reason = f'OWNERSHIP_{self.runtime.ownership.state.value.upper()}'
                break  # ownership turned invalid mid-sweep: delete nothing more
            if delete and report.orphan_deleted < budget:
                try:
                    await self.runtime.run_maintenance(storage.delete, obj.key)
                except (StorageUnavailableError, StorageObjectError) as exc:
                    report.delete_failures += 1
                    logger.warning('file_assets.sweep delete_failed key={} code={}', obj.key, exc.code)
                    continue
                report.orphan_deleted += 1
                logger.info(
                    'file_assets.sweep deleted key={} asset={} reason={}',
                    obj.key,
                    asset_id,
                    'unowned_explicit' if row is None else f'row_{row.state.lower()}',
                )
            if report.orphan_deleted >= budget:
                break
        return last_key

    def _report_sweep(self, report: SweepReport) -> None:
        metrics = self.runtime.metrics
        metrics.inc('orphan_found_total', report.orphan_found)
        metrics.inc('orphan_deleted_total', report.orphan_deleted)
        metrics.inc('unowned_object_total', len(report.unowned))
        metrics.inc('unexpected_key_total', len(report.unexpected_keys))
        if report.truncated:
            metrics.inc('orphan_sweep_truncated_total')
        if report.unowned:
            alert('unowned_object', 'objects without asset rows found', count=len(report.unowned))
        if report.unexpected_keys:
            alert('unexpected_key', 'objects outside the asset key format found', count=len(report.unexpected_keys))
        logger.info('file_assets.sweep {}', report.to_dict() | {'unownedObjects': len(report.unowned)})

    # -------------------------------------------------------------- tombstones ----

    async def purge_tombstones(self) -> int:
        retention = timedelta(days=self.settings.file_asset_tombstone_retention_days)
        async with self.session_factory() as session:
            repo = FileAssetRepository(session)
            now = await db_utc_now(session)
            ids = await repo.claim_tombstones(now - retention, TOMBSTONE_BATCH)
            purged = await repo.purge_tombstones(ids)
            await session.commit()
        if purged:
            self.runtime.metrics.inc('tombstone_purged_total', purged)
        return purged

    # -------------------------------------------------------------- consistency ----

    async def check_consistency(self, prefix: str | None = None) -> dict[str, Any]:
        """Report-only comparison of bucket and rows (orphans, unowned, foreign keys, missing objects)."""
        storage = self.runtime.storage
        if storage is None:
            return {'skippedReason': 'NOT_CONFIGURED'}
        # The whole bucket by default, so keys outside `assets/` are reported too.
        prefixes = [prefix or '']
        seen: set[str] = set()
        report = SweepReport(prefixes=prefixes)
        async with self.session_factory() as session:
            cutoff = await db_utc_now(session)
        for current in prefixes:
            start_after = None
            while True:
                page = await self.runtime.run_maintenance(storage.list, current, start_after, SWEEP_PAGE)
                fresh = [obj for obj in page.objects if obj.key not in seen and not obj.key.startswith(META_PREFIX)]
                seen.update(obj.key for obj in fresh)
                report.listed += len(fresh)
                await self._sweep_page(fresh, cutoff, report, apply=False, include_unowned=False, budget=10**9)
                if not page.is_truncated:
                    break
                start_after = page.next_start_after
        missing = await self._missing_ready_objects(seen, prefix)
        self.runtime.metrics.set_gauge('missing_object', len(missing))
        if missing:
            alert('missing_object', 'READY assets without stored objects', count=len(missing))
        return report.to_dict() | {'missingObjects': missing, 'orphanFoundIncludesGrace': False}

    async def _missing_ready_objects(self, seen: set[str], prefix: str | None) -> list[str]:
        storage = self.runtime.storage
        missing: list[str] = []
        last_id = ''
        async with self.session_factory() as session:
            while True:
                stmt = (
                    select(FileAssetDO.asset_id, FileAssetDO.object_key)
                    .where(
                        FileAssetDO.state == AssetState.READY.value,
                        FileAssetDO.bucket == storage.bucket,
                        FileAssetDO.asset_id > last_id,
                    )
                    .order_by(FileAssetDO.asset_id)
                    .limit(1000)
                )
                if prefix:
                    stmt = stmt.where(FileAssetDO.object_key.like(f'{prefix}%'))
                rows = (await session.execute(stmt)).all()
                if not rows:
                    break
                missing.extend(asset_id for asset_id, key in rows if key not in seen)
                last_id = rows[-1][0]
        return missing
