#!/usr/bin/env python3
"""Data migration runner for sensitive hash backfill."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.data_migrations.backfill_sensitive_hash import migrate


if __name__ == '__main__':
    asyncio.run(migrate())
