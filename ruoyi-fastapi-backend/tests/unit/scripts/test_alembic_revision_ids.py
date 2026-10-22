from alembic.runtime.migration import MigrationContext

from scripts.internal.db_workflow import alembic_revision_ids  # noqa: F401 -- Registers public dialect DDL hooks.


def test_revision_table_fits_the_existing_formal_chain():
    for dialect in ['mysql', 'postgresql']:
        impl = MigrationContext.configure(dialect_name=dialect).impl
        table = impl.version_table_impl(
            version_table='alembic_version', version_table_schema=None, version_table_pk=True
        )
        assert table.c.version_num.type.length >= len('20260405_workflow_object_capability')
