"""
Migration testing script for RuoYi-FastAPI.

This script provides tools to test Alembic migrations for correctness,
including upgrade/downgrade cycles, idempotency, and schema comparison.

Usage:
    python scripts/test_migrations.py --test upgrade-downgrade
    python scripts/test_migrations.py --test idempotency
    python scripts/test_migrations.py --test all
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from utils.log_util import logger


class MigrationTester:
    """
    Test migration scripts for correctness.
    
    Provides methods to:
    - Test upgrade/downgrade cycles
    - Test idempotency (applying migrations multiple times)
    - Compare database schemas
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize migration tester.
        
        Args:
            database_url: Database URL for testing. If None, uses config.
        """
        self.project_dir = Path(__file__).parent.parent
        self.alembic_cfg = Config(str(self.project_dir / "alembic.ini"))
        
        if database_url:
            self.alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        self.database_url = database_url or self._get_database_url()
    
    def _get_database_url(self) -> str:
        """Get database URL from alembic config."""
        return self.alembic_cfg.get_main_option("sqlalchemy.url")
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine for schema inspection."""
        return create_engine(self.database_url)
    
    def get_current_revision(self) -> Optional[str]:
        """Get current database revision."""
        engine = self._create_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            )
            row = result.fetchone()
            return row[0] if row else None
    
    def get_table_names(self) -> set[str]:
        """Get all table names in database."""
        engine = self._create_engine()
        inspector = inspect(engine)
        return set(inspector.get_table_names())
    
    def get_schema_info(self) -> dict:
        """
        Get detailed schema information for comparison.
        
        Returns:
            Dictionary with tables, columns, indexes, and foreign keys.
        """
        engine = self._create_engine()
        inspector = inspect(engine)
        
        schema_info = {
            'tables': {},
            'indexes': {},
            'foreign_keys': {}
        }
        
        for table_name in inspector.get_table_names():
            # Get columns
            columns = inspector.get_columns(table_name)
            schema_info['tables'][table_name] = {
                col['name']: {
                    'type': str(col['type']),
                    'nullable': col.get('nullable', True),
                    'default': str(col.get('default')) if col.get('default') else None
                }
                for col in columns
            }
            
            # Get indexes
            indexes = inspector.get_indexes(table_name)
            schema_info['indexes'][table_name] = {
                idx['name']: {
                    'columns': idx['column_names'],
                    'unique': idx.get('unique', False)
                }
                for idx in indexes if idx['name']
            }
            
            # Get foreign keys
            fks = inspector.get_foreign_keys(table_name)
            schema_info['foreign_keys'][table_name] = [
                {
                    'columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns']
                }
                for fk in fks
            ]
        
        return schema_info
    
    def test_upgrade_downgrade(self) -> bool:
        """
        Test that migrations can upgrade and downgrade successfully.
        
        Returns:
            True if test passes, False otherwise.
        """
        logger.info("Testing upgrade/downgrade cycle...")
        
        # Get initial state
        initial_revision = self.get_current_revision()
        logger.info(f"Initial revision: {initial_revision or 'None'}")
        
        # Upgrade to head
        logger.info("Upgrading to head...")
        command.upgrade(self.alembic_cfg, "head")
        
        head_revision = self.get_current_revision()
        logger.info(f"Head revision: {head_revision}")
        
        if not head_revision:
            logger.error("No revision after upgrade")
            return False
        
        # Downgrade one step
        logger.info("Downgrading one step...")
        command.downgrade(self.alembic_cfg, "-1")
        
        after_downgrade = self.get_current_revision()
        logger.info(f"Revision after downgrade: {after_downgrade or 'None'}")
        
        # Upgrade back
        logger.info("Upgrading back to head...")
        command.upgrade(self.alembic_cfg, "head")
        
        final_revision = self.get_current_revision()
        logger.info(f"Final revision: {final_revision}")
        
        if final_revision != head_revision:
            logger.error(f"Final revision {final_revision} != head {head_revision}")
            return False
        
        logger.info("Upgrade/downgrade test PASSED")
        return True
    
    def test_idempotency(self) -> bool:
        """
        Test that migrations are idempotent.
        
        Applying migrations multiple times should produce the same result.
        
        Returns:
            True if test passes, False otherwise.
        """
        logger.info("Testing migration idempotency...")
        
        # Apply migrations first time
        logger.info("First upgrade to head...")
        command.upgrade(self.alembic_cfg, "head")
        
        schema_after_first = self.get_schema_info()
        revision_after_first = self.get_current_revision()
        
        # Apply migrations second time (should be no-op)
        logger.info("Second upgrade to head...")
        command.upgrade(self.alembic_cfg, "head")
        
        schema_after_second = self.get_schema_info()
        revision_after_second = self.get_current_revision()
        
        # Compare
        if revision_after_first != revision_after_second:
            logger.error("Revision changed after second upgrade")
            return False
        
        if schema_after_first != schema_after_second:
            logger.error("Schema changed after second upgrade")
            return False
        
        logger.info("Idempotency test PASSED")
        return True
    
    def compare_schemas(self, schema1: dict, schema2: dict) -> dict:
        """
        Compare two database schemas.
        
        Args:
            schema1: First schema (from get_schema_info())
            schema2: Second schema
            
        Returns:
            Dictionary with differences found.
        """
        differences = {
            'added_tables': [],
            'removed_tables': [],
            'modified_tables': [],
            'added_columns': {},
            'removed_columns': {},
            'modified_columns': {}
        }
        
        tables1 = set(schema1['tables'].keys())
        tables2 = set(schema2['tables'].keys())
        
        differences['added_tables'] = list(tables2 - tables1)
        differences['removed_tables'] = list(tables1 - tables2)
        
        # Compare common tables
        for table in tables1 & tables2:
            cols1 = set(schema1['tables'][table].keys())
            cols2 = set(schema2['tables'][table].keys())
            
            added = cols2 - cols1
            removed = cols1 - cols2
            
            if added:
                differences['added_columns'][table] = list(added)
            if removed:
                differences['removed_columns'][table] = list(removed)
            
            # Compare column definitions
            for col in cols1 & cols2:
                if schema1['tables'][table][col] != schema2['tables'][table][col]:
                    if table not in differences['modified_columns']:
                        differences['modified_columns'][table] = []
                    differences['modified_columns'][table].append(col)
        
        return differences
    
    def test_all(self) -> bool:
        """
        Run all migration tests.
        
        Returns:
            True if all tests pass, False otherwise.
        """
        logger.info("=" * 60)
        logger.info("Running all migration tests")
        logger.info("=" * 60)
        
        results = []
        
        # Test 1: Upgrade/Downgrade
        logger.info("")
        logger.info("-" * 40)
        results.append(("upgrade_downgrade", self.test_upgrade_downgrade()))
        
        # Test 2: Idempotency
        logger.info("")
        logger.info("-" * 40)
        results.append(("idempotency", self.test_idempotency()))
        
        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Test Results Summary")
        logger.info("=" * 60)
        
        all_passed = True
        for test_name, passed in results:
            status = "PASSED" if passed else "FAILED"
            logger.info(f"  {test_name}: {status}")
            if not passed:
                all_passed = False
        
        logger.info("")
        if all_passed:
            logger.info("All tests PASSED")
        else:
            logger.error("Some tests FAILED")
        
        return all_passed


def main():
    """Main entry point for migration testing."""
    parser = argparse.ArgumentParser(
        description='Test Alembic migrations for correctness'
    )
    parser.add_argument(
        '--test',
        type=str,
        choices=['upgrade-downgrade', 'idempotency', 'all'],
        default='all',
        help='Test to run (default: all)'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='Database URL for testing (uses config if not specified)'
    )
    
    args = parser.parse_args()
    
    tester = MigrationTester(database_url=args.database_url)
    
    if args.test == 'upgrade-downgrade':
        success = tester.test_upgrade_downgrade()
    elif args.test == 'idempotency':
        success = tester.test_idempotency()
    else:
        success = tester.test_all()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
