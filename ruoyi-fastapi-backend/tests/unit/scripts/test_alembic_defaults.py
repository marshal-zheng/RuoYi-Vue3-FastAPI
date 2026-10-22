from alembic.runtime.migration import MigrationContext
from sqlalchemy import Boolean, Column, DateTime, Integer

from scripts.internal.db_workflow import alembic_revision_ids  # noqa: F401 -- Registers dialect DDL hooks.


def test_mysql_default_synonyms_do_not_generate_permanent_drift():
    implementation = MigrationContext.configure(dialect_name='mysql').impl
    datetime = Column('created_at', DateTime())
    boolean = Column('deleted', Boolean())
    integer = Column('number', Integer())
    assert implementation.compare_server_default(datetime, datetime, 'now()', 'CURRENT_TIMESTAMP') is False
    assert implementation.compare_server_default(datetime, datetime, 'now(6)', 'CURRENT_TIMESTAMP(6)') is False
    assert implementation.compare_server_default(datetime, datetime, 'now(6)', 'CURRENT_TIMESTAMP') is True
    assert (
        implementation.compare_server_default(
            datetime, datetime, 'now()', 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
        )
        is True
    )
    assert implementation.compare_server_default(boolean, boolean, 'false', "'0'") is False
    assert implementation.compare_server_default(boolean, boolean, 'false', "'1'") is True
    assert implementation.compare_server_default(integer, integer, 'false', "'0'") is True
