"""
Unit tests for seed data management.

Tests verify that seed_users(), seed_roles(), and seed_user_roles() methods
work correctly with proper idempotency and data integrity.
"""

import pytest
import asyncio
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Import the seed data manager
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.seed_data import SeedDataManager
from module_admin.entity.do.user_do import SysUser, SysUserRole
from module_admin.entity.do.role_do import SysRole
from utils.pwd_util import PwdUtil


# Test database URL (using SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    """Create a test database session."""
    # Create async engine for test database
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    from module_admin.entity.do.base import LegacyBaseModel
    async with engine.begin() as conn:
        await conn.run_sync(LegacyBaseModel.metadata.create_all)
    
    # Create session factory
    TestSessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def seed_manager(test_db):
    """Create a seed data manager with test database session."""
    manager = SeedDataManager(env='dev')
    manager.session = test_db
    return manager


class TestSeedUsers:
    """Test suite for seed_users() method."""
    
    @pytest.mark.asyncio
    async def test_seed_users_creates_admin(self, seed_manager, test_db):
        """Test that seed_users creates admin user with correct attributes."""
        # Execute seed_users
        await seed_manager.seed_users()
        await test_db.commit()
        
        # Verify admin user was created
        result = await test_db.execute(
            select(SysUser).where(SysUser.user_name == 'admin')
        )
        admin = result.scalar_one_or_none()
        
        assert admin is not None, "Admin user should be created"
        assert admin.user_name == 'admin'
        assert admin.nick_name == '超级管理员'
        assert admin.email == 'admin@example.com'
        assert admin.phonenumber == '15888888888'
        assert admin.status == '0'
        assert admin.del_flag == '0'
        
        # Verify password is hashed
        assert admin.password != 'admin123', "Password should be hashed"
        assert len(admin.password) > 20, "Hashed password should be long"
        
        # Verify password can be verified
        assert PwdUtil.verify_password('admin123', admin.password), \
            "Password should be verifiable with correct password"
        assert not PwdUtil.verify_password('wrongpassword', admin.password), \
            "Password should not verify with wrong password"
    
    @pytest.mark.asyncio
    async def test_seed_users_creates_test_user_in_dev(self, seed_manager, test_db):
        """Test that seed_users creates test user in dev environment."""
        # Execute seed_users
        await seed_manager.seed_users()
        await test_db.commit()
        
        # Verify test user was created (dev environment)
        result = await test_db.execute(
            select(SysUser).where(SysUser.user_name == 'niangao')
        )
        test_user = result.scalar_one_or_none()
        
        assert test_user is not None, "Test user should be created in dev environment"
        assert test_user.user_name == 'niangao'
        assert test_user.nick_name == '年糕'
    
    @pytest.mark.asyncio
    async def test_seed_users_idempotency(self, seed_manager, test_db):
        """Test that seed_users is idempotent (can be run multiple times)."""
        # Execute seed_users twice
        await seed_manager.seed_users()
        await test_db.commit()
        
        # Count users before second run
        result = await test_db.execute(select(SysUser))
        users_before = len(result.scalars().all())
        
        # Run again
        await seed_manager.seed_users()
        await test_db.commit()
        
        # Count users after second run
        result = await test_db.execute(select(SysUser))
        users_after = len(result.scalars().all())
        
        assert users_before == users_after, \
            "Running seed_users twice should not create duplicate users"


class TestSeedRoles:
    """Test suite for seed_roles() method."""
    
    @pytest.mark.asyncio
    async def test_seed_roles_creates_admin_role(self, seed_manager, test_db):
        """Test that seed_roles creates admin role with correct attributes."""
        # Execute seed_roles
        await seed_manager.seed_roles()
        await test_db.commit()
        
        # Verify admin role was created
        result = await test_db.execute(
            select(SysRole).where(SysRole.role_key == 'admin')
        )
        admin_role = result.scalar_one_or_none()
        
        assert admin_role is not None, "Admin role should be created"
        assert admin_role.role_name == '超级管理员'
        assert admin_role.role_key == 'admin'
        assert admin_role.role_sort == 1
        assert admin_role.data_scope == '1'
        assert admin_role.status == '0'
        assert admin_role.del_flag == '0'
    
    @pytest.mark.asyncio
    async def test_seed_roles_creates_common_role(self, seed_manager, test_db):
        """Test that seed_roles creates common user role."""
        # Execute seed_roles
        await seed_manager.seed_roles()
        await test_db.commit()
        
        # Verify common role was created
        result = await test_db.execute(
            select(SysRole).where(SysRole.role_key == 'common')
        )
        common_role = result.scalar_one_or_none()
        
        assert common_role is not None, "Common role should be created"
        assert common_role.role_name == '普通角色'
        assert common_role.role_key == 'common'
        assert common_role.role_sort == 2
        assert common_role.status == '0'
    
    @pytest.mark.asyncio
    async def test_seed_roles_idempotency(self, seed_manager, test_db):
        """Test that seed_roles is idempotent."""
        # Execute seed_roles twice
        await seed_manager.seed_roles()
        await test_db.commit()
        
        # Count roles before second run
        result = await test_db.execute(select(SysRole))
        roles_before = len(result.scalars().all())
        
        # Run again
        await seed_manager.seed_roles()
        await test_db.commit()
        
        # Count roles after second run
        result = await test_db.execute(select(SysRole))
        roles_after = len(result.scalars().all())
        
        assert roles_before == roles_after, \
            "Running seed_roles twice should not create duplicate roles"


