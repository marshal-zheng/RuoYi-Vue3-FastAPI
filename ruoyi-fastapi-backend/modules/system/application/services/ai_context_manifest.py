# ruff: noqa: N815 -- Wire manifest keys are exact camelCase contract fields.
"""Load only local deployment metadata; invalid manifests disable this optional capability."""

import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, ValidationError, model_validator

from module_admin.entity.vo.text_field_ai_vo import Exact, Identifier, PersonalKind


class PermissionSet(Exact):
    mode: Literal['any']
    values: list[Annotated[str, Field(min_length=1, max_length=128)]] = Field(min_length=1, max_length=32)


class Purpose(Exact):
    label: str = Field(min_length=1, max_length=80)
    defaultContextIds: list[Identifier] = Field(max_length=16)
    selectableContextIds: list[Identifier] = Field(max_length=16)


class PublicMetadata(Exact):
    id: Identifier
    label: str = Field(min_length=1, max_length=80)
    sensitivity: Literal['public']


class PersonalMetadata(PublicMetadata):
    sensitivity: Literal['personal']
    kind: PersonalKind


class ScopeMetadata(Exact):
    permissions: PermissionSet
    purposes: dict[Identifier, Purpose] = Field(min_length=1)
    items: list[Annotated[PublicMetadata | PersonalMetadata, Field(discriminator='sensitivity')]] = Field(
        max_length=128
    )

    @model_validator(mode='after')
    def references(self):
        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)) or len(set(self.permissions.values)) != len(self.permissions.values):
            raise ValueError('duplicate metadata')
        for purpose in self.purposes.values():
            refs = [*purpose.defaultContextIds, *purpose.selectableContextIds]
            if len(refs) != len(set(refs)) or not set(refs) <= set(ids):
                raise ValueError('invalid purpose references')
        return self


class Manifest(Exact):
    version: Literal['ai-context/v1']
    scopes: dict[
        Annotated[str, Field(pattern=r'^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)+$', max_length=96)], ScopeMetadata
    ] = Field(min_length=1)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def load_manifest(configured_path: str = '') -> tuple[Manifest | None, str | None]:
    path = (
        Path(configured_path)
        if configured_path
        else Path(__file__).resolve().parents[4] / 'resources/ai-context/manifest.json'
    )
    try:
        with path.open('rb') as stream:
            raw = stream.read(262145)
        if len(raw) > 262144:
            return None, None
        data = json.loads(raw, object_pairs_hook=_unique_object)
        return Manifest.model_validate(data), hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError, TypeError, RecursionError, ValidationError):
        return None, None
