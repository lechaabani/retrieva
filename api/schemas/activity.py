"""Schemas for the activity feed endpoint."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ActivityEvent(BaseModel):
    """A single event in the activity feed timeline."""

    id: str = Field(..., description="Unique event identifier")
    type: str = Field(
        ...,
        description="Event type: document_ingested, query_made, collection_created, api_key_created, error",
    )
    title: str = Field(..., description="Short human-readable title")
    description: str = Field("", description="Longer description of the event")
    timestamp: datetime = Field(..., description="When the event occurred (UTC)")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary extra data for the event"
    )

    model_config = {"from_attributes": True}


class ActivityFeedResponse(BaseModel):
    """Response envelope for the activity feed."""

    events: list[ActivityEvent] = Field(default_factory=list)
    total_count: int = Field(0, description="Total number of events returned")
