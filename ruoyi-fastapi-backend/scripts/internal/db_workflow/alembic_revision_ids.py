"""Fit the repository's existing revision IDs through Alembic's public DDL hook."""

import re

from alembic.ddl.mysql import MySQLImpl
from alembic.ddl.postgresql import PostgresqlImpl
from sqlalchemy import Boolean, DateTime, String, inspect, text


class _LongRevisionIds:
    def version_table_impl(self, **kwargs):
        table = super().version_table_impl(**kwargs)
        table.c.version_num.type = String(128)
        return table


def _mysql_default_token(column, rendered):
    if rendered is None:
        return None
    value = rendered.strip().lower()
    if isinstance(column.type, DateTime):
        timestamp = re.fullmatch(r'(?:now|current_timestamp)(?:\((\d*)\))?', value)
        if timestamp:
            return ('timestamp', int(timestamp.group(1) or 0))
    if isinstance(column.type, Boolean):
        value = value.strip("'()")
        if value in {'false', '0'}:
            return ('boolean', False)
        if value in {'true', '1'}:
            return ('boolean', True)
    return None


class RepositoryMySQLImpl(_LongRevisionIds, MySQLImpl):
    __dialect__ = 'mysql'

    def compare_server_default(
        self, inspector_column, metadata_column, rendered_metadata_default, rendered_inspector_default
    ):
        # MySQL reflects NOW() as CURRENT_TIMESTAMP and booleans as 0/1.
        # Full matching preserves fractional precision and ON UPDATE changes.
        expected = _mysql_default_token(metadata_column, rendered_metadata_default)
        actual = _mysql_default_token(metadata_column, rendered_inspector_default)
        if expected is not None and expected == actual:
            return False
        return super().compare_server_default(
            inspector_column,
            metadata_column,
            rendered_metadata_default,
            rendered_inspector_default,
        )


class RepositoryPostgresqlImpl(_LongRevisionIds, PostgresqlImpl):
    __dialect__ = 'postgresql'


def ensure_existing_revision_capacity(connection):
    inspector = inspect(connection)
    if not inspector.has_table('alembic_version'):
        connection.commit()
        return
    column = next(c for c in inspector.get_columns('alembic_version') if c['name'] == 'version_num')
    if getattr(column['type'], 'length', 128) >= 128:
        connection.commit()
        return
    if connection.dialect.name == 'mysql':
        connection.execute(text('ALTER TABLE alembic_version MODIFY version_num VARCHAR(128) NOT NULL'))
    elif connection.dialect.name == 'postgresql':
        connection.execute(text('ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)'))
    connection.commit()
