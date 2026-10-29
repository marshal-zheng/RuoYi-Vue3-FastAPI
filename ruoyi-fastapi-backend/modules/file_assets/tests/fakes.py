"""Fake storage with explicit failure injection (not evidence of real S3 behavior)."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from modules.file_assets.infrastructure.s3_storage import (
    CHUNK_SIZE,
    InstallationMarker,
    ListedObject,
    ListPage,
    ObjectMissingError,
    StorageError,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class _MemoryStream:
    def __init__(self, data: bytes):
        self._data = data
        self._offset = 0
        self.content_length = len(data)
        self.closed = False

    def read_chunk(self) -> bytes:
        chunk = self._data[self._offset : self._offset + CHUNK_SIZE]
        self._offset += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True


@dataclass
class FakeStorage:
    bucket: str = 'test-bucket'
    installation_id: str | None = 'test-installation'
    objects: dict[str, tuple[bytes, datetime]] = field(default_factory=dict)
    put_error: StorageError | None = None
    delete_errors: dict[str, StorageError] = field(default_factory=dict)
    delete_error_all: StorageError | None = None
    marker_error: StorageError | None = None
    before_put: Callable[[str], None] | None = None
    calls: list[tuple[str, str]] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def put(self, key: str, path: Path, size: int, media_type: str) -> None:
        self.calls.append(('put', key))
        if self.before_put is not None:
            self.before_put(key)
        if self.put_error is not None:
            raise self.put_error
        data = path.read_bytes()
        assert len(data) == size
        with self.lock:
            self.objects[key] = (data, datetime.now(UTC).replace(tzinfo=None))

    def open(self, key: str) -> _MemoryStream:
        self.calls.append(('open', key))
        with self.lock:
            if key not in self.objects:
                raise ObjectMissingError('get_object')
            return _MemoryStream(self.objects[key][0])

    def list(self, prefix: str, start_after: str | None, limit: int) -> ListPage:
        self.calls.append(('list', prefix))
        with self.lock:
            keys = sorted(
                key for key in self.objects if key.startswith(prefix) and (start_after is None or key > start_after)
            )
            page = keys[:limit]
            objects = tuple(ListedObject(key, len(self.objects[key][0]), self.objects[key][1]) for key in page)
        truncated = len(keys) > limit
        return ListPage(objects, truncated, page[-1] if truncated and page else None)

    def delete(self, key: str) -> None:
        self.calls.append(('delete', key))
        if self.delete_error_all is not None:
            raise self.delete_error_all
        if key in self.delete_errors:
            raise self.delete_errors[key]
        with self.lock:
            self.objects.pop(key, None)

    def read_installation_marker(self) -> InstallationMarker:
        if self.marker_error is not None:
            raise self.marker_error
        if self.installation_id is None:
            raise ObjectMissingError('get_installation_marker')
        return InstallationMarker(self.installation_id, None)

    def write_installation_marker(self, installation_id: str) -> None:
        self.installation_id = installation_id

    def age(self, key: str, when: datetime) -> None:
        with self.lock:
            data, _ = self.objects[key]
            self.objects[key] = (data, when)
