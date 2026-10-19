#!/usr/bin/env python3
"""Atlas-backed development schema apply adapter for SQLAlchemy metadata."""

from __future__ import annotations

import argparse
import importlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.database import Base  # noqa: E402
from config.env import DataBaseConfig, DataBaseWorkflowStatus  # noqa: E402

MODEL_MODULES = (
    'module_admin.entity.do.user_do',
    'module_admin.entity.do.role_do',
    'module_admin.entity.do.menu_do',
    'module_admin.entity.do.dept_do',
    'module_admin.entity.do.post_do',
    'module_admin.entity.do.dict_do',
    'module_admin.entity.do.config_do',
    'module_admin.entity.do.db_workflow_do',
    'module_admin.entity.do.notice_do',
    'module_admin.entity.do.dashboard_do',
    'module_admin.entity.do.log_do',
    'module_admin.entity.do.audit_log_do',
    'module_admin.entity.do.job_do',
    'module_admin.entity.do.project_do',
    'module_admin.entity.do.project_version_do',
    'module_admin.entity.do.project_topology_do',
    'module_admin.entity.do.device_do',
    'module_admin.entity.do.device_category_do',
    'module_admin.entity.do.protocol_do',
    'module_admin.entity.do.simulation_do',
    'events.models',
)


def _print_field(name: str, value: str) -> None:
    print(f'{name}={value}')


def _database_type() -> str:
    return DataBaseConfig.db_type.lower()


def _atlas_dialect() -> str:
    db_type = _database_type()
    if db_type == 'postgresql':
        return 'postgresql'
    if db_type == 'mysql':
        return 'mysql'
    raise RuntimeError(f'unsupported DB_TYPE for development schema apply: {db_type}')


def _atlas_database_url(database: str) -> str:
    username = quote_plus(DataBaseConfig.db_username)
    password = quote_plus(DataBaseConfig.db_password)
    if _database_type() == 'postgresql':
        return (
            f'postgres://{username}:{password}@{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{database}'
            '?sslmode=disable'
        )
    return (
        f'mysql://{username}:{password}@{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{database}'
        '?charset=utf8mb4'
    )


def _admin_sqlalchemy_url() -> tuple[str, str]:
    db_type = _database_type()
    username = DataBaseConfig.db_username
    password = quote_plus(DataBaseConfig.db_password)

    if db_type == 'postgresql':
        return db_type, (
            f'postgresql+psycopg2://{username}:{password}@'
            f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/postgres'
        )
    if db_type == 'mysql':
        return db_type, (
            f'mysql+pymysql://{username}:{password}@'
            f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/mysql?charset=utf8mb4'
        )
    raise RuntimeError(f'unsupported DB_TYPE for development schema apply: {db_type}')


def _shadow_database_name() -> str:
    database = DataBaseConfig.db_database
    if not re.fullmatch(r'[A-Za-z0-9_\-]+', database):
        raise RuntimeError(f'invalid DB_DATABASE for development schema apply: {database!r}')

    base_name = f'{database}_atlas_{os.getpid()}'
    max_length = 63 if _database_type() == 'postgresql' else 64
    return base_name[:max_length]


