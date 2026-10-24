"""Bounded wire storage contract; full widget validation remains in Dashboard."""

import json
from typing import Any, Literal

from pydantic import ConfigDict, Field, field_validator

from module_admin.entity.vo.base import CamelModelBase

DashboardScope = Literal['account', 'scene']
MAX_DOCUMENT_BYTES = 1024 * 1024
MAX_PANELS = 500
MAX_GRID_COORDINATE = 100000


class DashboardSaveModel(CamelModelBase):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    document: dict[str, Any]
    expected_revision: int | None = Field(alias='expectedRevision', ge=1, strict=True)

    @field_validator('document')
    @classmethod
    def bounded_document(cls, value):
        try:
            encoded = json.dumps(value, allow_nan=False, ensure_ascii=False).encode('utf-8')
        except (ValueError, TypeError, RecursionError) as exc:
            raise ValueError('Dashboard must be finite JSON') from exc
        if len(encoded) > MAX_DOCUMENT_BYTES:
            raise ValueError('Dashboard exceeds 1 MiB')
        if type(value.get('schemaVersion')) is not int or value['schemaVersion'] != 2:
            raise ValueError('Dashboard schemaVersion must be 2')
        panels = value.get('panels')
        if not isinstance(panels, list) or len(panels) > MAX_PANELS:
            raise ValueError('Dashboard must contain at most 500 panels')
        ids = set()
        for panel in panels:
            if not isinstance(panel, dict):
                raise ValueError('Panel must be an object')
            for name in ('id', 'widget'):
                if not isinstance(panel.get(name), str) or not panel[name].strip():
                    raise ValueError(f'Invalid panel {name}')
            if panel['id'] in ids:
                raise ValueError('Duplicate panel ID')
            ids.add(panel['id'])
            grid = panel.get('gridPos')
            if not isinstance(grid, dict):
                raise ValueError('Panel gridPos is required')
            for name in ('x', 'y', 'w', 'h'):
                number = grid.get(name)
                minimum = 0 if name in ('x', 'y') else 1
                if type(number) is not int or not minimum <= number <= MAX_GRID_COORDINATE:
                    raise ValueError(f'Invalid grid coordinate {name}')
        return value
