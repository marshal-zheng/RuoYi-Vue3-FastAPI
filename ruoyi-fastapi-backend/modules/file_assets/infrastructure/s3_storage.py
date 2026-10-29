"""Blocking S3-compatible storage adapter; callers run every method inside a bounded worker pool.

Only basic S3 operations are used so the production distribution stays a deployment decision.
Errors are classified and sanitized here; credentials, hosts and raw provider messages never escape.
"""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from modules.file_assets.domain.models import INSTALLATION_MARKER_KEY

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

CHUNK_SIZE = 64 * 1024

# (connect timeout, read timeout, total attempts including the first), standard retry mode.
DATA_CLIENT_LIMITS = (3, 30, 3)
MAINTENANCE_CLIENT_LIMITS = (3, 10, 2)
OWNERSHIP_CLIENT_LIMITS = (3, 3, 1)


class StorageError(Exception):
    """Sanitized storage failure; `code` is a short provider-independent label."""

    def __init__(self, code: str, operation: str):
        super().__init__(f'{operation}:{code}')
        self.code = code
        self.operation = operation


class StorageUnavailableError(StorageError):
    """Connection failure, timeout or 5xx; `connection_level` marks an unreachable endpoint."""

    def __init__(self, code: str, operation: str, *, connection_level: bool = False):
        super().__init__(code, operation)
        self.connection_level = connection_level


class StorageObjectError(StorageError):
    """A 4xx other than not-found, e.g. AccessDenied; tied to the request or the object."""

    def __init__(self, code: str, operation: str, *, status: int | None = None):
        super().__init__(code, operation)
        self.status = status


class ObjectMissingError(StorageError):
    def __init__(self, operation: str):
        super().__init__('NoSuchKey', operation)


@dataclass(frozen=True)
class ListedObject:
    key: str
    size: int
    last_modified: datetime  # naive UTC


@dataclass(frozen=True)
class ListPage:
    objects: tuple[ListedObject, ...]
    is_truncated: bool
    next_start_after: str | None


@dataclass(frozen=True)
class InstallationMarker:
    installation_id: str
    created_at: str | None


class ObjectStream(Protocol):
    content_length: int

    def read_chunk(self) -> bytes: ...

    def close(self) -> None: ...


class ObjectStorage(Protocol):
    bucket: str

    def put(self, key: str, path: Path, size: int, media_type: str) -> None: ...

    def open(self, key: str) -> ObjectStream: ...

    def list(self, prefix: str, start_after: str | None, limit: int) -> ListPage: ...

    def delete(self, key: str) -> None: ...

    def read_installation_marker(self) -> InstallationMarker: ...

    def write_installation_marker(self, installation_id: str) -> None: ...


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value


class _BotoObjectStream:
    def __init__(self, body, content_length: int):
        self._body = body
        self.content_length = content_length

    def read_chunk(self) -> bytes:
        try:
            return self._body.read(CHUNK_SIZE)
        except Exception as exc:  # urllib3/botocore read errors mid-stream
            raise StorageUnavailableError(type(exc).__name__, 'get_object.read') from None

    def close(self) -> None:
        # Closing a broken stream must not mask the original outcome.
        with contextlib.suppress(Exception):
            self._body.close()


