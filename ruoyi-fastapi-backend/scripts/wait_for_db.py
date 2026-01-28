#!/usr/bin/env python3
"""
Wait for database to be ready.

This script checks database connectivity with retries and timeout.
Used in Docker entrypoint to ensure database is available before migrations.

Usage:
    python scripts/wait_for_db.py
    python scripts/wait_for_db.py --max-retries 60 --delay 2
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set default environment if not set
if 'APP_ENV' not in os.environ:
    os.environ['APP_ENV'] = os.environ.get('ENV', 'dev')


async def wait_for_db(max_retries: int = 30, delay: int = 2) -> bool:
    """
    Wait for database connection to be ready.
    
    Args:
        max_retries: Maximum number of connection attempts
        delay: Seconds to wait between retries
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    # Import after setting environment
    from sqlalchemy import text
    from config.database import async_engine
    
    print(f"Waiting for database (max {max_retries} retries, {delay}s delay)...")
    
    for attempt in range(1, max_retries + 1):
        try:
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print(f"Database is ready! (attempt {attempt}/{max_retries})")
            return True
        except Exception as e:
            print(f"Attempt {attempt}/{max_retries}: Database not ready - {type(e).__name__}: {e}")
            if attempt < max_retries:
                await asyncio.sleep(delay)
    
    print(f"Failed to connect to database after {max_retries} attempts")
    return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Wait for database to be ready')
    parser.add_argument(
        '--max-retries',
        type=int,
        default=int(os.environ.get('DB_WAIT_MAX_RETRIES', 30)),
        help='Maximum number of connection attempts (default: 30)'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=int(os.environ.get('DB_WAIT_DELAY', 2)),
        help='Seconds to wait between retries (default: 2)'
    )
    
    args = parser.parse_args()
    
    result = asyncio.run(wait_for_db(
        max_retries=args.max_retries,
        delay=args.delay
    ))
    
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
