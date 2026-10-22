import importlib.util
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, create_engine, event


def test_initial_table_order_follows_foreign_key_dependencies(monkeypatch):
    path = Path(__file__).parents[3] / 'alembic/versions/20260123_120000_init_schema.py'
    spec = importlib.util.spec_from_file_location('initial_migration', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metadata = MetaData()
    Table('child', metadata, Column('parent_id', Integer, ForeignKey('parent.id')))
    Table('parent', metadata, Column('id', Integer, primary_key=True))
    order = []
    for table in metadata.tables.values():
        event.listen(table, 'before_create', lambda table, _connection, **_kwargs: order.append(table.name))
    monkeypatch.setattr(module, 'Base', SimpleNamespace(metadata=metadata))
    engine = create_engine('sqlite://')
    with engine.connect() as connection:
        monkeypatch.setattr(module.op, 'get_bind', lambda: connection)
        module.upgrade()
    assert order == ['parent', 'child']
