"""Opt-in real MySQL rehearsal. Creates only unique ruoyi_remark_* databases."""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import JSON, Column, Integer, MetaData, String, Table, create_engine, inspect, select, text
from sqlalchemy.engine import URL

from alembic import command
from common.remark_document_v1 import plain_to_remark, remark_literal_text
from config.database import Base
from scripts.data_migrations.remark_document_v2 import TARGETS, inspect_database, migrate

pytestmark = pytest.mark.skipif(os.getenv('RUN_REMARK_MYSQL') != '1', reason='explicit isolated MySQL rehearsal only')


def mysql_url(database):
    return URL.create(
        'mysql+pymysql', username='root', password='admin1234', host='127.0.0.1', port=3306, database=database
    )


def verified_backup(engine, restore, tmp_path):
    name = engine.url.database
    # A real backup and restore, not a mock manifest or report-path assertion.
    dump = subprocess.run(
        [
            'docker',
            'exec',
            '-e',
            'MYSQL_PWD=admin1234',
            'ruoyi-mysql-local',
            'mysqldump',
            '-uroot',
            '--skip-comments',
            '--set-gtid-purged=OFF',
            name,
        ],
        check=True,
        capture_output=True,
    ).stdout
    backup = tmp_path / 'backup.sql'
    backup.write_bytes(dump)
    subprocess.run(
        ['docker', 'exec', '-i', '-e', 'MYSQL_PWD=admin1234', 'ruoyi-mysql-local', 'mysql', '-uroot', restore],
        input=dump,
        check=True,
        capture_output=True,
    )
    with engine.connect() as c:
        before = inspect_database(c)
    restored = create_engine(mysql_url(restore))
    with restored.connect() as c:
        check = inspect_database(c)
        assert {k: v['sourceDigest'] for k, v in before['tables'].items()} == {
            k: v['sourceDigest'] for k, v in check['tables'].items()
        }
    restored.dispose()
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(
        json.dumps(
            {
                'databaseIdentifier': before['databaseIdentifier'],
                'restoreVerifiedAt': datetime.now(UTC).isoformat(),
                'backupFile': str(backup),
                'backupSha256': hashlib.sha256(dump).hexdigest(),
                'sourceDigests': {k: v['sourceDigest'] for k, v in before['tables'].items()},
            }
        )
    )
    return manifest


@pytest.fixture
def legacy_database(tmp_path):
    name = 'ruoyi_remark_' + uuid4().hex[:16]
    restore = name + '_restore'
    admin = create_engine(mysql_url('mysql'), isolation_level='AUTOCOMMIT')
    with admin.connect() as c:
        c.execute(text(f'CREATE DATABASE {name} CHARACTER SET utf8mb4'))
        c.execute(text(f'CREATE DATABASE {restore} CHARACTER SET utf8mb4'))
    engine = create_engine(mysql_url(name))
    originals = [None, '', '  中文😀  ', '\n\n', ' a\r\n\r\n尾\r', '<p>x</p>', '{"version":2}', '=1+1', '\t ']
    metadata = MetaData()
    for table, pk in TARGETS.items():
        Table(table, metadata, Column(pk, Integer, primary_key=True), Column('remark', String(500), nullable=True))
    metadata.create_all(engine)
    with engine.begin() as c:
        for table, pk in TARGETS.items():
            c.execute(
                metadata.tables[table].insert(), [{pk: i + 1, 'remark': value} for i, value in enumerate(originals)]
            )
    manifest = verified_backup(engine, restore, tmp_path)
    yield engine, manifest, originals, tmp_path
    engine.dispose()
    with admin.connect() as c:
        c.execute(text(f'DROP DATABASE {restore}'))
        c.execute(text(f'DROP DATABASE {name}'))
    admin.dispose()


