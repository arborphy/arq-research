"""Quest contract validation endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from webapp.backend.contracts.quest import Quest, ValidationResponse

log = logging.getLogger(__name__)

router = APIRouter(prefix="/contracts/quest", tags=["quest-contracts"])


@router.post("/validate", response_model=ValidationResponse)
def validate_quest(quest: Quest) -> ValidationResponse:
    """Validate a quest payload and return the normalized quest or errors.

    Accepts a full Quest document (the canonical export shape from
    questmaker). Returns a ValidationResponse with:
    - status: "valid" — quest passed all Pydantic validation; the normalised
      quest (with defaults applied) is returned in the `quest` field.
    - status: "invalid" — FastAPI already rejected the request before this
      handler is reached (HTTP 422). This handler only returns valid results.

    This endpoint is deliberately minimal: Pydantic enforces the schema
    (required ids, lat/lon ranges, day_of_year bounds, etc.). Additional
    business-rule validators can be added here as the contract matures.
    """
    # At this point Pydantic has already validated the shape.
    # We perform a lightweight business-rule check: a valid quest should
    # have at least one stop.
    errors: list[str] = []
    if not quest.stops:
        errors.append("Quest must have at least one stop")

    if errors:
        return ValidationResponse(status="invalid", errors=errors)

    return ValidationResponse(status="valid", quest=quest)
