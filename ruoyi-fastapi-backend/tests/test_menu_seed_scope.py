from pathlib import Path


def test_menu_model_includes_managed_by_seed_column() -> None:
    from module_admin.entity.do.menu_do import MenuDO

    assert hasattr(MenuDO, 'managed_by_seed')


def test_migration_contains_managed_by_seed_change() -> None:
    versions_dir = Path(__file__).parent.parent / 'alembic' / 'versions'
    migration_files = sorted(versions_dir.glob('*managed_by_seed*.py'))
    assert migration_files, 'managed_by_seed migration should exist'
    content = migration_files[-1].read_text(encoding='utf-8')
    assert 'managed_by_seed' in content

