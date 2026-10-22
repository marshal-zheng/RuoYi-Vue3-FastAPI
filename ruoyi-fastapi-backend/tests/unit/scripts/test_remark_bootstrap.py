from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from common.remark_document_v1 import plain_to_remark
from scripts.internal.bootstrap_seed import PwdUtil, SeedDataManager


@pytest.mark.asyncio
async def test_overlay_user_remark_is_explicitly_compiled_without_mutating_source(monkeypatch):
    manager = SeedDataManager()
    source = {'user_id': 9, 'user_name': 'sample', 'password': 'example', 'remark': '中文\n尾 '}
    manager._overlay_data = {'users': [source.copy()]}
    added = []
    manager.session = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None)),
        flush=AsyncMock(),
        add=added.append,
    )
    monkeypatch.setattr(PwdUtil, 'get_password_hash', lambda value: 'hash:' + value)
    await manager.seed_users()
    assert added[0].remark == plain_to_remark(source['remark'], identity_key='sys_user:9:remark')
    assert manager._overlay_data == {'users': [source]}
