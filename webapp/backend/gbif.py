"""GBIF Occurrence API client + normalization to stg_observations schema.

Used by the on-demand area-fetch endpoint to pull observations for a set of
H3 cells and prepare them for upload to Snowflake.

Why this exists:
  We can't replicate terabytes of GBIF data into Snowflake. Instead we
  fetch on demand for a specific quest area. The fetched rows are then
  upserted into stg_observations so the existing RAI loader picks them up
  on the next query.

Public surface:
  fetch_observations_for_cells(cells, taxon=None, max_records=10_000) -> DataFrame
      Returns a DataFrame with the same columns as stg_observations
      (including SOURCE='gbif' and H3_RES7/9/12/13 pre-computed).

References:
  GBIF Occurrence search API: https://techdocs.gbif.org/en/openapi/v1/occurrence
  GBIF Species match API:    https://techdocs.gbif.org/en/openapi/v1/species
"""

from __future__ import annotations

import logging
from typing import Iterator

import h3
import pandas as pd
import requests

log = logging.getLogger(__name__)

GBIF_BASE = "https://api.gbif.org/v1"
PAGE_SIZE = 300          # GBIF's max per-page
MAX_OFFSET = 100_000     # GBIF's hard offset ceiling
DEFAULT_TIMEOUT = 30     # seconds; GBIF search is fast but can spike

