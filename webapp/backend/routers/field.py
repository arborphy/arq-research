"""Field-capture observation endpoints (arq-mobile sync target).

This router is the mediation layer between arq-mobile (ArborQuest) and the
arborphy backend. Mobile captures observations OFFLINE (Automerge +
localStorage), then drains its pending queue to these endpoints when it
regains connectivity.

Deliberately ISOLATED from `observations.py`:
    observations.py  → GBIF fetch → PRODUCTION Snowflake stg_observations
    field.py (this)  → local JSONL file + local media dir, NO Snowflake

The Snowflake write path is a hazard we are explicitly keeping field-capture
traffic away from (no auth, blocking, prod table). Promotion of field data
into Snowflake/RAI is a SEPARATE, later, deliberate job:
    field_observations.jsonl → local_observations.csv → upload_stg_observations.py

Storage layout (all under ARQ_FIELD_STORE, default webapp/backend/_field_data):
    _field_data/observations.jsonl        — append-only, upsert-by-arborphy_id on read
    _field_data/media/{arborphy_id}/{filename}  — uploaded photos

Endpoints (mounted at /api by main.py):
    POST /api/field/observations              — upsert one observation (idempotent)
    GET  /api/field/observations              — list all (latest-wins per arborphy_id)
    POST /api/field/observations/{id}/photo   — multipart photo upload
    GET  /api/field/media/{id}/{filename}     — served via StaticFiles mount (see main.py)

See arq-mobile/AGENTS.md §6 for the canonical observation schema and §3 for
the field sync pipeline.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

router = APIRouter(prefix="/field", tags=["field"])


# ── Storage location ────────────────────────────────────────────────────────
# Configurable so tests / alternate field sites can point elsewhere, and so
# the path is never hard-coded the way the Snowflake constants are.
def _store_root() -> Path:
    root = os.environ.get("ARQ_FIELD_STORE")
    if root:
        return Path(root)
    # Default: webapp/backend/_field_data (this file is webapp/backend/routers/)
    return Path(__file__).resolve().parents[1] / "_field_data"


def _obs_path() -> Path:
    return _store_root() / "observations.jsonl"


def media_root() -> Path:
    """Public: main.py mounts this directory under /api/field/media."""
    return _store_root() / "media"


def _ensure_dirs() -> None:
    _store_root().mkdir(parents=True, exist_ok=True)
    media_root().mkdir(parents=True, exist_ok=True)


# ── Schema ──────────────────────────────────────────────────────────────────
# Mirrors arq-mobile/AGENTS.md §6 but intentionally permissive: the field
# client owns the canonical shape, and we must not reject an observation in
# the field because of a schema-drift mismatch. Unknown fields are preserved
# verbatim (extra="allow") so the contract can evolve client-first.
class FieldObservation(BaseModel):
    model_config = {"extra": "allow"}

    arborphy_id: str = Field(..., description="Stable permanent key; the upsert id")
    taxon_name: str | None = None
    common_name: str | None = None
    observed_on: str | None = None
    time_observed_at: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    positional_accuracy: float | None = None
    description: str | None = None
    photos: list[str] = Field(default_factory=list)
    instance_id: str | None = None
    quest_id: str | None = None
    stop_id: str | None = None
    session_id: str | None = None
    traits_observed: list[dict] = Field(default_factory=list)
    source: str = "arborphy"


_ARBORPHY_ID_RE = re.compile(r"^arq-\d{8}-[A-Za-z0-9_-]+$")


def _read_all() -> dict[str, dict]:
    """Read the JSONL log, applying latest-wins upsert by arborphy_id.

    The file is append-only; the live state is the last record seen for each
    id. A corrupt/half-written trailing line is skipped (crash-safe append).
    """
    path = _obs_path()
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # Tolerate a torn final line from a crashed append.
                log.warning("[field] skipping unparseable JSONL line")
                continue
            aid = rec.get("arborphy_id")
            if aid:
                out[aid] = rec
    return out


def _append(rec: dict) -> None:
    _ensure_dirs()
    # Append is atomic enough for single-writer; each record is one line so a
    # torn write only damages its own line (handled by _read_all).
    with _obs_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ── Endpoints ───────────────────────────────────────────────────────────────
@router.post("/observations")
def upsert_observation(obs: FieldObservation):
    """Upsert one field observation. Idempotent by arborphy_id.

    Re-posting the same arborphy_id (e.g. a sync retry after a dropped
    connection) is safe: it appends a newer record that supersedes the old
    one on read. The mobile client may POST the same observation multiple
    times across reconnects; that must never create duplicates.
    """
    cid = uuid.uuid4().hex[:12]
    if not _ARBORPHY_ID_RE.match(obs.arborphy_id):
        # Don't leak internals, but this one is safe and actionable.
        raise HTTPException(422, f"Invalid arborphy_id format (cid={cid})")

    rec = obs.model_dump()
    rec["_received_at"] = datetime.now(timezone.utc).isoformat()
    try:
        _append(rec)
    except Exception:
        log.exception(f"[{cid}] field observation append failed")
        raise HTTPException(500, f"Could not persist observation (cid={cid})")

    log.info(f"[{cid}] field obs upserted: {obs.arborphy_id} taxon={obs.taxon_name!r}")
    return {"cid": cid, "arborphy_id": obs.arborphy_id, "status": "stored"}


@router.get("/observations")
def list_observations():
    """List all field observations (latest-wins per arborphy_id).

    Read by arq-visualization (questmaker) to render field results back on
    the globe, and by arq-mobile to confirm round-trip.
    """
    records = list(_read_all().values())
    records.sort(key=lambda r: r.get("_received_at", ""), reverse=True)
    return {"data": records, "total": len(records)}


@router.post("/observations/{arborphy_id}/photo")
async def upload_photo(arborphy_id: str, file: UploadFile = File(...)):
    """Store a photo for an observation and return its served URL.

    Idempotent per (arborphy_id, filename): re-uploading overwrites the same
    path, matching the mobile retry semantics. Returns an image_url the
    client can persist back onto the observation and that questmaker can load.
    """
    cid = uuid.uuid4().hex[:12]
    if not _ARBORPHY_ID_RE.match(arborphy_id):
        raise HTTPException(422, f"Invalid arborphy_id format (cid={cid})")

    # Sanitize filename: no path traversal, keep a sane default.
    raw_name = file.filename or "photo.jpg"
    safe_name = Path(raw_name).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", safe_name) or "photo.jpg"

    dest_dir = media_root() / arborphy_id
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        data = await file.read()
        (dest_dir / safe_name).write_bytes(data)
    except Exception:
        log.exception(f"[{cid}] photo write failed for {arborphy_id}")
        raise HTTPException(500, f"Could not store photo (cid={cid})")

    image_url = f"/api/field/media/{arborphy_id}/{safe_name}"
    log.info(f"[{cid}] photo stored: {image_url} ({len(data)} bytes)")
    return {"cid": cid, "arborphy_id": arborphy_id, "filename": safe_name, "image_url": image_url}
