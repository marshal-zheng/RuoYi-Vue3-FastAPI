#!/usr/bin/env python3
"""One-click checks for sensitive hash columns and backfill status."""
import asyncio
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, or_, select
from sqlalchemy import inspect

from config.database import async_engine, AsyncSessionLocal
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.user_do import UserDO
from utils.log_util import logger


CHECKS: List[Tuple[object, str, str]] = [
    (UserDO, 'phonenumber', 'phonenumber_hash'),
    (UserDO, 'email', 'email_hash'),
    (UserDO, 'id_card', 'id_card_hash'),
    (DeptDO, 'phone', 'phone_hash'),
]

INDEX_CHECKS = [
    (UserDO, 'idx_user_phone_hash'),
    (UserDO, 'idx_user_email_hash'),
    (UserDO, 'idx_user_id_card_hash'),
]


async def _check_schema() -> List[str]:
    issues: List[str] = []

    async with async_engine.connect() as conn:
        def _inspect(sync_conn):
            inspector = inspect(sync_conn)
            for model, field, hash_field in CHECKS:
                table = model.__tablename__
                if table not in inspector.get_table_names():
                    issues.append(f"missing table: {table}")
                    continue
                columns = {col['name'] for col in inspector.get_columns(table)}
                if field not in columns:
                    issues.append(f"missing column: {table}.{field}")
                if hash_field not in columns:
                    issues.append(f"missing column: {table}.{hash_field}")
            for model, index_name in INDEX_CHECKS:
                table = model.__tablename__
                if table not in inspector.get_table_names():
                    continue
                indexes = {idx['name'] for idx in inspector.get_indexes(table)}
                if index_name not in indexes:
                    issues.append(f"missing index: {table}.{index_name}")
        await conn.run_sync(_inspect)
    return issues


async def _check_backfill() -> List[str]:
    issues: List[str] = []
    async with AsyncSessionLocal() as session:
        for model, field, hash_field in CHECKS:
            col = getattr(model, field)
            hash_col = getattr(model, hash_field)
            stmt = select(func.count('*')).where(
                col.is_not(None),
                col != '',
                or_(hash_col.is_(None), hash_col == ''),
            )
            result = await session.execute(stmt)
            missing = result.scalar() or 0
            if missing:
                issues.append(f"backfill pending: {model.__tablename__}.{hash_field} missing {missing} rows")
    return issues


async def main() -> int:
    logger.info('Checking sensitive hash columns...')
    schema_issues = await _check_schema()
    if schema_issues:
        for item in schema_issues:
            logger.error(item)
        return 1

    logger.info('Checking sensitive hash backfill...')
    backfill_issues = await _check_backfill()
    if backfill_issues:
        for item in backfill_issues:
            logger.error(item)
        return 2

    logger.info('Sensitive data checks passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