# Kingdom Plantae — used as the default taxonKey filter when no taxon is
# supplied. Avoids pulling birds/insects/fungi into the observation table.
PLANTAE_TAXON_KEY = 6


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_observations_for_cells(
    cells: list[str | int],
    taxon: str | None = None,
    max_records: int = 10_000,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[pd.DataFrame, dict]:
    """Fetch GBIF occurrences whose coordinates fall in the given H3 cells.

    Args:
        cells: H3 cell indices (hex strings or ints). Mixed resolutions OK.
        taxon: Optional scientific name (e.g. 'Quercus', 'Trillium erectum').
               Resolved via GBIF /species/match → taxonKey. If None, defaults
               to Kingdom Plantae (taxonKey=6).
        max_records: Hard cap on returned rows. Protects against runaway
                     fetches in dense areas.
        timeout: Per-request HTTP timeout in seconds.

    Returns:
        (df, stats) where df has stg_observations columns + SOURCE='gbif',
        and stats describes the fetch.

    Stats keys:
        gbif_matched, gbif_returned, after_cell_filter, taxon_key, bbox
    """
    if not cells:
        return _empty_df(), {"gbif_matched": 0, "gbif_returned": 0, "after_cell_filter": 0}

    # Normalize H3 cells to hex strings (h3-py accepts both, but we want a
    # consistent set for membership testing).
    cell_set = {_to_hex(c) for c in cells}

    # ── 1. Compute bounding box of all cells ─────────────────────────────────
    bbox = _cells_bbox(cell_set)

    # ── 2. Resolve taxon → taxonKey ──────────────────────────────────────────
    # DEMON: If a user-supplied name doesn't resolve in GBIF (typo, obscure
    # synonym, etc.) we MUST fall back to Plantae rather than dropping the
    # taxon filter entirely. Without this guard, a typo like 'Querkus' would
    # silently fetch all kingdoms (birds, insects, fungi) within the bbox
    # and dump them into stg_observations. The "no taxon" default behavior
    # is Plantae, so an unresolved name should degrade to the same default.
    if taxon:
        taxon_key, match_data = _resolve_taxon(taxon, timeout=timeout)
        if taxon_key is None:
            log.warning(
                f"GBIF: could not resolve taxon name {taxon!r}; "
                f"falling back to Kingdom Plantae (taxonKey={PLANTAE_TAXON_KEY})"
            )
            taxon_key = PLANTAE_TAXON_KEY
            taxon_meta = {
                "matchType":      "FALLBACK_PLANTAE",
                "rank":            "KINGDOM",
                "scientificName":  "Plantae",
                "input":           taxon,
                "gbif_match_data": match_data,
            }
        else:
            taxon_meta = match_data
    else:
        taxon_key = PLANTAE_TAXON_KEY
        taxon_meta = {"matchType": "DEFAULT", "rank": "KINGDOM", "scientificName": "Plantae"}

    # ── 3. Fetch occurrences in bbox ─────────────────────────────────────────
    raw_rows = list(_iter_occurrences(
        bbox=bbox,
        taxon_key=taxon_key,
        max_records=max_records,
        timeout=timeout,
    ))
    gbif_returned = len(raw_rows)
    log.info(f"GBIF: fetched {gbif_returned} occurrences for bbox={bbox} taxonKey={taxon_key}")

    # ── 4. Filter to cells that were actually requested ──────────────────────
    # GBIF's bbox query is rectangular but the H3 cell set may be an irregular
    # shape, so we compute the res-13 cell for each result and keep only
    # those whose ancestors at the requested resolutions are in cell_set.
    in_cells = [r for r in raw_rows if _falls_in_requested_cells(r, cell_set)]
    after_cell_filter = len(in_cells)

    # ── 5. Normalize to stg_observations schema + compute H3 columns ─────────
    df = _normalize_to_stg(in_cells)

    stats = {
        "gbif_returned":     gbif_returned,
        "after_cell_filter": after_cell_filter,
        "taxon_key":         taxon_key,
        "taxon_meta":        taxon_meta,
        "bbox":              bbox,
    }
    return df, stats


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _to_hex(cell: str | int) -> str:
    """Normalize an H3 cell to lowercase hex string."""
    if isinstance(cell, int):
        return format(cell, "x")
    return cell.lower()


def _cells_bbox(cell_hexes: set[str]) -> tuple[float, float, float, float]:
    """Return (min_lat, max_lat, min_lon, max_lon) covering all cell boundaries."""
    lats, lons = [], []
    for c in cell_hexes:
        boundary = h3.cell_to_boundary(c)  # list of (lat, lon) pairs
        for lat, lon in boundary:
            lats.append(lat)
            lons.append(lon)
    return (min(lats), max(lats), min(lons), max(lons))


def _falls_in_requested_cells(record: dict, cell_set: set[str]) -> bool:
    """True if the record's coords land inside one of the requested H3 cells.

    Computes the record's H3 cell at each resolution present in cell_set and
    checks membership. This handles mixed-resolution cell lists.

    DEMON: The `resolutions` set is invariant across records but recomputed
    on every call. For N records × M cells this is O(N·M). When real quest
    geometries arrive (hundreds of cells), hoist the resolution-set
    computation up to `fetch_observations_for_cells` and pass it in.
    """
    lat = record.get("decimalLatitude")
    lon = record.get("decimalLongitude")
    if lat is None or lon is None:
        return False
    # Resolutions actually used in cell_set — usually one or two values.
    resolutions = {h3.get_resolution(c) for c in cell_set}
    for res in resolutions:
        if h3.latlng_to_cell(lat, lon, res) in cell_set:
            return True
    return False


def _resolve_taxon(name: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[int | None, dict]:
    """Resolve a scientific name to a GBIF taxonKey.

    Returns (taxonKey, full match metadata). taxonKey is None on no-match.
    """
    r = requests.get(
        f"{GBIF_BASE}/species/match",
        params={"name": name, "strict": "false"},
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("matchType") == "NONE":
        return None, data
    # Prefer the most specific key available — usageKey is the matched
    # taxon's GBIF ID. If matchType=='HIGHERRANK' it's still a valid filter.
    return data.get("usageKey"), data


def _iter_occurrences(
    bbox: tuple[float, float, float, float],
    taxon_key: int | None,
    max_records: int,
    timeout: int = DEFAULT_TIMEOUT,
) -> Iterator[dict]:
    """Page through GBIF /occurrence/search within a bbox + optional taxon."""
    min_lat, max_lat, min_lon, max_lon = bbox
    params_base = {
        "decimalLatitude":  f"{min_lat},{max_lat}",
        "decimalLongitude": f"{min_lon},{max_lon}",
        "hasCoordinate":    "true",
        "hasGeospatialIssue": "false",
        "limit":            PAGE_SIZE,
    }
    if taxon_key is not None:
        params_base["taxonKey"] = taxon_key

    offset = 0
    yielded = 0
    while yielded < max_records and offset < MAX_OFFSET:
        params = {**params_base, "offset": offset}
        r = requests.get(f"{GBIF_BASE}/occurrence/search", params=params, timeout=timeout)
        r.raise_for_status()
        payload = r.json()
        results = payload.get("results", [])
        if not results:
            break
        for rec in results:
            yield rec
            yielded += 1
            if yielded >= max_records:
                return
        if payload.get("endOfRecords"):
            break
        offset += PAGE_SIZE


def _normalize_to_stg(records: list[dict]) -> pd.DataFrame:
    """Map GBIF occurrence records → stg_observations schema (uppercase cols).

    Output columns mirror dbt/models/staging/stg_observations.py exactly, so
    the existing kg.loaders.observations binding picks them up without
    changes:
      ID, UUID, SCIENTIFIC_NAME, COMMON_NAME, TAXON_ID, ICONIC_TAXON_NAME,
      OBSERVED_ON, TIME_OBSERVED_AT, LATITUDE, LONGITUDE,
      POSITIONAL_ACCURACY, COORDINATES_OBSCURED, IMAGE_URL, URL,
      QUALITY_GRADE, NUM_IDENTIFICATION_AGREEMENTS,
      NUM_IDENTIFICATION_DISAGREEMENTS, CAPTIVE_CULTIVATED,
      PLACE_GUESS, SPECIES_GUESS, DESCRIPTION, LICENSE, SOURCE,
      H3_RES7, H3_RES9, H3_RES12, H3_RES13
    """
    if not records:
        return _empty_df()

    rows = []
    for r in records:
        lat = r.get("decimalLatitude")
        lon = r.get("decimalLongitude")
        if lat is None or lon is None:
            continue  # shouldn't happen because we asked for hasCoordinate=true
        rows.append({
            "ID":                                str(r.get("gbifID", "")),
            "UUID":                              r.get("occurrenceID") or "",
            "SCIENTIFIC_NAME":                   r.get("species") or r.get("scientificName") or "",
            "COMMON_NAME":                       r.get("vernacularName") or "",
            "TAXON_ID":                          str(r.get("taxonKey", "")),
            "ICONIC_TAXON_NAME":                 r.get("kingdom") or "",
            "OBSERVED_ON":                       _gbif_date(r),
            "TIME_OBSERVED_AT":                  r.get("eventDate") or "",
            "LATITUDE":                          float(lat),
            "LONGITUDE":                         float(lon),
            "POSITIONAL_ACCURACY":               _safe_float(r.get("coordinateUncertaintyInMeters")),
            "COORDINATES_OBSCURED":              False,
            "IMAGE_URL":                         _first_media_url(r),
            "URL":                               f"https://www.gbif.org/occurrence/{r.get('gbifID', '')}",
            "QUALITY_GRADE":                     _quality_from_basis(r.get("basisOfRecord")),
            "NUM_IDENTIFICATION_AGREEMENTS":     0,
            "NUM_IDENTIFICATION_DISAGREEMENTS":  0,
            "CAPTIVE_CULTIVATED":                bool(r.get("establishmentMeans", "") in ("MANAGED", "INTRODUCED", "CULTIVATED")),
            "PLACE_GUESS":                       r.get("locality") or r.get("stateProvince") or "",
            "SPECIES_GUESS":                     r.get("species") or "",
            "DESCRIPTION":                       "",
            "LICENSE":                           r.get("license") or "",
            "SOURCE":                            "gbif",
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return _empty_df()

    # Drop dupes by GBIF ID (shouldn't happen within a single fetch but cheap).
    df = df.drop_duplicates(subset=["ID"]).reset_index(drop=True)

    # Compute H3 cells the same way the dbt model does.
    for res in (7, 9, 12, 13):
        df[f"H3_RES{res}"] = [
            int(h3.latlng_to_cell(lat, lon, res), 16)
            for lat, lon in zip(df["LATITUDE"], df["LONGITUDE"])
        ]

    # Coerce OBSERVED_ON to a real date (Snowflake will accept str but cleaner).
    df["OBSERVED_ON"] = pd.to_datetime(df["OBSERVED_ON"], errors="coerce").dt.date

    return df


def _empty_df() -> pd.DataFrame:
    """Return an empty DataFrame with the expected stg_observations columns.

    DEMON: This column list duplicates the definition in three places:
      1. `dbt/models/staging/stg_observations.py::COLS` (lowercase)
      2. The Snowflake table schema (RAI_DEMO.CB_WEBAPP.stg_observations)
      3. `kg/loaders/observations.py::obs_table = m.Table(... schema=...)`
    If you add or rename a column, all three must change in lockstep. The
    RAI loader binds the whole table, so a missing column manifests as
    null/missing data in the graph — not a loud error.

    When this becomes painful, factor `COLS + H3_RESOLUTIONS` from the
    dbt model into a shared module and have everything import from it.
    """
    return pd.DataFrame(columns=[
        "ID", "UUID", "SCIENTIFIC_NAME", "COMMON_NAME", "TAXON_ID",
        "ICONIC_TAXON_NAME", "OBSERVED_ON", "TIME_OBSERVED_AT", "LATITUDE",
        "LONGITUDE", "POSITIONAL_ACCURACY", "COORDINATES_OBSCURED",
        "IMAGE_URL", "URL", "QUALITY_GRADE", "NUM_IDENTIFICATION_AGREEMENTS",
        "NUM_IDENTIFICATION_DISAGREEMENTS", "CAPTIVE_CULTIVATED",
        "PLACE_GUESS", "SPECIES_GUESS", "DESCRIPTION", "LICENSE", "SOURCE",
        "H3_RES7", "H3_RES9", "H3_RES12", "H3_RES13",
    ])


def _gbif_date(r: dict) -> str:
    """Extract OBSERVED_ON from a GBIF record."""
    # GBIF gives eventDate as ISO; year/month/day may be set even when
    # eventDate is missing.
    iso = r.get("eventDate")
    if iso:
        # Strip time portion if present
        return iso.split("T", 1)[0][:10]
    y, m, d = r.get("year"), r.get("month"), r.get("day")
    if y and m and d:
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    return ""


def _safe_float(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _first_media_url(r: dict) -> str:
    """Get the first stillImage URL from a GBIF record's media list."""
    media = r.get("media") or []
    for m in media:
        if m.get("type") == "StillImage" and m.get("identifier"):
            return m["identifier"]
    return ""


def _quality_from_basis(basis: str | None) -> str:
    """Map GBIF basisOfRecord → iNat-style quality_grade for downstream consistency.

    DEMON: This mapping reuses the value "research" which has a SPECIFIC
    meaning in the existing iNat data: "photo + GPS + date + ≥2/3
    community ID agreement." A GBIF HUMAN_OBSERVATION record can be a
    single unvetted entry. Any downstream code that filters
    `quality_grade='research'` as a trust signal will now treat GBIF
    rows as research-grade when they may not be.

    If you start exposing quality_grade in product filters, either:
      (a) switch this mapping to always return 'casual' for GBIF, OR
      (b) check GBIF's identificationVerificationStatus / issues fields,
          which carry the real review state.
    """
    if not basis:
        return "casual"
    # HUMAN_OBSERVATION + identified = closest to iNat 'research'; everything
    # else is treated as 'casual' (needs_id is iNat-specific).
    if basis in ("HUMAN_OBSERVATION", "OBSERVATION", "MACHINE_OBSERVATION"):
        return "research"
    return "casual"