class S3ObjectStorage:
    """Boto3 client trio (data, maintenance, ownership) bound to one backend-only endpoint."""

    def __init__(
        self,
        *,
        endpoint: str,
        bucket: str,
        region: str,
        addressing_style: str,
        access_key: str,
        secret_key: str,
        max_pool_connections: int,
    ):
        self.bucket = bucket
        session = boto3.session.Session()

        def client(limits: tuple[int, int, int], pool: int):
            connect_timeout, read_timeout, attempts = limits
            return session.client(
                's3',
                endpoint_url=endpoint,
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=Config(
                    signature_version='s3v4',
                    s3={'addressing_style': addressing_style},
                    connect_timeout=connect_timeout,
                    read_timeout=read_timeout,
                    retries={'mode': 'standard', 'total_max_attempts': attempts},
                    max_pool_connections=pool,
                    # Integrity is the server-side SHA-256 we record; avoid optional checksum headers
                    # that S3-compatible implementations support unevenly.
                    request_checksum_calculation='when_required',
                    response_checksum_validation='when_required',
                    user_agent_extra='ruoyi-file-assets',
                ),
            )

        self._data = client(DATA_CLIENT_LIMITS, max_pool_connections)
        self._maintenance = client(MAINTENANCE_CLIENT_LIMITS, max(2, max_pool_connections // 4))
        self._ownership = client(OWNERSHIP_CLIENT_LIMITS, 2)

    # -- error mapping ------------------------------------------------------------

    @staticmethod
    def _classify(exc: Exception, operation: str) -> StorageError:  # noqa: PLR0911 - one outcome per error class
        if isinstance(exc, ClientError):
            error = exc.response.get('Error', {})
            code = str(error.get('Code') or 'ClientError')[:64]
            status = int(exc.response.get('ResponseMetadata', {}).get('HTTPStatusCode') or 0)
            if code == 'NoSuchBucket':
                # A missing bucket is a configuration fault, never "the object is already gone".
                return StorageObjectError(code, operation, status=status or 404)
            if status == 404 or code in {'NoSuchKey', 'NotFound', '404'}:
                return ObjectMissingError(operation)
            if status >= 500 or code in {'SlowDown', 'ServiceUnavailable', 'InternalError'}:
                return StorageUnavailableError(code, operation)
            return StorageObjectError(code, operation, status=status or None)
        if isinstance(exc, (EndpointConnectionError, ConnectTimeoutError)):
            return StorageUnavailableError(type(exc).__name__, operation, connection_level=True)
        if isinstance(exc, (ReadTimeoutError, ConnectionClosedError)):
            return StorageUnavailableError(type(exc).__name__, operation)
        return StorageUnavailableError(type(exc).__name__, operation)

    # -- data operations ------------------------------------------------------------

    def put(self, key: str, path: Path, size: int, media_type: str) -> None:
        try:
            with path.open('rb') as body:
                # A single PUT; the transfer manager (threads, multipart) is deliberately not used.
                self._data.put_object(
                    Bucket=self.bucket, Key=key, Body=body, ContentLength=size, ContentType=media_type
                )
        except Exception as exc:
            raise self._classify(exc, 'put_object') from None

    def open(self, key: str) -> ObjectStream:
        try:
            response = self._data.get_object(Bucket=self.bucket, Key=key)
        except Exception as exc:
            raise self._classify(exc, 'get_object') from None
        return _BotoObjectStream(response['Body'], int(response.get('ContentLength') or 0))

    def iter_bytes(self, key: str) -> Iterator[bytes]:
        stream = self.open(key)
        try:
            while chunk := stream.read_chunk():
                yield chunk
        finally:
            stream.close()

    # -- maintenance operations --------------------------------------------------------

    def list(self, prefix: str, start_after: str | None, limit: int) -> ListPage:
        params = {'Bucket': self.bucket, 'Prefix': prefix, 'MaxKeys': max(1, min(limit, 1000))}
        if start_after:
            params['StartAfter'] = start_after
        try:
            response = self._maintenance.list_objects_v2(**params)
        except Exception as exc:
            raise self._classify(exc, 'list_objects_v2') from None
        objects = tuple(
            ListedObject(
                key=item['Key'], size=int(item.get('Size') or 0), last_modified=_naive_utc(item['LastModified'])
            )
            for item in response.get('Contents', [])
        )
        truncated = bool(response.get('IsTruncated'))
        return ListPage(objects, truncated, objects[-1].key if truncated and objects else None)

    def delete(self, key: str) -> None:
        try:
            # S3 answers 204 for a missing key as well; deleting twice is idempotent success.
            self._maintenance.delete_object(Bucket=self.bucket, Key=key)
        except Exception as exc:
            error = self._classify(exc, 'delete_object')
            if isinstance(error, ObjectMissingError):
                return
            raise error from None

    # -- ownership marker ---------------------------------------------------------------------

    def read_installation_marker(self) -> InstallationMarker:
        try:
            response = self._ownership.get_object(Bucket=self.bucket, Key=INSTALLATION_MARKER_KEY)
            raw = response['Body'].read(4096)
        except Exception as exc:
            raise self._classify(exc, 'get_installation_marker') from None
        try:
            payload = json.loads(raw.decode('utf-8'))
            return InstallationMarker(str(payload['installationId']), payload.get('createdAt'))
        except (ValueError, KeyError, TypeError, UnicodeDecodeError):
            return InstallationMarker('', None)

    def write_installation_marker(self, installation_id: str) -> None:
        body = json.dumps(
            {'installationId': installation_id, 'createdAt': datetime.now(UTC).isoformat()}, ensure_ascii=True
        ).encode('ascii')
        try:
            self._maintenance.put_object(
                Bucket=self.bucket, Key=INSTALLATION_MARKER_KEY, Body=body, ContentType='application/json'
            )
        except Exception as exc:
            raise self._classify(exc, 'put_installation_marker') from None

    def head_bucket(self) -> None:
        try:
            self._maintenance.head_bucket(Bucket=self.bucket)
        except Exception as exc:
            raise self._classify(exc, 'head_bucket') from None