@pytest.mark.parametrize('failure', ['added', 'backfilled-batch', 'switched', 'cleaned', None])
def test_real_ddl_resume_and_row_equivalence(legacy_database, failure):
    engine, manifest, originals, tmp = legacy_database
    interrupted = False

    def checkpoint(phase, _table):
        nonlocal interrupted
        if phase == failure and not interrupted:
            interrupted = True
            raise RuntimeError('injected interruption')

    with engine.connect() as c:
        if failure:
            with pytest.raises(RuntimeError, match='injected'):
                migrate(
                    c,
                    backup_manifest=manifest,
                    writers_stopped=True,
                    report_path=tmp / 'interrupted.json',
                    checkpoint=checkpoint,
                )
        report = migrate(c, backup_manifest=manifest, writers_stopped=True, report_path=tmp / 'complete.json')
        assert report['phase'] == 'complete'
        for name in TARGETS:
            assert report['before']['tables'][name]['literalDigest'] == report['after']['tables'][name]['literalDigest']
            assert (
                report['before']['tables'][name]['canonicalDocumentDigest']
                == report['after']['tables'][name]['canonicalDocumentDigest']
            )
        for table, pk in TARGETS.items():
            columns = inspect(c).get_columns(table)
            assert [col['name'] for col in columns] == [pk, 'remark']
            assert isinstance(columns[-1]['type'], JSON)
            assert columns[-1]['comment'] == '备注文档'
            rows = c.execute(select(Table(table, MetaData(), autoload_with=c))).all()
            for row, original in zip(rows, originals, strict=True):
                assert remark_literal_text(row[1]) == (original or '').replace('\r\n', '\n').replace('\r', '\n')
            assert c.execute(text(f'SELECT COUNT(*) FROM {table} WHERE remark IS NULL')).scalar() == 2
            # A later JSON write must survive an idempotent rerun.
            t = Table(table, MetaData(), autoload_with=c)
            t.c.remark.type = JSON(none_as_null=True)
            c.execute(
                t.update()
                .where(t.c[pk] == 1)
                .values(remark=plain_to_remark('new rich text', identity_key=f'{table}:1:remark'))
            )
        c.commit()
        migrate(c, report_path=tmp / 'rerun.json')
        assert inspect_database(c)['tables']['sys_user']['rows'] == len(originals)
        for table, pk in TARGETS.items():
            current = Table(table, MetaData(), autoload_with=c)
            value = c.execute(select(current.c.remark).where(current.c[pk] == 1)).scalar()
            assert remark_literal_text(value) == 'new rich text'


def test_preconditions_and_conflicts_preserve_source(legacy_database):
    engine, manifest, _originals, tmp = legacy_database
    with engine.connect() as c:
        with pytest.raises(ValueError, match='stop old'):
            migrate(c, report_path=tmp / 'no-stop.json')
        with pytest.raises(ValueError, match='requires'):
            migrate(c, writers_stopped=True, report_path=tmp / 'no-backup.json')
        c.execute(text("UPDATE sys_user SET remark='changed' WHERE user_id=1"))
        c.commit()
        with pytest.raises(ValueError, match='source changed'):
            migrate(c, writers_stopped=True, backup_manifest=manifest, report_path=tmp / 'changed.json')
        assert inspect_database(c)['tables']['sys_user']['state'] == 'legacy'


def test_preflight_report_lock_and_backup_binding(legacy_database):
    engine, manifest, _originals, tmp = legacy_database
    bad = json.loads(manifest.read_text())
    bad['databaseIdentifier'] = 'another-database'
    wrong = tmp / 'foreign-manifest.json'
    wrong.write_text(json.dumps(bad))
    with engine.connect() as holder, engine.connect() as connection:
        with pytest.raises(ValueError, match='binding'):
            migrate(connection, backup_manifest=wrong, writers_stopped=True, report_path=tmp / 'binding.json')
        report = json.loads((tmp / 'binding.json').read_text())
        assert report['failedPhase'] == 'preflight'
        bad['databaseIdentifier'] = inspect_database(connection)['databaseIdentifier']
        bad['restoreVerifiedAt'] = 'true'
        wrong.write_text(json.dumps(bad))
        with pytest.raises(ValueError, match='restoration timestamp'):
            migrate(connection, backup_manifest=wrong, writers_stopped=True, report_path=tmp / 'timestamp.json')
        identifier = inspect_database(holder)['databaseIdentifier']
        key = 'remark-v2-' + identifier[:40]
        assert holder.execute(text('SELECT GET_LOCK(:key, 0)'), {'key': key}).scalar() == 1
        try:
            with pytest.raises(ValueError, match='holds the lock'):
                migrate(connection, backup_manifest=manifest, writers_stopped=True, report_path=tmp / 'lock.json')
            assert inspect_database(connection)['tables']['sys_user']['state'] == 'legacy'
        finally:
            holder.execute(text('SELECT RELEASE_LOCK(:key)'), {'key': key})


