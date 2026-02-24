"""API schemas for event history and replay."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventHistoryQuery(BaseModel):
    aggregate_id: str | None = Field(default=None, alias='aggregateId')
    aggregate_type: str | None = Field(default=None, alias='aggregateType')
    event_type: str | None = Field(default=None, alias='eventType')
    begin_time: datetime | None = Field(default=None, alias='beginTime')
    end_time: datetime | None = Field(default=None, alias='endTime')
    page_num: int = Field(default=1, alias='pageNum')
    page_size: int = Field(default=20, alias='pageSize')

    model_config = ConfigDict(populate_by_name=True)


class EventReplayRequest(BaseModel):
    aggregate_id: str | None = Field(default=None, alias='aggregateId')
    aggregate_type: str | None = Field(default=None, alias='aggregateType')
    event_type: str | None = Field(default=None, alias='eventType')
    begin_time: datetime | None = Field(default=None, alias='beginTime')
    end_time: datetime | None = Field(default=None, alias='endTime')
    limit: int = Field(default=200, ge=1, le=1000)

    model_config = ConfigDict(populate_by_name=True)
