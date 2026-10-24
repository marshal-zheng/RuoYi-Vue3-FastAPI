"""Test-only fallback for `aiosqlite` used by SQLAlchemy async sqlite tests."""

from __future__ import annotations

import sqlite3
from typing import Any

DatabaseError = sqlite3.DatabaseError
Error = sqlite3.Error
IntegrityError = sqlite3.IntegrityError
NotSupportedError = sqlite3.NotSupportedError
OperationalError = sqlite3.OperationalError
ProgrammingError = sqlite3.ProgrammingError
sqlite_version = sqlite3.sqlite_version
sqlite_version_info = sqlite3.sqlite_version_info


class _TxQueue:
    def put_nowait(self, item: tuple[Any, Any]) -> None:
        future, fn = item
        try:
            result = fn()
        except Exception as exc:  # pragma: no cover - defensive
            future.set_exception(exc)
        else:
            future.set_result(result)


class Cursor:
    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    @property
    def description(self):
        return self._cursor.description

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    async def execute(self, operation: str, parameters: Any = None) -> 'Cursor':
        if parameters is None:
            self._cursor.execute(operation)
        else:
            self._cursor.execute(operation, parameters)
        return self

    async def executemany(self, operation: str, seq_of_parameters: Any) -> 'Cursor':
        self._cursor.executemany(operation, seq_of_parameters)
        return self

    async def fetchall(self):
        return self._cursor.fetchall()

    async def fetchone(self):
        return self._cursor.fetchone()

    async def fetchmany(self, size: int | None = None):
        return self._cursor.fetchmany(size or self._cursor.arraysize)

    async def close(self) -> None:
        self._cursor.close()


class Connection:
    def __init__(self, database: str, *args, **kwargs):
        self._conn = sqlite3.connect(database, *args, **kwargs)
        self._tx = _TxQueue()
        self.daemon = False

    def __await__(self):
        async def _return_self():
            return self

        return _return_self().__await__()

    @property
    def isolation_level(self):
        return self._conn.isolation_level

    @isolation_level.setter
    def isolation_level(self, value):
        self._conn.isolation_level = value

    async def cursor(self) -> Cursor:
        return Cursor(self._conn.cursor())

    async def execute(self, *args, **kwargs) -> Cursor:
        cursor = self._conn.cursor()
        if args:
            if len(args) > 1:
                cursor.execute(args[0], args[1])
            else:
                cursor.execute(args[0])
        elif kwargs:
            statement = kwargs.get('sql') or kwargs.get('statement')
            parameters = kwargs.get('parameters')
            if parameters is None:
                cursor.execute(statement)
            else:
                cursor.execute(statement, parameters)
        return Cursor(cursor)

    async def rollback(self) -> None:
        self._conn.rollback()

    async def commit(self) -> None:
        self._conn.commit()

    async def close(self) -> None:
        self._conn.close()

    async def create_function(self, *args, **kwargs) -> None:
        self._conn.create_function(*args, **kwargs)


def connect(*args, **kwargs) -> Connection:
    return Connection(*args, **kwargs)