def test_over_budget_source_and_target_conflict_never_switch(legacy_database):
    engine, manifest, _originals, tmp = legacy_database
    with engine.connect() as connection:
        connection.execute(text('ALTER TABLE sys_user MODIFY remark TEXT NULL'))
        connection.execute(text('UPDATE sys_user SET remark=:value WHERE user_id=3'), {'value': 'x' * 5001})
        connection.commit()
        with pytest.raises(ValueError, match=r'sys_user pk=3 phase=legacy'):
            migrate(connection, backup_manifest=manifest, writers_stopped=True, report_path=tmp / 'budget.json')
        assert connection.execute(text('SELECT CHAR_LENGTH(remark) FROM sys_user WHERE user_id=3')).scalar() == 5001
        connection.execute(text('UPDATE sys_user SET remark=:value WHERE user_id=3'), {'value': '  中文😀  '})
        connection.execute(text('ALTER TABLE sys_user ADD COLUMN remark__json_v2 JSON NULL'))
        connection.execute(text('UPDATE sys_user SET remark__json_v2=JSON_OBJECT() WHERE user_id=1'))
        connection.commit()
        with pytest.raises(ValueError, match=r'sys_user pk=1 phase=backfilling'):
            migrate(connection, backup_manifest=manifest, writers_stopped=True, report_path=tmp / 'conflict.json')
        assert 'remark__text_v1' not in {column['name'] for column in inspect(connection).get_columns('sys_user')}


def test_complete_json_rejects_json_null_and_nonnullable_structure(legacy_database):
    engine, manifest, _originals, tmp = legacy_database
    with engine.connect() as connection:
        migrate(connection, backup_manifest=manifest, writers_stopped=True, report_path=tmp / 'complete.json')
        connection.execute(text("UPDATE sys_user SET remark=CAST('null' AS JSON) WHERE user_id=1"))
        connection.commit()
        with pytest.raises(ValueError, match='JSON null'):
            inspect_database(connection)
        payload = json.dumps(plain_to_remark('replacement', identity_key='sys_user:1:remark'))
        connection.execute(
            text("UPDATE sys_user SET remark=CAST(:value AS JSON) WHERE remark IS NULL OR JSON_TYPE(remark)='NULL'"),
            {'value': payload},
        )
        connection.execute(text('ALTER TABLE sys_user MODIFY remark JSON NOT NULL'))
        connection.commit()
        with pytest.raises(ValueError, match='must be nullable'):
            inspect_database(connection)


def test_formal_revision_requires_context_then_replays_converter(legacy_database, monkeypatch):
    engine, manifest, _originals, tmp = legacy_database
    monkeypatch.setenv('ALEMBIC_DATABASE_URL', engine.url.render_as_string(hide_password=False))
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(128) NOT NULL PRIMARY KEY)'))
        connection.execute(text("INSERT INTO alembic_version VALUES ('20261017_dashboard')"))
    config = Config('alembic.ini')
    config.attributes['remark_migration'] = {'report_path': tmp / 'formal-refused.json'}
    with pytest.raises(ValueError, match='stop old'):
        command.upgrade(config, 'head')
    with engine.connect() as connection:
        assert not inspect(connection).has_table('gen_table_column')
        assert inspect_database(connection)['tables']['sys_user']['state'] == 'legacy'
    config.attributes['remark_migration'] = {
        'backup_manifest': manifest,
        'writers_stopped': True,
        'report_path': tmp / 'formal-success.json',
    }
    command.upgrade(config, 'head')
    with engine.connect() as connection:
        assert all(item['state'] == 'complete' for item in inspect_database(connection)['tables'].values())
        assert inspect(connection).has_table('gen_table_column')
        assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar() == '20261022_remark_v2'
        for table in TARGETS:
            actual = next(column for column in inspect(connection).get_columns(table) if column['name'] == 'remark')
            expected = Base.metadata.tables[table].c.remark
            assert isinstance(actual['type'], JSON)
            assert (actual['nullable'], actual['default'], actual['comment']) == (
                expected.nullable,
                None,
                expected.comment,
            )


