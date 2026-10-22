"""Frozen, restartable conversion of the seven remark columns; SQLAlchemy Core only.

No current ORM/DTO imports. DDL is deliberately staged because MySQL commits it.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import JSON, MetaData, String, Table, create_engine, inspect, select, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import StatementError

from common.remark_document_v1 import plain_to_remark, remark_literal_text, validate_remark

TARGETS = {
    'sys_user': 'user_id',
    'sys_role': 'role_id',
    'sys_post': 'post_id',
    'sys_dict_type': 'dict_id',
    'sys_dict_data': 'dict_code',
    'sys_config': 'config_id',
    'gen_table': 'table_id',
}
TEMP, OLD = 'remark__json_v2', 'remark__text_v1'
VERSION = 'remark-a-v1/document-v2/1'


def _commit(connection):
    # Alembic's public autocommit block owns its proxy transaction. In that
    # mode statements are already durable; closing the proxy would break it.
    if connection.get_execution_options().get('isolation_level') != 'AUTOCOMMIT':
        connection.commit()


@contextmanager
def _atomic_statements(connection):
    """Keep batches and PG's two renames atomic inside Alembic autocommit."""
    autocommit = connection.get_execution_options().get('isolation_level') == 'AUTOCOMMIT'
    if autocommit:
        connection.execute(text('BEGIN'))
    try:
        yield
    except Exception:
        if autocommit:
            connection.execute(text('ROLLBACK'))
        else:
            connection.rollback()
        raise
    else:
        if autocommit:
            connection.execute(text('COMMIT'))
        else:
            connection.commit()


def _switch_columns(connection, name):
    table = connection.dialect.identifier_preparer.quote(name)
    if connection.dialect.name == 'mysql':
        connection.execute(text(f'ALTER TABLE {table} RENAME COLUMN remark TO {OLD}, RENAME COLUMN {TEMP} TO remark'))
        _commit(connection)
    else:
        # PostgreSQL can transact these two DDL statements; no intermediate
        # state without a main remark column may survive an interruption.
        with _atomic_statements(connection):
            connection.execute(text(f'ALTER TABLE {table} RENAME COLUMN remark TO {OLD}'))
            connection.execute(text(f'ALTER TABLE {table} RENAME COLUMN {TEMP} TO remark'))


def classify_columns(columns):
    if not columns:
        return 'missing'
    types = {c['name']: c['type'] for c in columns}
    main = types.get('remark')
    if isinstance(main, JSON) and TEMP not in types:
        if OLD not in types:
            return 'complete'
        if isinstance(types[OLD], String):
            return 'switched'
    if isinstance(main, String) and OLD not in types:
        if TEMP not in types:
            return 'legacy'
        if isinstance(types[TEMP], JSON):
            return 'backfilling'
    raise ValueError('remark-migration: conflicting column state; inspect backup and physical columns')


def database_identifier(connection):
    u = connection.engine.url
    # Include actual server identity; never include credentials in reports.
    server = connection.execute(
        text('SELECT @@server_uuid' if connection.dialect.name == 'mysql' else 'SELECT inet_server_addr()::text')
    ).scalar()
    value = [connection.dialect.name, u.host, u.port, u.database, str(server)]
    return hashlib.sha256(json.dumps(value).encode()).hexdigest()


def _rows(connection, table, pk, source, target=None):
    last = None
    columns = [table.c[pk], table.c[source]] + ([table.c[target]] if target else [])
    while True:
        stmt = select(*columns).order_by(table.c[pk]).limit(500)
        if last is not None:
            stmt = stmt.where(table.c[pk] > last)
        batch = connection.execute(stmt).all()
        if not batch:
            return
        yield batch
        last = batch[-1][0]


def _hash_update(digest, value):
    digest.update(json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode('utf-8'))
    digest.update(b'\n')


def _verify_columns(name, pk, columns, state):
    if columns and not any(column['name'] == pk for column in columns):
        raise ValueError(f'remark-migration: {name} phase=preflight: primary key {pk} missing')
    target = TEMP if state == 'backfilling' else 'remark' if state in {'complete', 'switched'} else None
    if target:
        column = next(column for column in columns if column['name'] == target)
        if not column['nullable']:
            raise ValueError(f'remark-migration: {name} phase=preflight: remark JSON must be nullable')
        if column.get('default') is not None:
            raise ValueError(f'remark-migration: {name} phase=preflight: remark JSON default must be SQL NULL')


