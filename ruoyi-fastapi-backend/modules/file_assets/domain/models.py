"""File asset domain values: states, ownership, purposes and stable references."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

CONTENT_PATH_PREFIX = '/file-assets/'
OBJECT_KEY_PREFIX = 'assets/'
META_PREFIX = '_meta/'
INSTALLATION_MARKER_KEY = '_meta/installation.json'

_UUID_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
_OBJECT_KEY_RE = re.compile(
    r'assets/(\d{4})/(0[1-9]|1[0-2])/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
)


class AssetState(StrEnum):
    UPLOADING = 'UPLOADING'
    READY = 'READY'
    FAILED = 'FAILED'
    DELETING = 'DELETING'
    DELETED = 'DELETED'


class AssetKind(StrEnum):
    IMAGE = 'image'
    FILE = 'file'


class ImageProfile(StrEnum):
    """How an image purpose re-encodes accepted pixels before storage."""

    STANDARD = 'standard'
    AVATAR = 'avatar'


class UploadEntry(StrEnum):
    """Which HTTP entry may create drafts for a purpose."""

    GENERIC = 'generic'
    DEDICATED = 'dedicated'


def normalize_asset_id(value: object) -> str | None:
    """Return the canonical lowercase UUID string, or None for anything else."""
    if not isinstance(value, str):
        return None
    candidate = value.strip().lower()
    if not _UUID_RE.fullmatch(candidate):
        return None
    try:
        return str(uuid.UUID(candidate))
    except ValueError:
        return None


def new_asset_id() -> str:
    return str(uuid.uuid4())


def object_key_for(asset_id: str, created_at: datetime) -> str:
    """Immutable key `assets/YYYY/MM/<asset_id>`; month taken from the UTC creation time."""
    return f'{OBJECT_KEY_PREFIX}{created_at.year:04d}/{created_at.month:02d}/{asset_id}'


def parse_object_key(key: str) -> str | None:
    """Return the asset id for a key in this system's exact format, otherwise None."""
    match = _OBJECT_KEY_RE.fullmatch(key)
    if not match:
        return None
    return normalize_asset_id(match.group(3))


def month_prefix(moment: datetime) -> str:
    return f'{OBJECT_KEY_PREFIX}{moment.year:04d}/{moment.month:02d}/'


def content_url(asset_id: str) -> str:
    return f'{CONTENT_PATH_PREFIX}{asset_id}/content'


def normalize_owner_id(value: object) -> str:
    """Owner ids are stored as canonical strings (`1`, never `01`)."""
    if isinstance(value, bool):
        raise ValueError('owner id must not be boolean')
    if isinstance(value, int):
        return str(value)
    text = str(value).strip()
    if text.isdigit():
        return str(int(text))
    if not text or len(text) > 128 or not re.fullmatch(r'[A-Za-z0-9_.:-]+', text):
        raise ValueError('owner id is not a canonical identifier')
    return text


@dataclass(frozen=True)
class OwnerRef:
    owner_type: str
    owner_id: str

    @classmethod
    def of(cls, owner_type: str, owner_id: object) -> OwnerRef:
        return cls(owner_type=owner_type, owner_id=normalize_owner_id(owner_id))


@dataclass(frozen=True)
class PurposeSpec:
    """A statically registered upload purpose and the single business field it feeds."""

    purpose: str
    owner_type: str
    field_key: str
    kind: AssetKind
    allowed_type_ids: tuple[str, ...]
    max_bytes: int
    max_count: int
    upload_entry: UploadEntry = UploadEntry.GENERIC
    image_profile: ImageProfile | None = None
    # Owner context of a draft: create permission when owner id is absent, edit permission otherwise.
    create_permission: str | None = None
    edit_permission: str | None = None

    @property
    def inline(self) -> bool:
        """Only server re-encoded images of an image purpose are served inline."""
        return self.kind is AssetKind.IMAGE


@dataclass(frozen=True)
class AssetDescriptor:
    asset_id: str
    name: str
    media_type: str
    size: int

    @property
    def content_url(self) -> str:
        return content_url(self.asset_id)

    def to_payload(self) -> dict[str, object]:
        return {
            'assetId': self.asset_id,
            'name': self.name,
            'mediaType': self.media_type,
            'size': self.size,
            'contentUrl': self.content_url,
        }


@dataclass(frozen=True)
class Actor:
    """The immutable authorization snapshot of the current principal."""

    user_id: int
    permissions: frozenset[str] = field(default_factory=frozenset)
    is_admin: bool = False

    def has_permission(self, permission: str | None) -> bool:
        if permission is None:
            return True
        return '*:*:*' in self.permissions or permission in self.permissions

    @classmethod
    def from_current_user(cls, current_user: object) -> Actor:
        user = getattr(current_user, 'user', None)
        user_id = getattr(user, 'user_id', None)
        if user_id is None:
            raise ValueError('current user has no id')
        permissions = frozenset(str(item) for item in (getattr(current_user, 'permissions', None) or []))
        return cls(user_id=int(user_id), permissions=permissions, is_admin=bool(getattr(user, 'admin', False)))
