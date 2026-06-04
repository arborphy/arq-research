"""Quest contract Pydantic models for arborphy quest validation.

These models define the canonical shape of quest payloads exported from
arq-visualization (questmaker) and consumed by arq-research / arq-mobile.
They are intentionally aligned with the schema documented in
arq-visualization/AGENTS.md §"Quest schema".

No Snowflake or RAI dependencies — pure validation contracts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Literals ────────────────────────────────────────────────────────────────

TargetType = Literal['taxon', 'instance', 'interaction', 'abiotic']
MediaType = Literal['image', 'audio', 'video']
Difficulty = Literal['easy', 'moderate', 'challenging'] | None


# ── FeatureTarget ──────────────────────────────────────────────────────────

class FeatureTarget(BaseModel):
    """A single feature dimension the participant should look for on a target."""

    model_config = ConfigDict(extra="allow")

    group: str = Field(default="", description="Feature group/category")
    feature: str = Field(default="", description="Feature dimension name")
    value: Any | None = Field(default=None, description="Expected value (null when exploratory)")
    hint: str | None = Field(default=None, description="UX hint shown to player")
    question: str | None = Field(default=None, description="Binary calibration question")
    value_image: str | None = Field(default=None, description="Reference image URL")


# ── MediaAttachment ────────────────────────────────────────────────────────

class MediaAttachment(BaseModel):
    """A media reference attached to an observation plan."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Media attachment identifier")
    media_type: MediaType = Field(default='image', description="media type tag")
    url_or_local_path: str | None = Field(default=None, description="URL or relative path")
    notes: str | None = Field(default=None)


# ── ObservationTarget ──────────────────────────────────────────────────────

class ObservationTarget(BaseModel):
    """A specific biological/abiotic target within an observation plan."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Stable target identifier")
    target_type: TargetType = Field(default="taxon", description="e.g. 'taxon', 'instance', 'interaction', 'abiotic'")
    taxon_name: str | None = Field(default=None)
    common_name: str | None = Field(default=None)
    target_features: list[FeatureTarget] = Field(default_factory=list)
    notes: str | None = Field(default=None)


# ── ObservationPlan ────────────────────────────────────────────────────────

class ObservationPlan(BaseModel):
    """An observation plan nested inside a quest stop."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Stable observation plan identifier")
    name: str = Field(default="", description="Display name")
    notes: str | None = Field(default=None)
    date: str | None = Field(default=None, description="YYYY-MM-DD or ISO date")
    media: list[MediaAttachment] = Field(default_factory=list)
    targets: list[ObservationTarget] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


# ── Camera framing (optional stop-level camera pose) ──────────────────────

class CameraPose(BaseModel):
    """Optional camera framing for a stop location."""

    lon: float = 0.0
    lat: float = 0.0
    alt: float = 0.0
    heading: float = 0.0
    pitch: float = 0.0


# ── Temporal moment hint ───────────────────────────────────────────────────

class MomentHint(BaseModel):
    """Optional seasonal/temporal hint for when a stop is relevant."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda field_name: {
            'day_of_year': 'dayOfYear',
        }.get(field_name, field_name),
    )

    day_of_year: int = Field(
        ...,
        ge=1,
        le=366,
        description="Day of year 1-366",
    )
    window: int = Field(
        default=7,
        ge=0,
        description="±days tolerance around day_of_year",
    )


# ── QuestStop ──────────────────────────────────────────────────────────────

class QuestStop(BaseModel):
    """A location stop within a quest, containing observation plans."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Stable stop identifier")
    name: str = Field(default="", description="Display name")
    notes: str | None = Field(default=None)
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    alt: float = Field(default=0.0, description="Altitude in meters")
    camera: CameraPose | None = Field(default=None)
    moment: MomentHint | None = Field(default=None)
    observations: list[ObservationPlan] = Field(default_factory=list)


# ── Quest ──────────────────────────────────────────────────────────────────

class Quest(BaseModel):
    """Top-level quest document — the canonical export shape from questmaker."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Stable quest identifier")
    name: str = Field(..., description="Display name")
    created: str | None = Field(default=None, description="ISO datetime of creation")
    difficulty: Difficulty = Field(default=None, description="easy | moderate | challenging")
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    stops: list[QuestStop] = Field(default_factory=list)


# ── Validation response ────────────────────────────────────────────────────

class ValidationResponse(BaseModel):
    """Response from the quest validation endpoint."""

    status: str = Field(..., description="'valid' or 'invalid'")
    quest: Quest | None = Field(default=None, description="Validated quest (None if invalid)")
    errors: list[str] = Field(default_factory=list, description="Validation error messages")
