from __future__ import annotations

import pytest

from config import get_db as get_db_module


class _FakeBeginConnection:
    def __init__(self) -> None:
        self.run_sync_calls: list[object] = []

    async def run_sync(self, fn):
        self.run_sync_calls.append(fn)


class _FakeBeginContext:
    def __init__(self, connection: _FakeBeginConnection) -> None:
        self.connection = connection

    async def __aenter__(self) -> _FakeBeginConnection:
        return self.connection

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeBeginEngine:
    def __init__(self) -> None:
        self.connection = _FakeBeginConnection()

    def begin(self) -> _FakeBeginContext:
        return _FakeBeginContext(self.connection)


class _FakeConnectConnection:
    def __init__(self) -> None:
        self.executed: list[object] = []

    async def execute(self, statement):
        self.executed.append(statement)


class _FakeConnectContext:
    def __init__(self, connection: _FakeConnectConnection) -> None:
        self.connection = connection

    async def __aenter__(self) -> _FakeConnectConnection:
        return self.connection

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeConnectEngine:
    def __init__(self) -> None:
        self.connection = _FakeConnectConnection()

    def connect(self) -> _FakeConnectContext:
        return _FakeConnectContext(self.connection)


@pytest.mark.asyncio
async def test_init_create_table_creates_schema_in_test_env(monkeypatch) -> None:
    fake_engine = _FakeBeginEngine()

    monkeypatch.setattr(get_db_module, '_is_test_env', lambda: True)
    monkeypatch.setattr(get_db_module, '_get_test_engine', lambda: fake_engine)

    await get_db_module.init_create_table()

    assert fake_engine.connection.run_sync_calls == [get_db_module.Base.metadata.create_all]


@pytest.mark.asyncio
async def test_init_create_table_only_checks_connection_outside_test(monkeypatch) -> None:
    fake_engine = _FakeConnectEngine()

    monkeypatch.setattr(get_db_module, '_is_test_env', lambda: False)
    monkeypatch.setattr(get_db_module, 'async_engine', fake_engine)

    await get_db_module.init_create_table()

    assert len(fake_engine.connection.executed) == 1
    assert str(fake_engine.connection.executed[0]) == 'SELECT 1'
