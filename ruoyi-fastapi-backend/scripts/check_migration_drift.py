#!/usr/bin/env python3
"""Fail CI when SQLAlchemy models drift from Alembic migrations."""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

from alembic import command
from alembic.config import Config
from alembic.util.exc import CommandError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


def _build_admin_url() -> tuple[str, str, str]:
    db_type = _env('DB_TYPE', 'mysql').lower()
    host = _env('DB_HOST', '127.0.0.1')
    port = _env('DB_PORT', '3306' if db_type == 'mysql' else '5432')
    username = _env('DB_USERNAME', 'root' if db_type == 'mysql' else 'postgres')
    password = quote_plus(_env('DB_PASSWORD', 'root' if db_type == 'mysql' else 'postgres'))
    database = _env('DB_DATABASE', 'ruoyi_fastapi_ci')

    if not re.fullmatch(r'[A-Za-z0-9_\-]+', database):
        raise ValueError(f'Invalid DB_DATABASE: {database!r}')

    if db_type == 'mysql':
        admin_url = f'mysql+pymysql://{username}:{password}@{host}:{port}/mysql?charset=utf8mb4'
    elif db_type == 'postgresql':
        admin_url = f'postgresql+psycopg2://{username}:{password}@{host}:{port}/postgres'
    else:
        raise ValueError(f'Unsupported DB_TYPE for migration drift check: {db_type}')

    return db_type, database, admin_url


def _wait_for_database_ready(admin_url: str, timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        engine = create_engine(admin_url, pool_pre_ping=True)
        try:
            with engine.connect() as connection:
                connection.execute(text('SELECT 1'))
            return
        except OperationalError as exc:
            last_error = exc
            time.sleep(2)
        finally:
            engine.dispose()

    raise RuntimeError(f'Database is not ready in {timeout_seconds}s') from last_error


def _ensure_database_exists(db_type: str, database: str, admin_url: str) -> None:
    engine = create_engine(admin_url, isolation_level='AUTOCOMMIT', pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            if db_type == 'mysql':
                connection.execute(
                    text(
                        f'CREATE DATABASE IF NOT EXISTS `{database}` '
                        'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
                    )
                )
                return

            exists = connection.execute(
                text('SELECT 1 FROM pg_database WHERE datname = :name'),
                {'name': database},
            ).scalar_one_or_none()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{database}"'))
    finally:
        engine.dispose()


def _run_migration_drift_check(project_root: Path) -> None:
    alembic_cfg = Config(str(project_root / 'alembic.ini'))
    command.upgrade(alembic_cfg, 'head')
    command.check(alembic_cfg)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)

    db_type, database, admin_url = _build_admin_url()
    print(f'[migration-check] db_type={db_type}, database={database}')
    _wait_for_database_ready(admin_url)
    _ensure_database_exists(db_type, database, admin_url)

    try:
        _run_migration_drift_check(project_root)
    except CommandError as exc:
        print('[migration-check] migration drift detected:')
        print(str(exc))
        return 1
    except Exception as exc:  # pragma: no cover
        print(f'[migration-check] unexpected failure: {exc}')
        return 1

    print('[migration-check] passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