def inspect_database(connection):
    if connection.dialect.name not in {'mysql', 'postgresql'}:
        raise ValueError('remark-migration: unsupported dialect')
    report = {
        'codec': VERSION,
        'databaseIdentifier': database_identifier(connection),
        'dialect': connection.dialect.name,
        'at': datetime.now(UTC).isoformat(),
        'tables': {},
    }
    inspector = inspect(connection)
    for name, pk in TARGETS.items():
        columns = inspector.get_columns(name) if inspector.has_table(name) else []
        try:
            state = classify_columns(columns)
        except ValueError:
            raise ValueError(
                f'remark-migration: {name} phase=preflight: conflicting physical columns; inspect backup'
            ) from None
        _verify_columns(name, pk, columns, state)
        item = {'state': state, 'rows': 0, 'sqlNulls': 0, 'emptyStrings': 0, 'maxCharacters': 0}
        item['columns'] = [
            {
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': str(column['default']) if column.get('default') is not None else None,
                'comment': column.get('comment'),
            }
            for column in columns
            if column['name'] in {'remark', TEMP, OLD}
        ]
        report['tables'][name] = item
        if state == 'missing':
            continue
        table = Table(name, MetaData(), autoload_with=connection)
        source = OLD if state == 'switched' else 'remark'
        target = 'remark' if state == 'switched' else TEMP if state == 'backfilling' else None
        digest = hashlib.sha256()
        literal_digest = hashlib.sha256()
        document_digest = hashlib.sha256()
        for batch in _rows(connection, table, pk, source, target):
            for row in batch:
                key, raw = row[0], row[1]
                try:
                    expected = (
                        validate_remark(raw)
                        if state == 'complete'
                        else plain_to_remark(raw, identity_key=f'{name}:{key}:remark')
                    )
                    if target and row[2] is not None and row[2] != expected:
                        raise ValueError('existing target differs from deterministic conversion')
                    if state == 'switched' and row[2] != expected:
                        raise ValueError('switched target differs from source')
                    normalized_text = (
                        (raw or '').replace('\r\n', '\n').replace('\r', '\n')
                        if state != 'complete'
                        else remark_literal_text(expected)
                    )
                    if remark_literal_text(expected) != normalized_text:
                        raise ValueError('literal equivalence failed')
                except (ValueError, TypeError) as error:
                    raise ValueError(f'remark-migration: {name} pk={key} phase={state}: {error}') from None
                item['rows'] += 1
                item['sqlNulls'] += raw is None
                item['emptyStrings'] += raw == ''
                item['maxCharacters'] = max(item['maxCharacters'], len(normalized_text))
                _hash_update(digest, [key, raw])
                _hash_update(literal_digest, [key, normalized_text])
                _hash_update(document_digest, [key, expected])
        item['sourceDigest'] = digest.hexdigest()
        item['literalDigest'] = literal_digest.hexdigest()
        item['canonicalDocumentDigest'] = document_digest.hexdigest()
        if state in {'complete', 'switched'}:
            expr = (
                "JSON_TYPE(remark) = 'NULL'" if connection.dialect.name == 'mysql' else "json_typeof(remark) = 'null'"
            )
            if connection.execute(text(f'SELECT COUNT(*) FROM {name} WHERE {expr}')).scalar():
                raise ValueError(f'remark-migration: {name} contains JSON null; SQL NULL required')
    report['schemaFingerprint'] = hashlib.sha256(
        json.dumps({n: [i['state'], i['columns']] for n, i in report['tables'].items()}, sort_keys=True).encode()
    ).hexdigest()
    return report


def _error_message(error):
    if isinstance(error, StatementError):
        original = error.orig
        code = getattr(original, 'pgcode', None)
        arguments = getattr(original, 'args', ())
        if code is None and arguments and isinstance(arguments[0], int):
            code = arguments[0]
        return f'database operation failed: {type(error).__name__} code={code or "unknown"}; use private database diagnostics'
    return str(error)


