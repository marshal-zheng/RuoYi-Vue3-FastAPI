"""Compiled/memory PostgreSQL evidence; this is not a real PG rehearsal."""

import importlib.util
import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import JSON, Column, Integer, MetaData, Table, create_engine
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.schema import CreateTable

from common.remark_document_v1 import plain_to_remark
from module_generator.entity.do.gen_do import GenTableColumnDO, GenTableDO
from scripts.data_migrations.remark_document_v2 import OLD, TEMP, _switch_columns


@pytest.mark.parametrize('dialect', [mysql.dialect(), postgresql.dialect()])
def test_native_json_uses_bound_whole_document_and_sql_null(dialect):
    table = Table('sys_user', MetaData(), Column('user_id', Integer), Column('remark', JSON(none_as_null=True)))
    document = plain_to_remark('文字\n尾 ', identity_key='sys_user:1:remark')
    compiled = table.update().where(table.c.user_id == 1).values(remark=document).compile(dialect=dialect)
    assert compiled.params['remark'] == document
    assert '文字' not in str(compiled)
    processor = table.c.remark.type.bind_processor(dialect)
    assert processor(None) is None
    assert json.loads(processor(document)) == document


class TransactionalPGProbe:
    dialect = postgresql.dialect()

    def __init__(self, *, fail_second=False):
        self.columns = {'remark', TEMP}
        self.commands = []
        self.fail_second = fail_second
        self.backup = None

    def get_execution_options(self):
        return {'isolation_level': 'AUTOCOMMIT'}

    def execute(self, statement):
        sql = str(statement)
        self.commands.append(sql)
        if sql == 'BEGIN':
            self.backup = self.columns.copy()
        elif sql == 'ROLLBACK':
            self.columns = self.backup.copy()
        elif 'RENAME COLUMN remark TO' in sql:
            self.columns.remove('remark')
            self.columns.add(OLD)
        elif f'RENAME COLUMN {TEMP} TO remark' in sql:
            if self.fail_second:
                raise RuntimeError('injected second rename failure')
            self.columns.remove(TEMP)
            self.columns.add('remark')


def test_pg_renames_share_transaction_even_under_alembic_autocommit():
    connection = TransactionalPGProbe()
    _switch_columns(connection, 'sys_user')
    assert connection.commands[0] == 'BEGIN'
    assert connection.commands[-1] == 'COMMIT'
    assert connection.columns == {'remark', OLD}


def test_pg_second_rename_failure_restores_the_original_physical_state():
    connection = TransactionalPGProbe(fail_second=True)
    with pytest.raises(RuntimeError, match='second rename failure'):
        _switch_columns(connection, 'sys_user')
    assert connection.commands[-1] == 'ROLLBACK'
    assert connection.columns == {'remark', TEMP}


def test_missing_generator_table_shape_is_frozen_and_matches_public_orm(monkeypatch):
    specification = importlib.util.spec_from_file_location(
        'remark_revision', Path(__file__).parents[3] / 'alembic/versions/20261022_remark_document_v2.py'
    )
    revision = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(revision)
    tables = MetaData()
    engine = create_engine('sqlite://')
    context = SimpleNamespace(config=SimpleNamespace(attributes={}), autocommit_block=nullcontext)
    with engine.connect() as connection:
        monkeypatch.setattr(revision.op, 'get_bind', lambda: connection)
        monkeypatch.setattr(revision.op, 'get_context', lambda: context)
        monkeypatch.setattr(revision, 'migrate', lambda *_args, **_kwargs: None)
        monkeypatch.setattr(revision.op, 'create_table', lambda name, *columns: Table(name, tables, *columns))
        revision.upgrade()
    for expected in [GenTableDO.__table__, GenTableColumnDO.__table__]:
        actual = tables.tables[expected.name]
        assert set(actual.c.keys()) == set(expected.c.keys())
        for column in expected.c:
            frozen = actual.c[column.name]
            assert (str(frozen.type), frozen.nullable, frozen.comment) == (
                str(column.type),
                column.nullable,
                column.comment,
            )
        assert 'CREATE TABLE' in str(CreateTable(actual).compile(dialect=postgresql.dialect()))
    assert tables.tables['gen_table'].c.remark.type.none_as_null is True
