"""Conditional single-resource writes and version snapshots share one transaction."""

from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.dashboard_do import DashboardDO, DashboardVersionDO


class DashboardRevisionConflictError(Exception):
    """The caller's expected revision no longer identifies the stored resource."""


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def identity(scope: str, key: str, account_id: int):
        return (
            DashboardDO.scope == scope,
            DashboardDO.scope_key == key,
            DashboardDO.account_id == account_id,
        )

    async def load(self, scope: str, key: str, account_id: int):
        result = await self.db.execute(
            select(DashboardDO).where(*self.identity(scope, key, account_id)).execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def save(self, scope, key, account_id, actor_id, document, expected_revision):
        now = datetime.now(UTC).replace(tzinfo=None)
        revision = (expected_revision or 0) + 1
        try:
            row = await self.load(scope, key, account_id)
            if expected_revision is None and row is None:
                dashboard_id = str(uuid4())
                self.db.add(
                    DashboardDO(
                        dashboard_id=dashboard_id,
                        scope=scope,
                        scope_key=key,
                        account_id=account_id,
                        owner_id=actor_id,
                        document=deepcopy(document),
                        revision=revision,
                        updated_at=now,
                        updated_by=actor_id,
                    )
                )
                await self.db.flush()
            else:
                if row is None:
                    raise DashboardRevisionConflictError
                dashboard_id = row.dashboard_id
                restoring = expected_revision is None
                if restoring and not row.deleted:
                    raise DashboardRevisionConflictError
                # Tombstones retain the counter, preventing stale clients from
                # matching a newly recreated resource's revision (the ABA problem).
                expected = row.revision if restoring else expected_revision
                revision = expected + 1
                result = await self.db.execute(
                    update(DashboardDO)
                    .where(
                        *self.identity(scope, key, account_id),
                        DashboardDO.revision == expected,
                        DashboardDO.deleted == restoring,
                    )
                    .values(
                        document=deepcopy(document),
                        revision=revision,
                        updated_at=now,
                        updated_by=actor_id,
                        deleted=False,
                    )
                    .execution_options(synchronize_session=False)
                )
                if result.rowcount != 1:
                    raise DashboardRevisionConflictError
            self.db.add(
                DashboardVersionDO(
                    dashboard_id=dashboard_id,
                    revision=revision,
                    document=deepcopy(document),
                    saved_at=now,
                    saved_by=actor_id,
                )
            )
            await self.db.flush()
            row = await self.load(scope, key, account_id)
            result = self.snapshot(row)
            await self.db.commit()
            return result
        except (IntegrityError, DashboardRevisionConflictError) as exc:
            await self.db.rollback()
            raise DashboardRevisionConflictError from exc
        except Exception:
            await self.db.rollback()
            raise

    async def remove(self, scope, key, account_id, expected_revision):
        try:
            row = await self.load(scope, key, account_id)
            if row is None:
                raise DashboardRevisionConflictError
            dashboard_id = row.dashboard_id
            # Erase content/history but retain the monotonic identity counter.
            result = await self.db.execute(
                update(DashboardDO)
                .where(
                    *self.identity(scope, key, account_id),
                    DashboardDO.revision == expected_revision,
                    DashboardDO.deleted.is_(False),
                )
                .values(deleted=True, document={}, revision=expected_revision + 1)
                .execution_options(synchronize_session=False)
            )
            if result.rowcount != 1:
                raise DashboardRevisionConflictError
            await self.db.execute(delete(DashboardVersionDO).where(DashboardVersionDO.dashboard_id == dashboard_id))
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    @staticmethod
    def snapshot(row):
        if row is None or row.deleted:
            return None
        return {
            'document': deepcopy(row.document),
            'revision': row.revision,
            'updatedAt': row.updated_at.replace(tzinfo=UTC).isoformat(),
            'ownerId': row.owner_id,
            'scope': row.scope,
            'scopeKey': row.scope_key,
        }