def _save(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def inspect_database_to_report(connection, report_path):
    """Read-only preflight always writes a safe success or failure report."""
    context = {'codec': VERSION, 'at': datetime.now(UTC).isoformat(), 'dialect': connection.dialect.name}
    try:
        context['databaseIdentifier'] = database_identifier(connection)
        report = inspect_database(connection)
    except Exception as error:
        message = _error_message(error)
        location = re.search(r'remark-migration: (\w+)(?: pk=([^ ]+))? phase=([^:]+):', message)
        context.update(phase='failed', failedPhase=location[3] if location else 'preflight', error=message)
        if location and location[1] in TARGETS:
            context['table'] = location[1]
            context['primaryKey'] = int(location[2]) if location[2] and location[2].isdigit() else location[2]
        _save(report_path, context)
        raise ValueError(
            f'remark-migration: read-only preflight failed; see phase report {report_path}: {message}'
        ) from None
    _save(report_path, report)
    return report


def _ensure_json_comment(connection, name, column):
    quote = connection.dialect.identifier_preparer.quote
    if connection.dialect.name == 'mysql':
        connection.execute(
            text(f"ALTER TABLE {quote(name)} MODIFY COLUMN {quote(column)} JSON NULL COMMENT '备注文档'")
        )
    else:
        connection.execute(text(f"COMMENT ON COLUMN {quote(name)}.{quote(column)} IS '备注文档'"))
    _commit(connection)


def _check_backup(manifest_path, before):
    if not manifest_path:
        raise ValueError(
            'remark-migration: nonempty legacy database requires --remark-backup-manifest and --remark-writers-stopped; run db.py remark-migration-check first'
        )
    manifest = json.loads(Path(manifest_path).read_text())
    if manifest.get('databaseIdentifier') != before['databaseIdentifier'] or not manifest.get('restoreVerifiedAt'):
        raise ValueError('remark-migration: backup database binding/restoration proof missing')
    try:
        restored_at = datetime.fromisoformat(manifest['restoreVerifiedAt'])
        if restored_at.tzinfo is None:
            raise ValueError('timezone required')
    except (TypeError, ValueError):
        raise ValueError(
            'remark-migration: backup restoration timestamp must be an ISO timestamp with timezone'
        ) from None
    backup = Path(manifest.get('backupFile', ''))
    if not backup.is_file():
        raise ValueError('remark-migration: backup file missing')
    with backup.open('rb') as handle:
        checksum = hashlib.file_digest(handle, 'sha256').hexdigest()
    if checksum != manifest.get('backupSha256'):
        raise ValueError('remark-migration: backup file digest mismatch')
    for name, item in before['tables'].items():
        if item['state'] == 'missing' and manifest.get('sourceDigests', {}).get(name) is not None:
            raise ValueError(f'remark-migration: {name} source changed after backup; table is now missing')
        if (
            item['state'] in {'legacy', 'backfilling', 'switched'}
            and manifest.get('sourceDigests', {}).get(name) != item['sourceDigest']
        ):
            raise ValueError(f'remark-migration: {name} source changed after backup; freeze writers and repeat backup')
    return manifest


@contextmanager
def _lock(connection, identifier):
    name = 'remark-v2-' + identifier[:40]
    mysql = connection.dialect.name == 'mysql'
    key = int(identifier[:15], 16)
    result = connection.execute(
        text('SELECT GET_LOCK(:key, 0)' if mysql else 'SELECT pg_try_advisory_lock(:key)'),
        {'key': name if mysql else key},
    ).scalar()
    if not result:
        raise ValueError('remark-migration: another migration holds the lock')
    try:
        yield
    finally:
        connection.execute(
            text('SELECT RELEASE_LOCK(:key)' if mysql else 'SELECT pg_advisory_unlock(:key)'),
            {'key': name if mysql else key},
        )


def _migrate(connection, *, backup_manifest=None, writers_stopped=False, report_path=None, checkpoint=None):  # noqa: PLR0912, PLR0915 -- Physical phase machine.
    """Convert all tables, retain old columns until global verification is durable."""
    report_path = report_path or Path('logs/remark-migration') / f'{uuid4()}.json'
    before = inspect_database(connection)
    needs = any(i['state'] in {'legacy', 'backfilling', 'switched'} and i['rows'] for i in before['tables'].values())
    if needs:
        if not writers_stopped:
            raise ValueError(
                'remark-migration: stop old application/import/managed-data writers; pass --remark-writers-stopped'
            )
        _check_backup(backup_manifest, before)
    elif backup_manifest:
        _check_backup(backup_manifest, before)
    with _lock(connection, before['databaseIdentifier']):
        after_freeze = inspect_database(connection)
        if after_freeze['tables'] != before['tables']:
            raise ValueError('remark-migration: source changed during preflight')
        report = {
            'before': before,
            'backupManifest': str(backup_manifest) if backup_manifest else None,
            'phase': 'preflight',
        }
        _save(report_path, report)
        quote = connection.dialect.identifier_preparer.quote

        def phase(name, table=None):
            report.update(phase=name, table=table, primaryKey=None)
            _save(report_path, report)
            if checkpoint:
                checkpoint(name, table)

        try:
            for name, pk in TARGETS.items():
                state = before['tables'][name]['state']
                target = TEMP if state == 'backfilling' else 'remark' if state in {'complete', 'switched'} else None
                if target:
                    column = next(column for column in before['tables'][name]['columns'] if column['name'] == target)
                    if column.get('comment') != '备注文档':
                        phase('commenting', name)
                        _ensure_json_comment(connection, name, target)
                if state in {'missing', 'complete'}:
                    continue
                if state == 'legacy':
                    phase('adding', name)
                    comment = " COMMENT '备注文档'" if connection.dialect.name == 'mysql' else ''
                    connection.execute(text(f'ALTER TABLE {quote(name)} ADD COLUMN {TEMP} JSON NULL{comment}'))
                    if connection.dialect.name == 'postgresql':
                        connection.execute(text(f"COMMENT ON COLUMN {quote(name)}.{TEMP} IS '备注文档'"))
                    _commit(connection)
                    phase('added', name)
                if state in {'legacy', 'backfilling'}:
                    table = Table(name, MetaData(), autoload_with=connection)
                    table.c[TEMP].type = JSON(none_as_null=True)
                    phase('backfilling', name)
                    for batch in _rows(connection, table, pk, 'remark', TEMP):
                        with _atomic_statements(connection):
                            for key, source, target in batch:
                                report['primaryKey'] = key
                                expected = plain_to_remark(source, identity_key=f'{name}:{key}:remark')
                                if target is not None and target != expected:
                                    raise ValueError(f'{name} pk={key}: target conflict')
                                connection.execute(table.update().where(table.c[pk] == key).values({TEMP: expected}))
                        phase('backfilled-batch', name)
                    check = inspect_database(connection)['tables'][name]
                    if (
                        check['sourceDigest'] != before['tables'][name]['sourceDigest']
                        or check['rows'] != before['tables'][name]['rows']
                    ):
                        raise ValueError(f'{name}: source row set changed')
                    # Verify every target including NULL source rows before switching.
                    for batch in _rows(connection, table, pk, 'remark', TEMP):
                        for key, source, target in batch:
                            if target != plain_to_remark(source, identity_key=f'{name}:{key}:remark'):
                                raise ValueError(f'{name} pk={key}: target equivalence failed')
                    phase('switching', name)
                    _switch_columns(connection, name)
                    phase('switched', name)
            report['verified'] = inspect_database(connection)
            # Recheck every retained source against the backup-bound digest.
            for name, item in report['verified']['tables'].items():
                original = before['tables'][name]
                if item['state'] == 'switched' and (
                    item['sourceDigest'] != original['sourceDigest'] or item['rows'] != original['rows']
                ):
                    raise ValueError(f'{name}: global source equivalence failed')
            phase('globally-verified')
            for name, item in report['verified']['tables'].items():
                if item['state'] == 'switched':
                    connection.execute(text(f'ALTER TABLE {quote(name)} DROP COLUMN {OLD}'))
                    _commit(connection)
                    phase('cleaned', name)
            report['after'] = inspect_database(connection)
            phase('complete')
            return report
        except Exception as error:
            report.update(failedPhase=report['phase'], phase='failed', error=_error_message(error))
            _save(report_path, report)
            raise


def migrate(connection, *, backup_manifest=None, writers_stopped=False, report_path=None, checkpoint=None):
    """Persist failure evidence even when read-only preflight rejects the run."""
    report_path = Path(report_path or Path('logs/remark-migration') / f'{uuid4()}.json')
    try:
        return _migrate(
            connection,
            backup_manifest=backup_manifest,
            writers_stopped=writers_stopped,
            report_path=report_path,
            checkpoint=checkpoint,
        )
    except Exception as error:
        report = json.loads(report_path.read_text()) if report_path.is_file() else {'codec': VERSION}
        if report.get('phase') != 'failed':
            report.update(failedPhase=report.get('phase', 'preflight'), phase='failed', error=_error_message(error))
            _save(report_path, report)
        if isinstance(error, StatementError):
            raise ValueError(f'remark-migration: {_error_message(error)}; see phase report {report_path}') from None
        raise


def configured_engine():
    from config.env import DataBaseConfig  # noqa: PLC0415 -- Defer runtime settings.

    if DataBaseConfig.db_type not in {'mysql', 'postgresql'}:
        raise ValueError('remark-migration: unsupported configured dialect')
    driver = 'postgresql+psycopg2' if DataBaseConfig.db_type == 'postgresql' else 'mysql+pymysql'
    return create_engine(
        URL.create(
            driver,
            username=DataBaseConfig.db_username,
            password=DataBaseConfig.db_password,
            host=DataBaseConfig.db_host,
            port=DataBaseConfig.db_port,
            database=DataBaseConfig.db_database,
        )
    )


def prepare_configured_database(**kwargs):
    engine = configured_engine()
    try:
        with engine.connect() as connection:
            return migrate(connection, **kwargs)
    finally:
        engine.dispose()


def verify_configured_database():
    engine = configured_engine()
    try:
        with engine.connect() as connection:
            report = inspect_database(connection)
            if any(i['state'] != 'complete' for i in report['tables'].values()):
                raise ValueError('remark-migration: incomplete physical migration; run db.py remark-migration-check')
            return report
    finally:
        engine.dispose()
