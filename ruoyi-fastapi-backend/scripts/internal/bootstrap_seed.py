"""
Bootstrap seed data management script with YAML support.

This script manages bootstrap-only initial data population for the
RuoYi-FastAPI application. Managed reference data such as menus, role-menu
grants, dictionaries, and system configs now belongs to the unified
`db.py` pipeline.

Usage:
    python scripts/db.py bootstrap-seed --env dev
    python scripts/db.py bootstrap-seed --env prod
    python scripts/db.py bootstrap-seed --env dev --reset
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import delete, select

from common.remark_document_v1 import plain_to_remark
from config.database import AsyncSessionLocal
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.post_do import PostDO
from module_admin.entity.do.role_do import RoleDeptDO, RoleDO
from module_admin.entity.do.user_do import UserDO, UserPostDO, UserRoleDO
from utils.log_util import logger
from utils.pwd_util import PwdUtil

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SeedDataManager:
    """
    Seed data manager for bootstrap initialization with YAML support.

    Handles creation of initial data required for application bootstrap,
    including roles, departments, posts, users, and bootstrap relations.

    Supports:
    - Environment-aware seeding (dev vs prod)
    - YAML-based data definitions with base + overlay pattern
    - Idempotent operations (safe to run multiple times)
    - Transaction management with rollback on error
    - Dependency-ordered bootstrap insertion
    """

    # ORM model mapping
    MODEL_MAP: ClassVar[dict[str, type[DeptDO] | type[PostDO] | type[RoleDO] | type[UserDO]]] = {
        'depts': DeptDO,
        'posts': PostDO,
        'roles': RoleDO,
        'users': UserDO,
    }

    # Primary key field mapping
    PRIMARY_KEY_MAP: ClassVar[dict[str, str]] = {
        'depts': 'dept_id',
        'posts': 'post_id',
        'roles': 'role_id',
        'users': 'user_id',
    }

    def __init__(self, env: str = 'dev'):
        """
        Initialize seed data manager for specific environment.

        Args:
            env: Environment name ('dev' or 'prod')
        """
        self.env = env
        self.session: AsyncSession = None
        self.data_dir = Path(__file__).resolve().parents[1] / 'seed_data'
        self._manifest: dict = None
        self._overlay_data: dict = None
        logger.info(f'Initializing SeedDataManager for environment: {env}')

    def load_manifest(self) -> dict:
        """Load manifest.yaml configuration."""
        if self._manifest is None:
            manifest_path = self.data_dir / 'manifest.yaml'
            with manifest_path.open(encoding='utf-8') as f:
                self._manifest = yaml.safe_load(f)
        return self._manifest

    def load_base_data(self, entity: str) -> list[dict[str, Any]]:
        """
        Load base data from YAML file for specified entity.

        Args:
            entity: Entity name (e.g., 'depts', 'menus')

        Returns:
            List of data dictionaries
        """
        base_path = self.data_dir / 'base' / f'{entity}.yaml'
        if not base_path.exists():
            return []

        with base_path.open(encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return data.get(entity, []) if data else []

    def load_overlay(self) -> dict[str, Any]:
        """
        Load environment overlay data.

        Returns:
            Dictionary with all overlay data for current environment
        """
        if self._overlay_data is None:
            overlay_path = self.data_dir / 'overlays' / f'{self.env}.yaml'
            if overlay_path.exists():
                with overlay_path.open(encoding='utf-8') as f:
                    self._overlay_data = yaml.safe_load(f) or {}
            else:
                self._overlay_data = {}
        return self._overlay_data

    async def seed_all(self, reset: bool = False, *, bootstrap_only: bool = True) -> None:
        """
        Execute bootstrap seed operations in correct dependency order.

        Managed reference data is intentionally excluded and must flow through
        `python scripts/db.py dev-sync` or `deploy`.

        Args:
            reset: If True, clear existing data before seeding
            bootstrap_only: Explicit bootstrap-only mode switch

        Raises:
            Exception: If any seed operation fails (transaction will be rolled back)
        """
        if self.session is not None:
            await self._seed_all_with_session(reset=reset, bootstrap_only=bootstrap_only)
            return

        async with AsyncSessionLocal() as session:
            self.session = session
            try:
                await self._seed_all_with_session(reset=reset, bootstrap_only=bootstrap_only)
                await session.commit()
            finally:
                self.session = None

    async def _seed_all_with_session(self, *, reset: bool, bootstrap_only: bool) -> None:
        logger.info('=' * 60)
        logger.info('Starting bootstrap seed data operations')
        logger.info(f'Environment: {self.env}')
        logger.info(f'Reset mode: {reset}')
        logger.info('Seed mode: bootstrap-only')
        logger.info('=' * 60)

        if not bootstrap_only:
            logger.warning(
                'Managed reference data seeding has moved to db_workflow; '
                'bootstrap-seed now always runs in bootstrap-only mode'
            )

        if reset:
            logger.warning('Reset mode enabled - clearing existing bootstrap data')
            await self.clear_data()

        # Seed bootstrap data in dependency order.
        await self.seed_entity('depts')
        await self.seed_entity('posts')
        await self.seed_entity('roles')

        # Users and bootstrap relations come from environment overlays.
        await self.seed_users()
        await self.seed_user_roles()
        await self.seed_user_posts()
        await self.seed_role_depts()

        logger.info('=' * 60)
        logger.info('Bootstrap seed data operations completed successfully')
        logger.info('=' * 60)

    async def seed_entity(self, entity: str) -> None:
        """
        Seed a single bootstrap entity type from base YAML.

        Args:
            entity: Entity name (e.g., 'depts', 'roles')
        """
        logger.info(f'Seeding {entity}...')

        model = self.MODEL_MAP.get(entity)
        pk_field = self.PRIMARY_KEY_MAP.get(entity)

        if not model or not pk_field:
            logger.warning(f'Unknown entity: {entity}, skipping')
            return

        # Check if data already exists
        pk_attr = getattr(model, pk_field)
        result = await self.session.execute(select(model).where(pk_attr == 1).limit(1))
        if result.scalar_one_or_none():
            logger.info(f'{entity} already exist, skipping')
            return

        # Load data
        data = self.load_base_data(entity)
        if not data:
            logger.info(f'No {entity} data found')
            return

        now = datetime.now()
        count = 0

        for item_data in data:
            # Add audit fields
            item_data_with_audit = {
                **item_data,
                'create_by': 'admin',
                'create_time': now,
                'update_by': '',
            }

            if entity in {'posts', 'roles', 'users'}:
                item_data_with_audit['remark'] = plain_to_remark(
                    item_data.get('remark'), identity_key=f'{model.__tablename__}:{item_data[pk_field]}:remark'
                )
            instance = model(**item_data_with_audit)
            self.session.add(instance)
            count += 1

        await self.session.flush()
        logger.info(f'Created {count} {entity}')

    async def seed_users(self) -> None:
        """
        Create users from overlay data.

        Users are environment-specific and defined in overlays.
        Passwords are hashed during insertion.
        """
        logger.info('Seeding users...')

        # Check if admin user already exists
        result = await self.session.execute(select(UserDO).where(UserDO.user_name == 'admin'))
        if result.scalar_one_or_none():
            logger.info('Admin user already exists, skipping user seeding')
            return

        overlay = self.load_overlay()
        users_data = overlay.get('users', [])

        if not users_data:
            logger.warning('No users defined in overlay, skipping')
            return

        now = datetime.now()
        count = 0

        for source_user in users_data:
            user_data = dict(source_user)
            user_data['remark'] = plain_to_remark(
                user_data.get('remark'), identity_key=f'sys_user:{user_data["user_id"]}:remark'
            )
            # Hash the password
            plain_password = user_data.pop('password', 'admin123')
            hashed_password = PwdUtil.get_password_hash(plain_password)

            user = UserDO(
                **user_data,
                password=hashed_password,
                login_date=now,
                create_by='admin',
                create_time=now,
                update_by='',
            )
            self.session.add(user)
            count += 1
            logger.info(f'Created user: {user_data.get("user_name")}')

        await self.session.flush()
        logger.info(f'Created {count} users')

    async def seed_roles(self) -> None:
        """Seed roles from base YAML (wrapper for seed_entity)."""
        await self.seed_entity('roles')

    async def seed_user_roles(self) -> None:
        """Create user-role associations from overlay."""
        logger.info('Seeding user-role associations...')

        result = await self.session.execute(select(UserRoleDO).where(UserRoleDO.user_id == 1, UserRoleDO.role_id == 1))
        if result.scalar_one_or_none():
            logger.info('User-role associations already exist, skipping')
            return

        overlay = self.load_overlay()
        user_roles = overlay.get('user_roles', [])

        count = 0
        for ur in user_roles:
            self.session.add(UserRoleDO(user_id=ur['user_id'], role_id=ur['role_id']))
            count += 1

        await self.session.flush()
        logger.info(f'Created {count} user-role associations')

    async def seed_user_posts(self) -> None:
        """Create user-post associations from overlay."""
        logger.info('Seeding user-post associations...')

        result = await self.session.execute(select(UserPostDO).where(UserPostDO.user_id == 1, UserPostDO.post_id == 1))
        if result.scalar_one_or_none():
            logger.info('User-post associations already exist, skipping')
            return

        overlay = self.load_overlay()
        user_posts = overlay.get('user_posts', [])

        count = 0
        for up in user_posts:
            self.session.add(UserPostDO(user_id=up['user_id'], post_id=up['post_id']))
            count += 1

        await self.session.flush()
        logger.info(f'Created {count} user-post associations')

    async def seed_role_depts(self) -> None:
        """Create role-dept associations from overlay."""
        logger.info('Seeding role-dept associations...')

        result = await self.session.execute(select(RoleDeptDO).where(RoleDeptDO.role_id == 2))
        if result.scalar_one_or_none():
            logger.info('Role-dept associations already exist, skipping')
            return

        overlay = self.load_overlay()
        role_depts = overlay.get('role_depts', [])

        count = 0
        for rd in role_depts:
            role_id = rd['role_id']
            dept_ids = rd.get('dept_ids', [])

            for dept_id in dept_ids:
                self.session.add(RoleDeptDO(role_id=role_id, dept_id=dept_id))
                count += 1

        await self.session.flush()
        logger.info(f'Created {count} role-dept associations')

    async def clear_data(self) -> None:
        """
        Clear bootstrap seed data from database.

        Deletes bootstrap data in reverse dependency order to respect foreign key constraints.
        Used for reset functionality.

        Warning: This is a destructive operation!
        """
        logger.warning('Clearing existing bootstrap seed data...')

        # Delete in reverse dependency order
        # 1. Relationship tables first
        await self.session.execute(delete(UserRoleDO))
        await self.session.execute(delete(UserPostDO))
        await self.session.execute(delete(RoleDeptDO))
        logger.info('Cleared bootstrap relationship tables')

        # 2. Dependent entities
        await self.session.execute(delete(UserDO))
        logger.info('Cleared users')

        # 3. Independent entities
        await self.session.execute(delete(RoleDO))
        await self.session.execute(delete(DeptDO))
        await self.session.execute(delete(PostDO))
        logger.info('Cleared bootstrap independent entities')

        await self.session.flush()
        logger.info('All bootstrap seed data cleared successfully')


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Bootstrap-only seed data management script', add_help=True)
    parser.add_argument(
        '--env',
        type=str,
        default=os.environ.get('APP_ENV', 'dev'),
        choices=['dev', 'prod'],
        help='Environment (dev or prod, default: from APP_ENV or dev)',
    )
    parser.add_argument('--reset', action='store_true', help='Clear existing data before seeding')
    parser.add_argument(
        '--bootstrap-only',
        action='store_true',
        help='Explicitly run bootstrap-only seed mode (the only supported mode)',
    )
    return parser.parse_args(argv)


async def _main_async(args: argparse.Namespace) -> int:
    """
    Main entry point for seed data script.
    """
    logger.info(f'Starting seed data script with environment: {args.env}')
    if not args.bootstrap_only:
        logger.warning(
            'bootstrap seed now runs in bootstrap-only mode by default; managed data has moved to db.py deploy/dev-sync'
        )

    manager = SeedDataManager(env=args.env)
    await manager.seed_all(reset=args.reset, bootstrap_only=True)

    logger.info('Seed data script completed successfully')
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    os.environ['APP_ENV'] = args.env
    return asyncio.run(_main_async(args))


if __name__ == '__main__':
    sys.exit(main())
