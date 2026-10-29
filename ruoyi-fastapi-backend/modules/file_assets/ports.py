"""Cross-context contract of the file asset context.

Business contexts implement owner policies, bind inside their own transactions and project
descriptors through these names only; they never import this context's infrastructure.
"""

from __future__ import annotations

from modules.file_assets.application.composition import (
    get_binding_service,
    get_file_asset_services,
    peek_file_asset_services,
)
from modules.file_assets.application.policies import AssetOwnerPolicy, PermissionOwnerPolicy
from modules.file_assets.domain.errors import (
    AssetConflictError,
    AssetInvalidError,
    AssetNotFoundError,
    AssetPermissionDeniedError,
    FileAssetError,
    FileAssetsUnavailableError,
)
from modules.file_assets.domain.models import (
    CONTENT_PATH_PREFIX,
    Actor,
    AssetDescriptor,
    AssetKind,
    ImageProfile,
    OwnerRef,
    PurposeSpec,
    UploadEntry,
    content_url,
    normalize_asset_id,
)
from modules.file_assets.domain.types import (
    IMAGE_TYPE_IDS,
    MAX_ATTACHMENT_BYTES,
    MAX_IMAGE_BYTES,
    OFFICE_BASELINE_TYPE_IDS,
    accept_attribute,
    validate_type_ids,
)

__all__ = [
    'CONTENT_PATH_PREFIX',
    'IMAGE_TYPE_IDS',
    'MAX_ATTACHMENT_BYTES',
    'MAX_IMAGE_BYTES',
    'OFFICE_BASELINE_TYPE_IDS',
    'Actor',
    'AssetConflictError',
    'AssetDescriptor',
    'AssetInvalidError',
    'AssetKind',
    'AssetNotFoundError',
    'AssetOwnerPolicy',
    'AssetPermissionDeniedError',
    'FileAssetError',
    'FileAssetsUnavailableError',
    'ImageProfile',
    'OwnerRef',
    'PermissionOwnerPolicy',
    'PurposeSpec',
    'UploadEntry',
    'accept_attribute',
    'content_url',
    'get_binding_service',
    'get_file_asset_services',
    'normalize_asset_id',
    'peek_file_asset_services',
    'validate_type_ids',
]
