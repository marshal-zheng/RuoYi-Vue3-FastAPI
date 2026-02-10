"""
Database seed data management script with YAML support.

This script manages initial data population for the RuoYi-FastAPI application.
It supports environment-aware seeding (dev vs prod), idempotent operations,
and loads data from YAML files.

Usage:
    python scripts/seed_data.py --env dev
    python scripts/seed_data.py --env prod
    python scripts/seed_data.py --env dev --reset
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Parse arguments BEFORE importing config modules to avoid conflicts
parser = argparse.ArgumentParser(
    description='Database seed data management script',
    add_help=True
)
parser.add_argument(
    '--env',
    type=str,
    default=os.environ.get('APP_ENV', 'dev'),
    choices=['dev', 'prod'],
    help='Environment (dev or prod, default: from APP_ENV or dev)'
)
parser.add_argument(
    '--reset',
    action='store_true',
    help='Clear existing data before seeding'
)

# Parse only known args to avoid conflicts with env.py argparse
cli_args, unknown = parser.parse_known_args()

# Set APP_ENV before importing config modules
os.environ['APP_ENV'] = cli_args.env

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal
from utils.log_util import logger
from utils.pwd_util import PwdUtil

# Import all ORM models
from module_admin.entity.do.user_do import UserDO, UserRoleDO, UserPostDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO, RoleDeptDO
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.post_do import PostDO
from module_admin.entity.do.dict_do import DictTypeDO, DictDataDO
from module_admin.entity.do.config_do import ConfigDO


class SeedDataManager:
    """
    Seed data manager for database initialization with YAML support.
    
    Handles creation of initial data required for application bootstrap,
    including admin users, roles, permissions, system configuration, etc.
    
    Supports:
    - Environment-aware seeding (dev vs prod)
    - YAML-based data definitions with base + overlay pattern
    - Idempotent operations (safe to run multiple times)
    - Transaction management with rollback on error
    - Dependency-ordered data insertion
    """
    
    # ORM model mapping
    MODEL_MAP = {
        'depts': DeptDO,
        'posts': PostDO,
        'roles': RoleDO,
        'menus': MenuDO,
        'dict_types': DictTypeDO,
        'dict_data': DictDataDO,
        'configs': ConfigDO,
        'users': UserDO,
    }
    
    # Primary key field mapping
    PRIMARY_KEY_MAP = {
        'depts': 'dept_id',
        'posts': 'post_id',
        'roles': 'role_id',
        'menus': 'menu_id',
        'dict_types': 'dict_id',
        'dict_data': 'dict_code',
        'configs': 'config_id',
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
        self.data_dir = Path(__file__).parent / 'seed_data'
        self._manifest: dict = None
        self._overlay_data: dict = None
        logger.info(f"Initializing SeedDataManager for environment: {env}")
    
    def load_manifest(self) -> dict:
        """Load manifest.yaml configuration."""
        if self._manifest is None:
            manifest_path = self.data_dir / 'manifest.yaml'
            with open(manifest_path, 'r', encoding='utf-8') as f:
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
        
        with open(base_path, 'r', encoding='utf-8') as f:
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
                with open(overlay_path, 'r', encoding='utf-8') as f:
                    self._overlay_data = yaml.safe_load(f) or {}
            else:
                self._overlay_data = {}
        return self._overlay_data
    
    def merge_data(
        self,
        base: list[dict[str, Any]],
        overlay: list[dict[str, Any]],
        key_field: str
    ) -> list[dict[str, Any]]:
        """
        Merge base and overlay data.
        
        Overlay data with matching key overwrites base data.
        New overlay items are appended.
        
        Args:
            base: Base data list
            overlay: Overlay data list
            key_field: Field to use as unique key
            
        Returns:
            Merged data list
        """
        if not overlay:
            return base
        
        # Create lookup dict from base data
        result_map = {item[key_field]: item.copy() for item in base}
        
        # Apply overlay
        for item in overlay:
            key = item.get(key_field)
            if key is not None:
                if key in result_map:
                    # Update existing item
                    result_map[key].update(item)
                else:
                    # Add new item
                    result_map[key] = item.copy()
        
        return list(result_map.values())
    
    async def seed_all(self, reset: bool = False) -> None:
        """
        Execute all seed data operations in correct dependency order.
        
        This is the main orchestration method that coordinates all seeding operations.
        Data is inserted in dependency order to respect foreign key constraints.
        
        Args:
            reset: If True, clear existing data before seeding
            
        Raises:
            Exception: If any seed operation fails (transaction will be rolled back)
        """
        async with AsyncSessionLocal() as session:
            self.session = session
            
            logger.info("=" * 60)
            logger.info("Starting database seed data operations")
            logger.info(f"Environment: {self.env}")
            logger.info(f"Reset mode: {reset}")
            logger.info("=" * 60)
            
            if reset:
                logger.warning("Reset mode enabled - clearing existing data")
                await self.clear_data()
            
            # Seed data in dependency order
            # 1. Independent entities from base YAML files
            await self.seed_entity('depts')
            await self.seed_entity('posts')
            await self.seed_entity('roles')
            await self.seed_entity('menus')
            await self.seed_entity('dict_types')
            await self.seed_entity('dict_data')
            await self.seed_configs()
            
            # 2. Users from overlay (environment-specific)
            await self.seed_users()
            
            # 3. Relationship tables from overlay
            await self.seed_user_roles()
            await self.seed_user_posts()
            await self.seed_role_menus()
            await self.seed_role_depts()
            
            # Commit all changes
            await session.commit()
            
            logger.info("=" * 60)
            logger.info("Database seed data operations completed successfully")
            logger.info("=" * 60)
    
    async def seed_entity(self, entity: str) -> None:
        """
        Seed a single entity type from base YAML.
        
        Args:
            entity: Entity name (e.g., 'depts', 'menus')
        """
        logger.info(f"Seeding {entity}...")
        
        model = self.MODEL_MAP.get(entity)
        pk_field = self.PRIMARY_KEY_MAP.get(entity)
        
        if not model or not pk_field:
            logger.warning(f"Unknown entity: {entity}, skipping")
            return
        
        # Check if data already exists
        pk_attr = getattr(model, pk_field)
        result = await self.session.execute(
            select(model).where(pk_attr == 1).limit(1)
        )
        if result.scalar_one_or_none():
            logger.info(f"{entity} already exist, skipping")
            return
        
        # Load data
        data = self.load_base_data(entity)
        if not data:
            logger.info(f"No {entity} data found")
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
            
            instance = model(**item_data_with_audit)
            self.session.add(instance)
            count += 1
        
        await self.session.flush()
        logger.info(f"Created {count} {entity}")
    
    async def seed_configs(self) -> None:
        """
        Seed system configuration with overlay support.
        
        Base configs are loaded first, then overlay configs update/add entries.
        """
        logger.info("Seeding system configuration...")
        
        # Check if config already exists
        result = await self.session.execute(
            select(ConfigDO).where(ConfigDO.config_id == 1)
        )
        if result.scalar_one_or_none():
            logger.info("System configuration already exists, skipping")
            return
        
        # Load base and overlay configs
        base_configs = self.load_base_data('configs')
        overlay = self.load_overlay()
        overlay_configs = overlay.get('configs', [])
        
        # For overlay, use config_key as the merge key
        config_map = {c['config_key']: c.copy() for c in base_configs}
        
        for overlay_config in overlay_configs:
            key = overlay_config.get('config_key')
            if key and key in config_map:
                config_map[key].update(overlay_config)
        
        now = datetime.now()
        count = 0
        
        for config_data in config_map.values():
            config_data_with_audit = {
                **config_data,
                'create_by': 'admin',
                'create_time': now,
                'update_by': '',
            }
            config = ConfigDO(**config_data_with_audit)
            self.session.add(config)
            count += 1
        
        await self.session.flush()
        logger.info(f"Created {count} configuration entries")
    
    async def seed_users(self) -> None:
        """
        Create users from overlay data.
        
        Users are environment-specific and defined in overlays.
        Passwords are hashed during insertion.
        """
        logger.info("Seeding users...")
        
        # Check if admin user already exists
        result = await self.session.execute(
            select(UserDO).where(UserDO.user_name == 'admin')
        )
        if result.scalar_one_or_none():
            logger.info("Admin user already exists, skipping user seeding")
            return
        
        overlay = self.load_overlay()
        users_data = overlay.get('users', [])
        
        if not users_data:
            logger.warning("No users defined in overlay, skipping")
            return
        
        now = datetime.now()
        count = 0
        
        for user_data in users_data:
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
            logger.info(f"Created user: {user_data.get('user_name')}")
        
        await self.session.flush()
        logger.info(f"Created {count} users")

    async def seed_roles(self) -> None:
        """Seed roles from base YAML (wrapper for seed_entity)."""
        await self.seed_entity('roles')
    
    async def seed_user_roles(self) -> None:
        """Create user-role associations from overlay."""
        logger.info("Seeding user-role associations...")
        
        result = await self.session.execute(
            select(UserRoleDO).where(
                UserRoleDO.user_id == 1,
                UserRoleDO.role_id == 1
            )
        )
        if result.scalar_one_or_none():
            logger.info("User-role associations already exist, skipping")
            return
        
        overlay = self.load_overlay()
        user_roles = overlay.get('user_roles', [])
        
        count = 0
        for ur in user_roles:
            self.session.add(UserRoleDO(
                user_id=ur['user_id'],
                role_id=ur['role_id']
            ))
            count += 1
        
        await self.session.flush()
        logger.info(f"Created {count} user-role associations")
    
    async def seed_user_posts(self) -> None:
        """Create user-post associations from overlay."""
        logger.info("Seeding user-post associations...")
        
        result = await self.session.execute(
            select(UserPostDO).where(
                UserPostDO.user_id == 1,
                UserPostDO.post_id == 1
            )
        )
        if result.scalar_one_or_none():
            logger.info("User-post associations already exist, skipping")
            return
        
        overlay = self.load_overlay()
        user_posts = overlay.get('user_posts', [])
        
        count = 0
        for up in user_posts:
            self.session.add(UserPostDO(
                user_id=up['user_id'],
                post_id=up['post_id']
            ))
            count += 1
        
        await self.session.flush()
        logger.info(f"Created {count} user-post associations")
    
    async def seed_role_menus(self) -> None:
        """
        Create role-menu associations from overlay.
        
        Supports both flat menu_ids list and expanded format.
        """
        logger.info("Seeding role-menu associations...")
        
        result = await self.session.execute(
            select(RoleMenuDO).where(RoleMenuDO.role_id == 2)
        )
        if result.scalar_one_or_none():
            logger.info("Role-menu associations already exist, skipping")
            return
        
        overlay = self.load_overlay()
        role_menus = overlay.get('role_menus', [])
        
        count = 0
        for rm in role_menus:
            role_id = rm['role_id']
            menu_ids = rm.get('menu_ids', [])
            
            for menu_id in menu_ids:
                self.session.add(RoleMenuDO(
                    role_id=role_id,
                    menu_id=menu_id
                ))
                count += 1
        
        await self.session.flush()
        logger.info(f"Created {count} role-menu associations")
    
    async def seed_role_depts(self) -> None:
        """Create role-dept associations from overlay."""
        logger.info("Seeding role-dept associations...")
        
        result = await self.session.execute(
            select(RoleDeptDO).where(RoleDeptDO.role_id == 2)
        )
        if result.scalar_one_or_none():
            logger.info("Role-dept associations already exist, skipping")
            return
        
        overlay = self.load_overlay()
        role_depts = overlay.get('role_depts', [])
        
        count = 0
        for rd in role_depts:
            role_id = rd['role_id']
            dept_ids = rd.get('dept_ids', [])
            
            for dept_id in dept_ids:
                self.session.add(RoleDeptDO(
                    role_id=role_id,
                    dept_id=dept_id
                ))
                count += 1
        
        await self.session.flush()
        logger.info(f"Created {count} role-dept associations")
    
    async def clear_data(self) -> None:
        """
        Clear all seed data from database.
        
        Deletes data in reverse dependency order to respect foreign key constraints.
        Used for reset functionality.
        
        Warning: This is a destructive operation!
        """
        logger.warning("Clearing existing seed data...")
        
        # Delete in reverse dependency order
        # 1. Relationship tables first
        await self.session.execute(delete(UserRoleDO))
        await self.session.execute(delete(UserPostDO))
        await self.session.execute(delete(RoleMenuDO))
        await self.session.execute(delete(RoleDeptDO))
        logger.info("Cleared relationship tables")
        
        # 2. Dependent entities
        await self.session.execute(delete(UserDO))
        logger.info("Cleared users")
        
        # 3. Independent entities
        await self.session.execute(delete(RoleDO))
        await self.session.execute(delete(MenuDO))
        await self.session.execute(delete(DeptDO))
        await self.session.execute(delete(PostDO))
        await self.session.execute(delete(DictDataDO))
        await self.session.execute(delete(DictTypeDO))
        await self.session.execute(delete(ConfigDO))
        logger.info("Cleared independent entities")
        
        await self.session.flush()
        logger.info("All seed data cleared successfully")


async def main():
    """
    Main entry point for seed data script.
    
    Uses pre-parsed command line arguments.
    """
    logger.info(f"Starting seed data script with environment: {cli_args.env}")
    
    manager = SeedDataManager(env=cli_args.env)
    await manager.seed_all(reset=cli_args.reset)
    
    logger.info("Seed data script completed successfully")
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