def _drop_database(engine_url: str, db_type: str, database: str) -> None:
    engine = create_engine(engine_url, isolation_level='AUTOCOMMIT', pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            if db_type == 'mysql':
                connection.execute(text(f'DROP DATABASE IF EXISTS `{database}`'))
                return

            connection.execute(
                text(
                    'SELECT pg_terminate_backend(pid) '
                    'FROM pg_stat_activity '
                    'WHERE datname = :name AND pid <> pg_backend_pid()'
                ),
                {'name': database},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database}"'))
    finally:
        engine.dispose()


def _create_database(engine_url: str, db_type: str, database: str) -> None:
    engine = create_engine(engine_url, isolation_level='AUTOCOMMIT', pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            if db_type == 'mysql':
                connection.execute(
                    text(
                        f'CREATE DATABASE `{database}` '
                        'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
                    )
                )
                return

            connection.execute(text(f'CREATE DATABASE "{database}"'))
    finally:
        engine.dispose()


def _prepare_shadow_database() -> tuple[str, str]:
    db_type, admin_engine_url = _admin_sqlalchemy_url()
    shadow_database = _shadow_database_name()
    _drop_database(admin_engine_url, db_type, shadow_database)
    _create_database(admin_engine_url, db_type, shadow_database)
    return shadow_database, _atlas_database_url(shadow_database)


def _cleanup_shadow_database(shadow_database: str) -> None:
    db_type, admin_engine_url = _admin_sqlalchemy_url()
    _drop_database(admin_engine_url, db_type, shadow_database)


def _import_model_modules() -> None:
    for module_name in MODEL_MODULES:
        importlib.import_module(module_name)


def _collect_model_classes() -> list[type[object]]:
    _import_model_modules()
    classes = [mapper.class_ for mapper in Base.registry.mappers]
    return sorted(classes, key=lambda cls: (cls.__module__, cls.__name__))


def _load_print_ddl():
    try:
        ddl_module = importlib.import_module('atlas_provider_sqlalchemy.ddl')
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on local env
        raise RuntimeError(
            'atlas-provider-sqlalchemy is not installed. '
            'Install it in the backend virtualenv before using dev-sync.'
        ) from exc

    print_ddl = getattr(ddl_module, 'print_ddl', None)
    if print_ddl is None:  # pragma: no cover - defensive guard
        raise RuntimeError('atlas-provider-sqlalchemy.ddl.print_ddl is unavailable')

    return print_ddl


def print_schema_ddl() -> int:
    model_classes = _collect_model_classes()
    if not model_classes:
        raise RuntimeError('no SQLAlchemy model classes were loaded for development schema apply')

    print_ddl = _load_print_ddl()
    print_ddl(_atlas_dialect(), model_classes)
    return 0


def _atlas_env() -> dict[str, str]:
    env = os.environ.copy()
    python_bin_dir = str(Path(sys.executable).resolve().parent)
    existing_path = env.get('PATH', '')
    env['PATH'] = f'{python_bin_dir}:{existing_path}' if existing_path else python_bin_dir
    return env


def _require_atlas_binary(env: dict[str, str]) -> str:
    atlas_path = shutil.which('atlas', path=env.get('PATH'))
    if atlas_path:
        return atlas_path
    raise RuntimeError(
        'Atlas CLI is not installed or not available in PATH. '
        'Install Atlas before using dev-sync.'
    )


def run_schema_apply(*, project_root: Path, workflow_status: DataBaseWorkflowStatus, invoked_by_startup: bool) -> str:
    env = _atlas_env()
    atlas_binary = _require_atlas_binary(env)
    shadow_database, shadow_url = _prepare_shadow_database()
    target_url = _atlas_database_url(DataBaseConfig.db_database)
    atlas_hcl = project_root / 'atlas.hcl'

    if not atlas_hcl.exists():
        _cleanup_shadow_database(shadow_database)
        raise RuntimeError(f'Atlas config not found: {atlas_hcl}')

    command = [
        atlas_binary,
        'schema',
        'apply',
        '--config',
        f'file://{atlas_hcl}',
        '--env',
        'sqlalchemy',
        '--url',
        target_url,
        '--dev-url',
        shadow_url,
        '--auto-approve',
    ]

    _print_field('atlas_config', str(atlas_hcl))
    _print_field('atlas_target_url', target_url)
    _print_field('atlas_dev_url', shadow_url)
    _print_field('atlas_trigger', 'startup' if invoked_by_startup else 'manual')
    _print_field('atlas_command', ' '.join(command[1:]))
    _print_field('atlas_risk_note', 'atlas will apply destructive schema changes directly when they are planned')

    try:
        result = subprocess.run(
            command,
            cwd=project_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        _cleanup_shadow_database(shadow_database)

    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)

    if result.returncode != 0:
        raise RuntimeError(f'Atlas schema apply failed with exit code {result.returncode}')

    return f'atlas_apply_success:{workflow_status.db_dev_sync_engine}'


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Atlas development schema apply adapter')
    subparsers = parser.add_subparsers(dest='command', required=True)

    schema_parser = subparsers.add_parser('schema', help='Print SQLAlchemy schema DDL for Atlas external_schema')
    schema_parser.set_defaults(handler=_handle_schema_command)

    return parser


def _handle_schema_command(_args: argparse.Namespace) -> int:
    return print_schema_ddl()


def main(argv: list[str] | None = None) -> int:
    os.chdir(PROJECT_ROOT)
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.handler(args)
    except RuntimeError as exc:
        print(f'error={exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
