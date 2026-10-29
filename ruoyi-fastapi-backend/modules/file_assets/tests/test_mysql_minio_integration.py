"""Opt-in real MySQL 8 / MinIO integration (disposable database and bucket per test module).

    RUN_FILE_ASSETS_MYSQL=1 RUN_FILE_ASSETS_S3=1 ./venv/bin/python -m pytest -n 0 --no-cov \
        modules/file_assets/tests/test_mysql_minio_integration.py

MinIO here is the pinned NON-PRODUCTION test fixture (scripts/minio-local.sh); it does not decide TBD-PROD-01.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import threading
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import modules.file_assets.application.cleanup_service as cleanup_module
from config.env import FileAssetConfig
from config.get_db import get_db
from exceptions.handle import handle_exception
from module_admin.entity.do.notice_do import NoticeDO
from module_admin.entity.do.user_do import UserDO
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.file_assets.api.file_asset_controller import fileAssetController
from modules.file_assets.application import composition
from modules.file_assets.application.asset_service import AssetService
from modules.file_assets.application.binding_service import BindingService
from modules.file_assets.application.cleanup_service import CleanupService
from modules.file_assets.application.composition import get_policy_registry
from modules.file_assets.application.runtime import FileAssetRuntime, OwnershipState
from modules.file_assets.domain.errors import AssetConflictError
from modules.file_assets.domain.models import AssetState, OwnerRef
from modules.file_assets.infrastructure.bootstrap import _client, bootstrap_storage
from modules.file_assets.infrastructure.models import FileAssetDO, FileBindingDO
from modules.file_assets.infrastructure.repository import FileAssetRepository, db_utc_now
from modules.file_assets.infrastructure.s3_storage import ObjectMissingError, S3ObjectStorage
from modules.file_assets.tests.conftest import EDITOR, make_settings, png_bytes, upload
from modules.file_assets.tests.fakes import FakeStorage
from modules.identity.ports import get_current_user
from modules.system.application.notice_content import sanitize_notice_html
from scripts.data_migrations import file_assets_v1

MYSQL = os.environ.get('RUN_FILE_ASSETS_MYSQL') == '1'
S3 = os.environ.get('RUN_FILE_ASSETS_S3') == '1'
ADMIN_URL = os.environ.get('FILE_ASSETS_TEST_MYSQL_ADMIN_URL', 'mysql+pymysql://root:admin1234@127.0.0.1:3306/mysql')
requires_mysql = pytest.mark.skipif(
    not MYSQL, reason='set RUN_FILE_ASSETS_MYSQL=1 (disposable database on local MySQL)'
)
requires_s3 = pytest.mark.skipif(not S3, reason='set RUN_FILE_ASSETS_S3=1 (pinned local MinIO fixture)')


def _admin_credentials() -> tuple[str, str, str]:
    key = os.environ.get('FILE_ASSET_S3_ADMIN_ACCESS_KEY', '')
    secret = os.environ.get('FILE_ASSET_S3_ADMIN_SECRET_KEY', '')
    if not (key and secret):
        pytest.skip('FILE_ASSET_S3_ADMIN_* credentials are required (see scripts/minio-local.sh)')
    return FileAssetConfig.file_asset_s3_endpoint or 'http://127.0.0.1:19000', key, secret


# ------------------------------------------------------------------- fixtures ---


@pytest.fixture
def mysql_database():
    if not MYSQL:
        pytest.skip('MySQL integration disabled')
    name = f'ruoyi_file_assets_{uuid.uuid4().hex[:10]}'
    admin = sa.create_engine(ADMIN_URL)
    with admin.begin() as connection:
        connection.execute(sa.text(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'))
    sync = sa.create_engine(ADMIN_URL.rsplit('/', 1)[0] + f'/{name}?charset=utf8mb4')
    for table in (UserDO.__table__, NoticeDO.__table__, FileAssetDO.__table__, FileBindingDO.__table__):
        table.create(sync)
    with sync.begin() as connection:
        connection.execute(
            UserDO.__table__.insert(),
            [
                {'user_id': 2, 'user_name': 'editor', 'nick_name': 'e', 'del_flag': '0'},
                {'user_id': 3, 'user_name': 'other', 'nick_name': 'o', 'del_flag': '0'},
            ],
        )
        connection.execute(
            NoticeDO.__table__.insert(),
            [
                {'notice_id': 10, 'notice_title': 'a', 'notice_type': '1'},
                {'notice_id': 11, 'notice_title': 'b', 'notice_type': '1'},
            ],
        )
    sync.dispose()
    yield name
    _drop_database(admin, name)


def _drop_database(admin, name: str) -> None:
    with admin.begin() as connection:
        # Never wait forever on a metadata lock left by a failed test's open transaction.
        for (process_id,) in connection.execute(
            sa.text('SELECT id FROM information_schema.processlist WHERE db = :db'), {'db': name}
        ):
            try:
                connection.execute(sa.text(f'KILL {int(process_id)}'))
            except sa.exc.OperationalError as error:
                # 1094: the connection exited between the processlist snapshot and KILL.
                if error.orig.args[0] != 1094:
                    raise
        connection.execute(sa.text('SET SESSION lock_wait_timeout = 10'))
        connection.execute(sa.text(f'DROP DATABASE `{name}`'))
    admin.dispose()


@pytest.fixture
async def mysql_sessions(mysql_database):
    url = ADMIN_URL.replace('mysql+pymysql', 'mysql+asyncmy').rsplit('/', 1)[0] + f'/{mysql_database}?charset=utf8mb4'
    engine = create_async_engine(
        url,
        pool_size=10,
        connect_args={'init_command': 'SET SESSION innodb_lock_wait_timeout=5'},
    )
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


@pytest.fixture
async def mysql_stack(mysql_sessions):
    storage = FakeStorage()
    runtime = FileAssetRuntime(make_settings(), storage)
    runtime.ownership.state = OwnershipState.CONFIRMED
    registry = get_policy_registry()
    yield {
        'sessions': mysql_sessions,
        'storage': storage,
        'runtime': runtime,
        'assets': AssetService(runtime, registry, mysql_sessions),
        'bindings': BindingService(registry, delete_grace_hours=24),
        'cleanup': CleanupService(runtime, mysql_sessions),
    }
    await runtime.stop()


# ---------------------------------------------------------------------- MySQL ---


@requires_mysql
async def test_competing_owners_bind_exactly_once(mysql_stack):
    sessions, bindings = mysql_stack['sessions'], mysql_stack['bindings']
    for _ in range(5):
        draft = await upload(mysql_stack['assets'], EDITOR)

        async def attempt(owner_id: str, asset_id: str):
            async with sessions() as session:
                try:
                    await bindings.replace_field_assets(
                        session,
                        EDITOR,
                        OwnerRef.of('system.notice', owner_id),
                        'noticeContent',
                        [asset_id],
                        creating=True,
                    )
                    await session.commit()
                    return 'ok'
                except AssetConflictError as exc:
                    await session.rollback()
                    return exc.reason

        results = sorted(await asyncio.gather(attempt('10', draft.asset_id), attempt('11', draft.asset_id)))
        assert results[1] == 'ok' and results[0] in {'ASSET_NOT_BINDABLE', 'ASSET_ALREADY_BOUND'}
        async with sessions() as session:
            assert (
                await session.scalar(
                    sa.select(sa.func.count())
                    .select_from(FileBindingDO)
                    .where(FileBindingDO.asset_id == draft.asset_id)
                )
                == 1
            )


@requires_mysql
async def test_a_held_asset_row_is_skipped_by_cleanup_and_bound_drafts_never_expire(mysql_stack):
    sessions, bindings, cleanup = mysql_stack['sessions'], mysql_stack['bindings'], mysql_stack['cleanup']
    held = await upload(mysql_stack['assets'], EDITOR, owner_id='10')
    bound = await upload(mysql_stack['assets'], EDITOR, owner_id='10')
    async with sessions() as session:
        await bindings.replace_field_assets(
            session, EDITOR, OwnerRef.of('system.notice', 10), 'noticeContent', [bound.asset_id], creating=False
        )
        await session.commit()
    async with sessions() as session:
        await session.execute(
            sa.update(FileAssetDO).values(expires_at=sa.func.utc_timestamp(6) - sa.text('INTERVAL 1 HOUR'))
        )
        await session.commit()
    async with sessions() as holder:
        await FileAssetRepository(holder).lock_assets([held.asset_id])  # e.g. a binder mid-transaction
        assert (await cleanup.reclaim())['expiredDrafts'] == 0  # SKIP LOCKED: no wait, no claim
        await holder.rollback()
    assert (await cleanup.reclaim())['expiredDrafts'] == 1  # released lock: the expired draft is claimed
    async with sessions() as session:
        assert (await session.get(FileAssetDO, held.asset_id)).state == AssetState.DELETING.value
        assert (await session.get(FileAssetDO, bound.asset_id)).state == AssetState.READY.value


@requires_mysql
async def test_cleanup_claim_first_makes_binder_conflict(mysql_stack):
    sessions, bindings = mysql_stack['sessions'], mysql_stack['bindings']
    draft = await upload(mysql_stack['assets'], EDITOR, owner_id='10')
    async with sessions() as session:
        await session.execute(
            sa.update(FileAssetDO)
            .where(FileAssetDO.asset_id == draft.asset_id)
            .values(expires_at=sa.func.utc_timestamp(6) - sa.text('INTERVAL 1 HOUR'))
        )
        await session.commit()
    claimer = sessions()
    claimed = await FileAssetRepository(claimer).claim_expired_drafts(await db_utc_now(claimer), 10)
    assert [row.asset_id for row in claimed] == [draft.asset_id]

    async def bind_after_wait():
        async with sessions() as session:
            try:
                await bindings.replace_field_assets(
                    session, EDITOR, OwnerRef.of('system.notice', 10), 'noticeContent', [draft.asset_id], creating=False
                )
                await session.commit()
                return 'ok'
            except AssetConflictError as exc:
                return exc.reason

    waiter = asyncio.create_task(bind_after_wait())
    await asyncio.sleep(0.5)
    assert not waiter.done()  # blocked on the claimer's row lock
    claimed[0].state, claimed[0].delete_after = AssetState.DELETING.value, datetime.now(UTC).replace(tzinfo=None)
    await claimer.commit()
    await claimer.close()
    assert await waiter == 'ASSET_NOT_BINDABLE'


@requires_mysql
async def test_two_deletion_workers_claim_disjoint_rows_and_lease_expiry_reclaims(mysql_stack):
    sessions, assets = mysql_stack['sessions'], mysql_stack['assets']
    ids = []
    for _ in range(6):
        draft = await upload(assets, EDITOR)
        async with sessions() as session:
            await assets.discard(session, EDITOR, draft.asset_id)
            await session.commit()
        ids.append(draft.asset_id)
    async with sessions() as session:
        now = await db_utc_now(session) + timedelta(seconds=1)  # lifecycle times come from the DB clock
    async with sessions() as first, sessions() as second:
        a = {row.asset_id for row in await FileAssetRepository(first).claim_due_deletions(now, 3)}
        b = {row.asset_id for row in await FileAssetRepository(second).claim_due_deletions(now, 10)}
        await first.rollback()
        await second.rollback()
    assert len(a) == 3 and len(b) == 3 and not (a & b)

    cleanup = mysql_stack['cleanup']
    claims = await cleanup._claim_deletions()  # a worker that crashes right after claiming
    assert len(claims) == 6
    async with sessions() as session:
        rows = (await session.scalars(sa.select(FileAssetDO).where(FileAssetDO.asset_id.in_(ids)))).all()
        delete_after = {row.asset_id: row.delete_after for row in rows}
        assert all(row.delete_next_attempt_at > row.delete_after for row in rows)
    assert (await cleanup.run_deletions())['claimed'] == 0  # lease still held
    async with sessions() as session:
        await session.execute(
            sa.update(FileAssetDO)
            .where(FileAssetDO.asset_id.in_(ids))
            .values(delete_next_attempt_at=sa.func.utc_timestamp(6) - sa.text('INTERVAL 1 SECOND'))
        )
        await session.commit()
    assert (await cleanup.run_deletions())['deleted'] == 6
    async with sessions() as session:
        rows = (await session.scalars(sa.select(FileAssetDO).where(FileAssetDO.asset_id.in_(ids)))).all()
        assert {row.state for row in rows} == {'DELETED'}
        assert all(row.delete_after == delete_after[row.asset_id] for row in rows)


@requires_mysql
async def test_late_failure_writeback_never_overrides_deleted(mysql_stack):
    sessions, assets, cleanup = mysql_stack['sessions'], mysql_stack['assets'], mysql_stack['cleanup']
    draft = await upload(assets, EDITOR)
    async with sessions() as session:
        await assets.discard(session, EDITOR, draft.asset_id)
        await session.commit()
    await cleanup.run_deletions()
    async with sessions() as session:
        changed = await FileAssetRepository(session).record_delete_failure(
            draft.asset_id,
            now=datetime.now(UTC).replace(tzinfo=None),
            error_code='STORAGE_X',
            next_attempt_at=datetime.now(UTC).replace(tzinfo=None),
            count_attempt=True,
            failing_since=datetime.now(UTC).replace(tzinfo=None),
        )
        await session.commit()
        assert changed is False
        assert (await session.get(FileAssetDO, draft.asset_id)).state == 'DELETED'


@requires_mysql
async def test_business_rollback_on_mysql(mysql_stack):
    sessions, bindings = mysql_stack['sessions'], mysql_stack['bindings']
    draft = await upload(mysql_stack['assets'], EDITOR, owner_id='10')
    async with sessions() as session:
        await bindings.replace_field_assets(
            session, EDITOR, OwnerRef.of('system.notice', 10), 'noticeContent', [draft.asset_id], creating=False
        )
        await session.rollback()
    async with sessions() as session:
        assert await session.scalar(sa.select(sa.func.count()).select_from(FileBindingDO)) == 0
        assert (await session.get(FileAssetDO, draft.asset_id)).first_bound_at is None


@requires_mysql
async def test_notice_content_mediumtext_round_trips_large_multibyte_html(mysql_sessions):
    html = '<p>' + '中文😀' * 30000 + '</p>'  # ~ 293 KiB of UTF-8, well above TEXT's 64 KiB
    cleaned, _ = sanitize_notice_html(html)
    async with mysql_sessions() as session:
        await session.execute(sa.update(NoticeDO).where(NoticeDO.notice_id == 10).values(notice_content=cleaned))
        await session.commit()
        stored = await session.scalar(sa.select(NoticeDO.notice_content).where(NoticeDO.notice_id == 10))
        assert stored == cleaned and len(stored.encode()) > 256 * 1024
        column_type = await session.scalar(
            sa.text(
                'SELECT DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() '
                "AND TABLE_NAME = 'sys_notice' AND COLUMN_NAME = 'notice_content'"
            )
        )
        assert column_type == 'mediumtext'


# ------------------------------------------------------------------------- S3 ---


@pytest.fixture
def s3_bucket():
    if not S3:
        pytest.skip('S3 integration disabled')

    endpoint, key, secret = _admin_credentials()
    name = f'ruoyi-fa-test-{uuid.uuid4().hex[:10]}'
    admin = _client(endpoint, 'us-east-1', 'path', key, secret)
    admin.create_bucket(Bucket=name)
    yield {'name': name, 'endpoint': endpoint, 'key': key, 'secret': secret, 'admin': admin}
    for page in admin.get_paginator('list_objects_v2').paginate(Bucket=name):
        for item in page.get('Contents', []):
            admin.delete_object(Bucket=name, Key=item['Key'])
    admin.delete_bucket(Bucket=name)


def _storage(bucket, *, key=None, secret=None, endpoint=None):
    return S3ObjectStorage(
        endpoint=endpoint or bucket['endpoint'],
        bucket=bucket['name'],
        region='us-east-1',
        addressing_style='path',
        access_key=key or bucket['key'],
        secret_key=secret or bucket['secret'],
        max_pool_connections=4,
    )


@requires_mysql
def test_hard_cutover_upgrade_on_the_legacy_shape_is_idempotent_and_fails_loudly():
    """The single cut-over revision on the pre-file-assets shape: no history is migrated (2026-10-27)."""
    name = f'ruoyi_file_assets_cut_{uuid.uuid4().hex[:8]}'
    admin = sa.create_engine(ADMIN_URL)
    with admin.begin() as connection:
        connection.execute(sa.text(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'))
    engine = sa.create_engine(ADMIN_URL.rsplit('/', 1)[0] + f'/{name}?charset=utf8mb4')
    html = '<p>中文公告 <img src="/api/profile/upload/2026/02/10/a.png"></p>'
    try:
        with engine.begin() as connection:
            for ddl in (
                'CREATE TABLE sys_user (user_id BIGINT PRIMARY KEY, user_name VARCHAR(30), '
                "avatar VARCHAR(100) DEFAULT '')",
                'CREATE TABLE sys_notice (notice_id INT PRIMARY KEY, notice_title VARCHAR(50), notice_content LONGBLOB)',
                'CREATE TABLE gen_table (table_id BIGINT PRIMARY KEY, table_name VARCHAR(200))',
                'CREATE TABLE sys_job (job_id BIGINT AUTO_INCREMENT PRIMARY KEY, job_name VARCHAR(64), '
                'job_group VARCHAR(64), job_executor VARCHAR(64), invoke_target VARCHAR(500), job_args VARCHAR(255), '
                'job_kwargs VARCHAR(255), cron_expression VARCHAR(255), misfire_policy VARCHAR(20), concurrent CHAR(1), '
                'status CHAR(1), remark VARCHAR(500), create_by VARCHAR(64), create_time DATETIME)',
            ):
                connection.execute(sa.text(ddl))
            connection.execute(sa.text("INSERT INTO sys_user VALUES (1, 'admin', '/profile/avatar/2026/10/19/a.png')"))
            connection.execute(
                sa.text('INSERT INTO sys_notice VALUES (10, :t, :c), (11, :t, :bad)'),
                {'t': 'n', 'c': html.encode(), 'bad': b'\xff\xfe not utf-8'},
            )

        with engine.connect() as connection:
            # A non-strict session must not decide correctness: the pre-scan stops before any destructive step.
            connection.execute(sa.text("SET SESSION sql_mode = ''"))
            with pytest.raises(file_assets_v1.NoticeContentNotUtf8Error, match=r'\[11\]'):
                file_assets_v1.upgrade(connection)
        assert 'avatar' in {column['name'] for column in sa.inspect(engine).get_columns('sys_user')}
        with engine.begin() as connection:
            connection.execute(sa.text('DELETE FROM sys_notice WHERE notice_id = 11'))

        with engine.connect() as connection:
            first = file_assets_v1.upgrade(connection)
        # The failed attempt stopped at the conversion, before dropping the avatar column or seeding jobs.
        assert first['droppedAvatar'] is True and first['noticeConverted'] is True
        assert first['jobsSeeded'] == len(file_assets_v1.MAINTENANCE_JOBS)
        with engine.connect() as connection:
            second = file_assets_v1.upgrade(connection)
        assert second == {
            'createdTables': [],
            'genAssetFieldsColumn': False,
            'droppedAvatar': False,
            'noticeConverted': False,
            'jobsSeeded': 0,
        }

        inspector = sa.inspect(engine)
        assert {'sys_file_asset', 'sys_file_binding'} <= set(inspector.get_table_names())
        assert 'avatar' not in {column['name'] for column in inspector.get_columns('sys_user')}
        assert 'asset_fields' in {column['name'] for column in inspector.get_columns('gen_table')}
        with engine.connect() as connection:
            data_type = connection.execute(
                sa.text(
                    'SELECT DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = :db '
                    "AND TABLE_NAME = 'sys_notice' AND COLUMN_NAME = 'notice_content'"
                ),
                {'db': name},
            ).scalar()
            content = connection.execute(sa.text('SELECT notice_content FROM sys_notice WHERE notice_id = 10')).scalar()
            targets = set(connection.execute(sa.text('SELECT invoke_target FROM sys_job')).scalars())
        assert data_type == 'mediumtext' and content == html
        assert targets == {target for _, target, _, _ in file_assets_v1.MAINTENANCE_JOBS}
    finally:
        engine.dispose()
        _drop_database(admin, name)


@requires_s3
def test_s3_put_stream_list_delete_semantics(s3_bucket, tmp_path):
    storage = _storage(s3_bucket)
    data = os.urandom(200 * 1024)
    source = tmp_path / 'blob'
    source.write_bytes(data)
    keys = [f'assets/2026/10/{uuid.uuid4()}' for _ in range(3)]
    for key in keys:
        storage.put(key, source, len(data), 'application/octet-stream')
    stream = storage.open(keys[0])
    chunks = []
    while chunk := stream.read_chunk():
        chunks.append(chunk)
    stream.close()
    assert b''.join(chunks) == data and stream.content_length == len(data) and len(chunks) > 1
    first = storage.list('assets/2026/10/', None, 2)
    assert first.is_truncated and len(first.objects) == 2 and first.objects[0].last_modified.tzinfo is None
    rest = storage.list('assets/2026/10/', first.next_start_after, 2)
    assert not rest.is_truncated and {o.key for o in first.objects + rest.objects} == set(keys)
    storage.delete(keys[0])
    storage.delete(keys[0])  # deleting a missing key is idempotent success
    with pytest.raises(ObjectMissingError):
        storage.open(keys[0])
    assert storage.list('_meta/', None, 10).objects == ()


@requires_s3
async def test_s3_ownership_states(s3_bucket):
    storage = _storage(s3_bucket)
    runtime = FileAssetRuntime(
        make_settings(file_asset_installation_id='it-a', file_asset_s3_bucket=s3_bucket['name']), storage
    )
    try:
        assert (await runtime.ownership.check_once()).reason == 'MARKER_MISSING'
        storage.write_installation_marker('it-a')
        await runtime.ownership.check_once()
        assert runtime.ownership.state is OwnershipState.CONFIRMED
        storage.write_installation_marker('it-b')
        await runtime.ownership.check_once()
        assert runtime.ownership.reason == 'INSTALLATION_MISMATCH'
    finally:
        await runtime.stop()

    app_key = FileAssetConfig.file_asset_s3_access_key.get_secret_value()
    if app_key:
        # The app account of another bucket is denied: 403 is a configuration error, not a transient one.
        denied = FileAssetRuntime(
            make_settings(file_asset_installation_id='it-a'),
            _storage(s3_bucket, key=app_key, secret=FileAssetConfig.file_asset_s3_secret_key.get_secret_value()),
        )
        try:
            assert (await denied.ownership.check_once()).reason == 'MARKER_ACCESS_DENIED'
        finally:
            await denied.stop()
    unreachable = FileAssetRuntime(make_settings(), _storage(s3_bucket, endpoint='http://127.0.0.1:19999'))
    try:
        result = await unreachable.ownership.check_once()
        assert result.outcome == 'transient' and unreachable.ownership.state is OwnershipState.UNCONFIRMED
    finally:
        await unreachable.stop()


@requires_s3
def test_bootstrap_refuses_to_take_over_without_confirmation(s3_bucket):
    common = {
        'endpoint': s3_bucket['endpoint'],
        'region': 'us-east-1',
        'addressing_style': 'path',
        'bucket': s3_bucket['name'],
        'admin_access_key': s3_bucket['key'],
        'admin_secret_key': s3_bucket['secret'],
    }
    assert bootstrap_storage(installation_id='env-a', **common).ok
    refused = bootstrap_storage(installation_id='env-b', **common)
    assert not refused.ok and 'refusing to overwrite' in refused.findings[0]
    assert not bootstrap_storage(installation_id='env-b', take_over=True, confirm_installation='wrong', **common).ok
    assert bootstrap_storage(installation_id='env-b', take_over=True, confirm_installation='env-a', **common).ok
    assert _storage(s3_bucket).read_installation_marker().installation_id == 'env-b'


@requires_mysql
@requires_s3
async def test_late_write_after_reclamation_is_swept_by_the_orphan_sweep(mysql_sessions, s3_bucket, monkeypatch):
    real = _storage(s3_bucket)
    real.write_installation_marker('test-installation')
    gate, started = threading.Event(), threading.Event()

    class Delayed:
        bucket = real.bucket

        def __getattr__(self, name):
            return getattr(real, name)

        def put(self, *args):
            started.set()
            gate.wait(10)
            return real.put(*args)

    runtime = FileAssetRuntime(make_settings(file_asset_s3_bucket=real.bucket), Delayed())
    await runtime.ownership.check_once()
    assert runtime.ownership.confirmed
    assets = AssetService(runtime, get_policy_registry(), mysql_sessions)
    cleanup = CleanupService(runtime, mysql_sessions)
    task = asyncio.create_task(upload(assets, EDITOR, data=png_bytes()))
    await asyncio.to_thread(started.wait, 10)
    async with mysql_sessions() as session:
        asset_id = await session.scalar(sa.select(FileAssetDO.asset_id))
        await session.execute(
            sa.update(FileAssetDO)
            .where(FileAssetDO.asset_id == asset_id)
            .values(upload_deadline=sa.func.utc_timestamp(6) - sa.text('INTERVAL 2 HOUR'))
        )
        await session.commit()
    await cleanup.reclaim()
    await cleanup.run_deletions()  # nothing stored yet: DELETE is an idempotent no-op, row becomes DELETED
    gate.set()
    with pytest.raises(AssetConflictError):
        await task  # the late PUT completed but READY was refused
    async with mysql_sessions() as session:
        row = await session.get(FileAssetDO, asset_id)
    assert row.state == 'DELETED'
    stream = real.open(row.object_key)  # the late object exists in the private bucket
    stream.close()
    prefix = row.object_key.rsplit('/', 1)[0] + '/'
    assert (await cleanup.sweep_orphans([prefix], use_cursor=False)).orphan_deleted == 0  # inside grace

    original = cleanup_module.db_utc_now

    async def future(session):
        return (await original(session)) + timedelta(hours=25)

    monkeypatch.setattr(cleanup_module, 'db_utc_now', future)
    report = await cleanup.sweep_orphans([prefix], use_cursor=False)
    assert report.orphan_deleted == 1

    with pytest.raises(ObjectMissingError):
        real.open(row.object_key)
    consistency = await cleanup.check_consistency(prefix)
    assert consistency['missingObjects'] == [] and consistency['unownedObjects'] == []
    await runtime.stop()


@requires_mysql
@requires_s3
async def test_http_chain_against_minio_streams_and_revalidates(mysql_sessions, s3_bucket):
    real = _storage(s3_bucket)
    real.write_installation_marker('test-installation')
    runtime = FileAssetRuntime(make_settings(file_asset_s3_bucket=real.bucket), real)
    await runtime.ownership.check_once()
    assets = AssetService(runtime, get_policy_registry(), mysql_sessions)
    big = png_bytes((1500, 1500), 'purple')
    descriptor = await upload(assets, EDITOR, data=big, owner_id='10')
    async with mysql_sessions() as session:
        plan = await assets.authorize_content(session, EDITOR, descriptor.asset_id)
    stream = await runtime.run_download(real.open, plan.object_key)

    digest = hashlib.sha256()
    while chunk := await runtime.run_download(stream.read_chunk):
        digest.update(chunk)
    stream.close()
    assert digest.hexdigest() == plan.sha256 and plan.size == descriptor.size
    await runtime.stop()


@requires_mysql
@requires_s3
async def test_schema_attachment_http_contract_with_real_mysql_and_minio(mysql_sessions, s3_bucket):
    """Exercise the exact generic-upload DTO consumed by the schema business adapter."""
    real = _storage(s3_bucket)
    real.write_installation_marker('test-installation')
    runtime = FileAssetRuntime(make_settings(file_asset_s3_bucket=real.bucket), real)
    await runtime.ownership.check_once()
    previous = composition._services
    composition.configure_file_assets(mysql_sessions, runtime=runtime)
    app = FastAPI()
    handle_exception(app)
    app.include_router(fileAssetController)
    principal = {'user_id': 2, 'permissions': ['system:notice:add', 'system:notice:edit', 'system:notice:list']}

    async def actor():
        return CurrentUserModel(
            permissions=principal['permissions'],
            roles=[],
            user=UserInfoModel(userId=principal['user_id'], userName='schema', nickName='Schema'),
        )

    async def db():
        async with mysql_sessions() as session:
            yield session
            if session.in_transaction():
                await session.commit()

    app.dependency_overrides[get_current_user] = actor
    app.dependency_overrides[get_db] = db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://schema.test') as client:
            response = await client.post(
                '/file-assets/uploads',
                data={'purpose': 'notice.image', 'ownerId': '10'},
                files={'file': ('schema.png', png_bytes(), 'image/png')},
            )
            assert response.status_code == 200, response.text
            asset = response.json()
            assert set(asset) == {'assetId', 'name', 'mediaType', 'size', 'contentUrl'}
            assert asset['contentUrl'] == f'/file-assets/{asset["assetId"]}/content'
            content = await client.get(asset['contentUrl'])
            assert content.status_code == 200 and content.content.startswith(b'\x89PNG')
            assert (
                await client.get(asset['contentUrl'], headers={'If-None-Match': content.headers['etag']})
            ).status_code == 304
            principal.update(user_id=3, permissions=[])
            hidden = await client.get(asset['contentUrl'])
            assert hidden.status_code == 404
            denied = await client.post(
                '/file-assets/uploads',
                data={'purpose': 'notice.image', 'ownerId': '10'},
                files={'file': ('denied.png', png_bytes(), 'image/png')},
            )
            assert denied.status_code == 403
            principal.update(user_id=2, permissions=['system:notice:edit', 'system:notice:list'])
            batch = await client.post('/file-assets/metadata:batch', json={'assetIds': [asset['assetId']]})
            assert batch.status_code == 200 and batch.json()['items'] == [asset]
            # Reference removal and server draft deletion are separate operations.
            removed = await client.delete(f'/file-assets/{asset["assetId"]}')
            assert removed.status_code == 204
            assert (await client.get(asset['contentUrl'])).status_code == 404
    finally:
        composition._services = previous
        await runtime.stop()