class TestSeedUserRoles:
    """Test suite for seed_user_roles() method."""
    
    @pytest.mark.asyncio
    async def test_seed_user_roles_assigns_admin_role(self, seed_manager, test_db):
        """Test that seed_user_roles assigns admin role to admin user."""
        # First create users and roles
        await seed_manager.seed_users()
        await seed_manager.seed_roles()
        await test_db.commit()
        
        # Execute seed_user_roles
        await seed_manager.seed_user_roles()
        await test_db.commit()
        
        # Verify admin user has admin role
        result = await test_db.execute(
            select(SysUserRole).where(
                SysUserRole.user_id == 1,
                SysUserRole.role_id == 1
            )
        )
        user_role = result.scalar_one_or_none()
        
        assert user_role is not None, "Admin user should have admin role"
        assert user_role.user_id == 1
        assert user_role.role_id == 1
    
    @pytest.mark.asyncio
    async def test_seed_user_roles_assigns_test_user_role_in_dev(self, seed_manager, test_db):
        """Test that seed_user_roles assigns common role to test user in dev."""
        # First create users and roles
        await seed_manager.seed_users()
        await seed_manager.seed_roles()
        await test_db.commit()
        
        # Execute seed_user_roles
        await seed_manager.seed_user_roles()
        await test_db.commit()
        
        # Verify test user has common role (dev environment)
        result = await test_db.execute(
            select(SysUserRole).where(
                SysUserRole.user_id == 2,
                SysUserRole.role_id == 2
            )
        )
        user_role = result.scalar_one_or_none()
        
        assert user_role is not None, "Test user should have common role in dev"
        assert user_role.user_id == 2
        assert user_role.role_id == 2
    
    @pytest.mark.asyncio
    async def test_seed_user_roles_idempotency(self, seed_manager, test_db):
        """Test that seed_user_roles is idempotent."""
        # First create users and roles
        await seed_manager.seed_users()
        await seed_manager.seed_roles()
        await test_db.commit()
        
        # Execute seed_user_roles twice
        await seed_manager.seed_user_roles()
        await test_db.commit()
        
        # Count associations before second run
        result = await test_db.execute(select(SysUserRole))
        associations_before = len(result.scalars().all())
        
        # Run again
        await seed_manager.seed_user_roles()
        await test_db.commit()
        
        # Count associations after second run
        result = await test_db.execute(select(SysUserRole))
        associations_after = len(result.scalars().all())
        
        assert associations_before == associations_after, \
            "Running seed_user_roles twice should not create duplicate associations"


class TestIntegration:
    """Integration tests for complete seeding workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_user_role_workflow(self, seed_manager, test_db):
        """Test complete workflow: users -> roles -> user_roles."""
        # Execute all seeding operations in order
        await seed_manager.seed_roles()
        await seed_manager.seed_users()
        await seed_manager.seed_user_roles()
        await test_db.commit()
        
        # Verify admin user exists
        result = await test_db.execute(
            select(SysUser).where(SysUser.user_name == 'admin')
        )
        admin = result.scalar_one()
        assert admin is not None
        
        # Verify admin role exists
        result = await test_db.execute(
            select(SysRole).where(SysRole.role_key == 'admin')
        )
        admin_role = result.scalar_one()
        assert admin_role is not None
        
        # Verify admin user has admin role
        result = await test_db.execute(
            select(SysUserRole).where(
                SysUserRole.user_id == admin.user_id,
                SysUserRole.role_id == admin_role.role_id
            )
        )
        user_role = result.scalar_one()
        assert user_role is not None
    
    @pytest.mark.asyncio
    async def test_idempotency_across_all_methods(self, seed_manager, test_db):
        """Test that all methods are idempotent when run together."""
        # Run all seeding operations twice
        for _ in range(2):
            await seed_manager.seed_roles()
            await seed_manager.seed_users()
            await seed_manager.seed_user_roles()
            await test_db.commit()
        
        # Count final records
        result = await test_db.execute(select(SysUser))
        users = result.scalars().all()
        
        result = await test_db.execute(select(SysRole))
        roles = result.scalars().all()
        
        result = await test_db.execute(select(SysUserRole))
        user_roles = result.scalars().all()
        
        # In dev environment, should have 2 users, 2 roles, 2 associations
        assert len(users) == 2, "Should have exactly 2 users"
        assert len(roles) == 2, "Should have exactly 2 roles"
        assert len(user_roles) == 2, "Should have exactly 2 user-role associations"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
