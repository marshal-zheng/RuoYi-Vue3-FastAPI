"""Owner policies: business modules own permissions and existence; this module owns the registry.

Policies are registered explicitly in code (no reflection, DSL or client-declared rules). An
unknown purpose or a missing policy is always a rejection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from modules.file_assets.domain.errors import AssetInvalidError, AssetNotFoundError, AssetPermissionDeniedError
from modules.file_assets.domain.types import FILE_TYPES, MAX_ATTACHMENT_BYTES, MAX_IMAGE_BYTES, TypeFamily

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.file_assets.domain.models import Actor, PurposeSpec


@runtime_checkable
class AssetOwnerPolicy(Protocol):
    owner_type: str
    purposes: tuple[PurposeSpec, ...]

    async def authorize_upload(
        self, session: AsyncSession, actor: Actor, purpose: PurposeSpec, owner_id: str | None
    ) -> None:
        """Raise unless the actor may currently create a draft for this purpose and owner context."""

    async def authorize_write(self, session: AsyncSession, actor: Actor, owner_id: str, *, creating: bool) -> None:
        """Raise unless the actor may change the owner's asset fields in the running business transaction."""

    async def readable_owner_ids(
        self, session: AsyncSession, actor: Actor, owner_ids: set[str], field_key: str
    ) -> set[str]:
        """Return the subset of owners whose `field_key` assets the actor may read (one batched check)."""


class PermissionOwnerPolicy:
    """Common shape: create/edit permissions from the purpose, plus an owner-existence lookup."""

    owner_type: str = ''
    purposes: tuple[PurposeSpec, ...] = ()

    async def existing_owner_ids(self, session: AsyncSession, owner_ids: set[str]) -> set[str]:
        raise NotImplementedError

    async def authorize_upload(
        self, session: AsyncSession, actor: Actor, purpose: PurposeSpec, owner_id: str | None
    ) -> None:
        if owner_id is None:
            if purpose.create_permission is None or not actor.has_permission(purpose.create_permission):
                raise AssetPermissionDeniedError()
            return
        if purpose.edit_permission is None or not actor.has_permission(purpose.edit_permission):
            raise AssetPermissionDeniedError()
        if owner_id not in await self.existing_owner_ids(session, {owner_id}):
            raise AssetNotFoundError('OWNER_NOT_FOUND', user_message='关联的业务数据不存在')

    async def authorize_write(self, session: AsyncSession, actor: Actor, owner_id: str, *, creating: bool) -> None:
        permissions = {spec.create_permission if creating else spec.edit_permission for spec in self.purposes}
        if not all(permission and actor.has_permission(permission) for permission in permissions):
            raise AssetPermissionDeniedError()


def validate_purpose(spec: PurposeSpec) -> None:
    """Guard the registry itself: every purpose stays within the module-wide limits."""
    if not spec.allowed_type_ids or any(type_id not in FILE_TYPES for type_id in spec.allowed_type_ids):
        raise ValueError(f'{spec.purpose}: allowed types must be registered type ids')
    image_kind = spec.kind.value == 'image'
    if image_kind and any(FILE_TYPES[t].family is not TypeFamily.IMAGE for t in spec.allowed_type_ids):
        raise ValueError(f'{spec.purpose}: image purposes only accept image types')
    ceiling = MAX_IMAGE_BYTES if image_kind else MAX_ATTACHMENT_BYTES
    if not 0 < spec.max_bytes <= ceiling or spec.max_count < 1:
        raise ValueError(f'{spec.purpose}: size/count limits exceed module limits')


class PolicyRegistry:
    def __init__(self, policies: Iterable[AssetOwnerPolicy]):
        self._policies: dict[str, AssetOwnerPolicy] = {}
        self._purposes: dict[str, PurposeSpec] = {}
        self._fields: dict[tuple[str, str], PurposeSpec] = {}
        for policy in policies:
            if policy.owner_type in self._policies:
                raise ValueError(f'duplicate owner policy: {policy.owner_type}')
            self._policies[policy.owner_type] = policy
            for spec in policy.purposes:
                validate_purpose(spec)
                if spec.owner_type != policy.owner_type:
                    raise ValueError(f'{spec.purpose}: owner type does not match its policy')
                if spec.purpose in self._purposes or (spec.owner_type, spec.field_key) in self._fields:
                    raise ValueError(f'duplicate purpose or field: {spec.purpose}')
                self._purposes[spec.purpose] = spec
                self._fields[(spec.owner_type, spec.field_key)] = spec

    def purpose(self, purpose: str) -> PurposeSpec:
        spec = self._purposes.get((purpose or '').strip())
        if spec is None:
            raise AssetInvalidError('UNKNOWN_PURPOSE', '不支持的上传用途', field='purpose')
        return spec

    def field(self, owner_type: str, field_key: str) -> PurposeSpec:
        spec = self._fields.get((owner_type, field_key))
        if spec is None:
            raise AssetInvalidError('UNKNOWN_FIELD', '未登记的资产字段')
        return spec

    def policy(self, owner_type: str) -> AssetOwnerPolicy | None:
        return self._policies.get(owner_type)

    def require_policy(self, owner_type: str) -> AssetOwnerPolicy:
        policy = self._policies.get(owner_type)
        if policy is None:
            raise AssetInvalidError('UNKNOWN_OWNER_TYPE', '未登记的资产归属')
        return policy

    @property
    def purposes(self) -> tuple[PurposeSpec, ...]:
        return tuple(self._purposes.values())