def test_unified_cli_is_read_only_then_passes_verified_context(legacy_database):
    engine, manifest, _originals, tmp = legacy_database
    environment = {**os.environ, 'DB_DATABASE': engine.url.database, 'DB_WORKFLOW_MODE': 'development'}
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(128) NOT NULL PRIMARY KEY)'))
        connection.execute(text("INSERT INTO alembic_version VALUES ('20261017_dashboard')"))
        before = inspect_database(connection)
    report_path = tmp / 'cli-preflight.json'
    check = subprocess.run(
        [str(Path.cwd() / 'venv/bin/python'), 'scripts/db.py', 'remark-migration-check', '--report', str(report_path)],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    report = json.loads(report_path.read_text())
    assert report['databaseIdentifier'] == before['databaseIdentifier']
    with engine.connect() as connection:
        after = inspect_database(connection)
        assert before['tables'] == after['tables']
    denied = subprocess.run(
        [str(Path.cwd() / 'venv/bin/python'), 'scripts/db.py', 'deploy', '--revision', 'head'],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert denied.returncode != 0
    assert 'stop old application/import/managed-data writers' in denied.stdout
    with engine.connect() as connection:
        assert not inspect(connection).has_table('gen_table_column')
    allowed = subprocess.run(
        [
            str(Path.cwd() / 'venv/bin/python'),
            'scripts/db.py',
            'deploy',
            '--revision',
            'head',
            '--remark-backup-manifest',
            str(manifest),
            '--remark-writers-stopped',
        ],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    # The repository's old baseline release artifacts are independently invalid;
    # schema conversion must nevertheless finish before their explicit rejection.
    assert 'schema_deploy_result=success' in allowed.stdout, allowed.stdout + allowed.stderr
    assert 'checksum mismatch' in allowed.stdout
    with engine.connect() as connection:
        assert all(item['state'] == 'complete' for item in inspect_database(connection)['tables'].values())


def test_keyset_crosses_500_rows_and_resumes_without_replacing_existing_targets(legacy_database):
    engine, _manifest, _originals, tmp = legacy_database
    with engine.begin() as connection:
        table = Table('sys_user', MetaData(), autoload_with=connection)
        connection.execute(
            table.insert(), [{'user_id': 100 + index * 2, 'remark': f'行 {index} 尾 '} for index in range(505)]
        )
    manifest = verified_backup(engine, engine.url.database + '_restore', tmp)
    interrupted = False

    def checkpoint(phase, table):
        nonlocal interrupted
        if phase == 'backfilled-batch' and table == 'sys_user' and not interrupted:
            interrupted = True
            raise RuntimeError('first 500-row batch persisted')

    with engine.connect() as connection:
        with pytest.raises(RuntimeError, match='500-row batch'):
            migrate(
                connection,
                backup_manifest=manifest,
                writers_stopped=True,
                report_path=tmp / 'batch-interrupted.json',
                checkpoint=checkpoint,
            )
        assert (
            connection.execute(text('SELECT COUNT(*) FROM sys_user WHERE remark__json_v2 IS NOT NULL')).scalar() == 498
        )
        before = inspect_database(connection)['tables']['sys_user']
        assert before['rows'] == 514
        result = migrate(
            connection, backup_manifest=manifest, writers_stopped=True, report_path=tmp / 'multi-page.json'
        )
        after = result['after']['tables']['sys_user']
        assert after['rows'] == 514
        assert after['literalDigest'] == before['literalDigest']
        assert after['canonicalDocumentDigest'] == before['canonicalDocumentDigest']


@pytest.mark.parametrize('state', ['backfilling', 'switched', 'complete'])
def test_resume_corrects_json_comment_left_by_an_older_candidate(legacy_database, state):
    engine, manifest, _originals, tmp = legacy_database
    interruption = {'backfilling': 'added', 'switched': 'switched'}.get(state)

    def checkpoint(phase, table):
        if table == 'sys_user' and phase == interruption:
            raise RuntimeError('older candidate stopped')

    with engine.connect() as connection:
        if interruption:
            with pytest.raises(RuntimeError, match='older candidate'):
                migrate(
                    connection,
                    backup_manifest=manifest,
                    writers_stopped=True,
                    report_path=tmp / 'older.json',
                    checkpoint=checkpoint,
                )
        else:
            migrate(connection, backup_manifest=manifest, writers_stopped=True, report_path=tmp / 'older.json')
        column = 'remark__json_v2' if state == 'backfilling' else 'remark'
        connection.execute(text(f"ALTER TABLE sys_user MODIFY COLUMN {column} JSON NULL COMMENT ''"))
        connection.commit()
        result = migrate(
            connection, backup_manifest=manifest, writers_stopped=True, report_path=tmp / 'comment-resumed.json'
        )
        for table in TARGETS:
            remark = next(column for column in inspect(connection).get_columns(table) if column['name'] == 'remark')
            assert remark['comment'] == '备注文档'
            assert (
                result['before']['tables'][table]['canonicalDocumentDigest']
                == result['after']['tables'][table]['canonicalDocumentDigest']
            )


@pytest.mark.parametrize('fault', ['control', 'budget', 'conflict', 'invalid-document'])
def test_readonly_precheck_persists_safe_failure_report_without_migrating(legacy_database, fault):
    engine, manifest, _originals, tmp = legacy_database
    private = 'PRIVATE_REMARK_MUST_NEVER_APPEAR'
    with engine.connect() as connection:
        if fault == 'control':
            connection.execute(text('UPDATE sys_user SET remark=:value WHERE user_id=3'), {'value': private + '\x00'})
        elif fault == 'budget':
            connection.execute(text('ALTER TABLE sys_user MODIFY remark TEXT NULL'))
            connection.execute(
                text('UPDATE sys_user SET remark=:value WHERE user_id=3'), {'value': private + 'x' * 5001}
            )
        elif fault == 'conflict':
            connection.execute(text('ALTER TABLE sys_user ADD remark__json_v2 JSON NULL'))
            connection.execute(
                text("UPDATE sys_user SET remark__json_v2=JSON_OBJECT('private', :value) WHERE user_id=3"),
                {'value': private},
            )
        else:
            migrate(connection, backup_manifest=manifest, writers_stopped=True, report_path=tmp / 'before-invalid.json')
            connection.execute(
                text("UPDATE sys_user SET remark=JSON_OBJECT('version', 1, 'private', :value) WHERE user_id=3"),
                {'value': private},
            )
        connection.commit()
        before = connection.execute(text('SELECT CAST(remark AS CHAR) FROM sys_user WHERE user_id=3')).scalar()
        columns = [column['name'] for column in inspect(connection).get_columns('sys_user')]
    report = tmp / 'readonly-failed.json'
    result = subprocess.run(
        [str(Path.cwd() / 'venv/bin/python'), 'scripts/db.py', 'remark-migration-check', '--report', str(report)],
        env={**os.environ, 'DB_DATABASE': engine.url.database},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert report.is_file()
    content = json.loads(report.read_text())
    assert content['phase'] == 'failed'
    assert content['table'] == 'sys_user'
    assert content['primaryKey'] == 3
    assert content['failedPhase'] in {'legacy', 'backfilling', 'complete'}
    assert private not in report.read_text() + result.stdout + result.stderr
    with engine.connect() as connection:
        assert connection.execute(text('SELECT CAST(remark AS CHAR) FROM sys_user WHERE user_id=3')).scalar() == before
        assert [column['name'] for column in inspect(connection).get_columns('sys_user')] == columns


def test_after_new_writes_freeze_current_backup_restore_and_forward_repair(legacy_database):
    engine, legacy_manifest, _originals, tmp = legacy_database
    current_restore = engine.url.database + '_current_restore'
    admin = create_engine(mysql_url('mysql'), isolation_level='AUTOCOMMIT')
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE {current_restore} CHARACTER SET utf8mb4'))
    restored = create_engine(mysql_url(current_restore))
    try:
        with engine.connect() as connection:
            migrate(connection, backup_manifest=legacy_manifest, writers_stopped=True, report_path=tmp / 'upgrade.json')
            new_document = plain_to_remark('新写入 😀 保留格式\n第二段 ', identity_key='sys_user:1:remark')
            new_document['body']['content']['content'][0]['content'][0]['marks'] = [{'type': 'bold'}]
            table = Table('sys_user', MetaData(), autoload_with=connection)
            table.c.remark.type = JSON(none_as_null=True)
            connection.execute(table.update().where(table.c.user_id == 1).values(remark=new_document))
            connection.commit()
            frozen = inspect_database(connection)
        # This test owns the only writer and stops it here. Subsequent writes
        # are explicit fault injection/forward repair inside the maintenance window.
        current_dir = tmp / 'current-json-backup'
        current_dir.mkdir(mode=0o700)
        current_manifest = verified_backup(engine, current_restore, current_dir)
        with restored.connect() as connection:
            restored_report = inspect_database(connection)
            table = Table('sys_user', MetaData(), autoload_with=connection)
            recovered = connection.execute(select(table.c.remark).where(table.c.user_id == 1)).scalar()
        assert recovered == new_document
        assert all(item['state'] == 'complete' for item in restored_report['tables'].values())
        with engine.connect() as connection:
            connection.execute(text("UPDATE sys_user SET remark=JSON_OBJECT('version', 1) WHERE user_id=1"))
            connection.commit()
            with pytest.raises(ValueError, match=r'sys_user pk=1 phase=complete'):
                migrate(connection, report_path=tmp / 'post-write-fault.json')
            # Repair only the damaged row from the verified CURRENT JSON backup.
            # The old pre-upgrade snapshot is never restored over new writes.
            table = Table('sys_user', MetaData(), autoload_with=connection)
            table.c.remark.type = JSON(none_as_null=True)
            connection.execute(table.update().where(table.c.user_id == 1).values(remark=recovered))
            connection.commit()
            repaired = migrate(
                connection,
                backup_manifest=current_manifest,
                writers_stopped=True,
                report_path=tmp / 'forward-repaired.json',
            )
            for name in TARGETS:
                assert (
                    repaired['after']['tables'][name]['canonicalDocumentDigest']
                    == frozen['tables'][name]['canonicalDocumentDigest']
                )
                assert repaired['after']['tables'][name]['literalDigest'] == frozen['tables'][name]['literalDigest']
            assert connection.execute(select(table.c.remark).where(table.c.user_id == 1)).scalar() == new_document
            assert all(item['state'] == 'complete' for item in repaired['after']['tables'].values())
        (tmp / 'post-write-recovery.json').write_text(
            json.dumps(
                {
                    'steps': [
                        'new-rich-document-written',
                        'writers-stopped',
                        'current-json-dumped',
                        'current-json-restored-and-compared',
                        'invalid-version-fault-rejected',
                        'targeted-forward-repair-from-current-json-backup',
                        'all-seven-current-digests-verified',
                    ],
                    'currentBackupSha256': json.loads(current_manifest.read_text())['backupSha256'],
                    'before': frozen,
                    'restored': restored_report,
                    'after': repaired['after'],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        restored.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE {current_restore}'))
        admin.dispose()
