"""On-demand observation fetch endpoint.

Given a list of H3 cells (the area of interest) and an optional taxon
filter, fetches matching observations from the GBIF Occurrence API,
normalizes them to the stg_observations schema, and upserts them into
Snowflake. RAI picks them up on the next query (the existing loader binds
the whole table).

After a successful load the relevant cache namespaces are busted so
follow-up queries see the new data instead of stale cached results.

Endpoint:
    POST /api/observations/fetch-area
    Body:
        {
            "cells":       ["8a2a1072b59ffff", "8a2a1072b58ffff", ...],
                           # H3 cell hex strings (any resolution, mixed OK)
            "taxon":       "Quercus",          # optional scientific name
            "max_records": 5000                # optional, defaults to 5000
        }
    Response:
        {
            "gbif": { gbif_returned, after_cell_filter, taxon_key, ... },
            "snowflake": { attempted, inserted, deleted_for_idempotency, ... },
            "cache": { busted_namespaces: ["geo", ...] }
        }
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from webapp.backend.cache import cache_bust, cache_stats
from webapp.backend.gbif import fetch_observations_for_cells
from webapp.backend.snowflake_upload import upload_observations

log = logging.getLogger(__name__)

router = APIRouter(prefix="/observations", tags=["observations"])


# Namespaces invalidated when new observations are loaded. The cache
# decorator on each query function decides its own namespace; these are
# the ones whose results depend on Observation entities.
#
# DEMON: This list MUST stay in sync with the @ttl_cache(namespace=...)
# annotations across kg/queries/*.py. If you add a new query that joins
# Observation data, either:
#   (a) put it in one of these namespaces, OR
#   (b) add a new namespace and append it here.
# Today, predicates.py caches predicate_graph() under "ref" with a 10-min
# TTL; that graph can include observation-derived edges (Species created
# from observation rows), so users may see stale predicate-graph results
# for up to 10 minutes after a fetch-area call. Acceptable for now; if it
# bites, either move those queries to a new "deriv" namespace + add here,
# or call cache_bust() with no namespace to wipe everything.
OBSERVATION_DEPENDENT_NAMESPACES = ["geo", "co_occurrence", "trails"]


class FetchAreaRequest(BaseModel):
    cells:       list[str] = Field(..., min_length=1, description="H3 cell hex strings; any resolution")
    taxon:       str | None = Field(None, description="Scientific name (e.g. 'Quercus'); defaults to Plantae")
    max_records: int        = Field(5000, ge=1, le=100_000, description="Hard cap on rows fetched from GBIF")


@router.post("/fetch-area")
def fetch_area(req: FetchAreaRequest):
    """Fetch GBIF observations for an H3 cell area and load into Snowflake.

    Returns granular stats so the caller can show progress / diagnose
    why a fetch returned fewer rows than expected.

    DEMON (errors): Error responses MUST NOT include raw exception
    messages. Snowflake connector errors routinely contain account name,
    warehouse, role, full SQL text, and bind values. The PAT loader can
    leak filesystem paths. Always return a generic message with a
    correlation ID; the full trace goes to server logs only.

    DEMON (blocking): This is a sync `def` handler. It can hold a FastAPI
    worker thread for many seconds (cold GBIF fetch + Snowflake upsert).
    With Starlette's default 40-thread pool, a handful of concurrent
    fetch-area calls saturates the pool and the rest of the API stalls.
    Acceptable while it's only the developer hitting this endpoint;
    convert to BackgroundTasks + a job-status endpoint before exposing to
    multiple concurrent users.

    DEMON (no auth): There is no authentication on this endpoint. It
    issues DELETE + INSERT against the production stg_observations table.
    Today it's gated only by CORS (localhost) but a non-browser caller
    can hit it freely. Add auth (or restrict to internal-only routing)
    before this server is reachable outside localhost.

    DEMON (no cells limit): `cells` has min_length=1 but no max_length. A
    request with hundreds of thousands of cells will compute a planetary
    bbox and chew Snowflake compute. Add a max_length when the frontend
    starts driving this from real quest geometries.
    """
    # Correlation ID so a client error message can be traced back to the
    # specific server-log entry without exposing internals.
    cid = uuid.uuid4().hex[:12]
    log.info(f"[{cid}] fetch-area: cells={len(req.cells)} taxon={req.taxon!r} max_records={req.max_records}")

    try:
        df, gbif_stats = fetch_observations_for_cells(
            cells=req.cells,
            taxon=req.taxon,
            max_records=req.max_records,
        )
    except Exception:
        log.exception(f"[{cid}] GBIF fetch failed")
        raise HTTPException(502, f"Upstream GBIF fetch failed (cid={cid})")

    if df.empty:
        return {
            "cid":       cid,
            "gbif":      gbif_stats,
            "snowflake": {"attempted": 0, "inserted": 0, "note": "no rows after filtering"},
            "cache":     {"busted_namespaces": []},
        }

    try:
        sf_stats = upload_observations(df, source_tag="gbif")
    except Exception:
        log.exception(f"[{cid}] Snowflake upload failed")
        raise HTTPException(500, f"Snowflake upsert failed (cid={cid})")

    # Bust caches that depend on observations.
    busted = []
    for ns in OBSERVATION_DEPENDENT_NAMESPACES:
        n = cache_bust(ns)
        busted.append({"namespace": ns, "removed": n})

    return {
        "cid":       cid,
        "gbif":      gbif_stats,
        "snowflake": sf_stats,
        "cache":     {"busted": busted},
    }


@router.get("/cache/stats")
def cache_stats_endpoint():
    """Inspect cache hit/miss telemetry. Useful for tuning TTLs."""
    return cache_stats()


@router.post("/cache/bust")
def cache_bust_endpoint(namespace: str | None = None):
    """Manually invalidate cache entries. Pass ?namespace=geo to scope."""
    removed = cache_bust(namespace)
    return {"namespace": namespace, "removed": removed}
