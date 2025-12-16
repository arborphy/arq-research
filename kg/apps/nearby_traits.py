"""Nearby plant traits app.

This is a small CLI that takes a latitude/longitude (decimal degrees) and prints
the most common USDA plant traits observed nearby, inferred via:

  Observation (GBIF) -> Taxon -> match canonical name -> USDA Plants -> Plant Traits

It shells out to Snowflake CLI ("snow") so it uses the same PAT-based auth flow
as the rest of this repo.

Examples:
  uv run -m kg.apps.nearby_traits --lat 41.2369444444 --lon -73.5680555556
  uv run -m kg.apps.nearby_traits --lat 37.55 --lon -122.32 --k 4 --limit 50

Lat/lon format:
  - Decimal degrees as floats.
  - North/East are positive; South/West are negative.
  - Latitude must be in [-90, 90], longitude in [-180, 180].
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def _normalize_connection_env_key(connection_name: str) -> str:
    # Snowflake CLI env var convention:
    #   SNOWFLAKE_CONNECTIONS_<CONNECTION_NAME>_PASSWORD
    # where <CONNECTION_NAME> is uppercased and non-alnum mapped to underscores.
    normalized = re.sub(r"[^A-Za-z0-9]", "_", connection_name).upper()
    return f"SNOWFLAKE_CONNECTIONS_{normalized}_PASSWORD"


def _ensure_snow_password_env(connection_name: str, pat_file: str | None) -> None:
    env_key = _normalize_connection_env_key(connection_name)
    if os.environ.get(env_key):
        return

    token_path = Path(pat_file or os.environ.get("SNOWFLAKE_PAT_FILE") or "~/.config/snowflake/pat.token").expanduser()
    if not token_path.exists():
        raise FileNotFoundError(
            f"Missing Snowflake PAT token file at {token_path}. "
            f"Set SNOWFLAKE_PAT_FILE or pass --pat-file, or export {env_key}."
        )

    os.environ[env_key] = token_path.read_text(encoding="utf-8").strip()


def _validate_lat_lon(lat: float, lon: float) -> None:
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude out of range [-90, 90]: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude out of range [-180, 180]: {lon}")


def _nearby_traits_query(
    *,
    lat: float,
    lon: float,
    k: int,
    res7: int,
    res6: int,
    limit: int,
    database: str,
    schema: str,
    observation_table: str,
    taxon_table: str,
    plants_table: str,
    plant_traits_table: str,
) -> str:
    # Note: observation_table etc are expected to be either unqualified table
    # names (OBSERVATION_10K) or fully-qualified (TEAM_ARQ.PUBLIC.OBSERVATION_10K).
    def qualify(t: str) -> str:
        if "." in t:
            return t
        return f"{database}.{schema}.{t}"

    obs = qualify(observation_table)
    taxon = qualify(taxon_table)
    plants = qualify(plants_table)
    plant_traits = qualify(plant_traits_table)

    # Keep the SQL close to the interactive query we validated in the terminal.
    return f"""
WITH params AS (
  SELECT {lat}::FLOAT AS lat, {lon}::FLOAT AS lon
),
cells AS (
  SELECT
    H3_GRID_DISK(H3_LATLNG_TO_CELL(lat, lon, {res7}), {k}) AS disk_7,
    H3_GRID_DISK(H3_LATLNG_TO_CELL(lat, lon, {res6}), {k}) AS disk_6
  FROM params
),
nearby_obs AS (
  SELECT DISTINCT o.TAXONKEY
  FROM {obs} o
  CROSS JOIN cells c
  WHERE ARRAY_CONTAINS(TO_VARIANT(o.H3_CELL_7), c.disk_7)
     OR ARRAY_CONTAINS(TO_VARIANT(o.H3_CELL_6), c.disk_6)
),
taxa AS (
  SELECT t.TAXONID, t.CANONICALNAME
  FROM {taxon} t
  JOIN nearby_obs n ON n.TAXONKEY = t.TAXONID
),
matched_plants AS (
  SELECT p.ID AS PLANT_ID, p.SCIENTIFIC_NAME, p.COMMON_NAME
  FROM {plants} p
  JOIN taxa t ON t.CANONICALNAME = p.SCIENTIFIC_NAME
),
traits AS (
  SELECT
    mp.SCIENTIFIC_NAME,
    mp.COMMON_NAME,
    pt.TRAIT_NAME,
    pt.TRAIT_VALUE
  FROM matched_plants mp
  JOIN {plant_traits} pt
    ON pt.PLANT_ID = mp.PLANT_ID
)
SELECT
  TRAIT_NAME,
  TRAIT_VALUE,
  COUNT(DISTINCT SCIENTIFIC_NAME) AS SPECIES_COUNT,
  LISTAGG(DISTINCT SCIENTIFIC_NAME, ', ') WITHIN GROUP (ORDER BY SCIENTIFIC_NAME) AS EXAMPLE_SPECIES,
  LISTAGG(DISTINCT COMMON_NAME, ', ') WITHIN GROUP (ORDER BY COMMON_NAME) AS EXAMPLE_COMMON_NAMES
FROM traits
GROUP BY 1, 2
ORDER BY SPECIES_COUNT DESC, TRAIT_NAME
LIMIT {limit};
""".strip()


def _run_snow_sql(*, connection: str, query: str, output_format: str) -> str:
    cmd: list[str] = [
        "uvx",
        "--from",
        "snowflake-cli",
        "snow",
        "sql",
        "-c",
        connection,
        "--format",
        output_format,
        "--silent",
        "-q",
        query,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "Snowflake query failed.\n"
            f"Command: {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def _truncate_cell(value: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(value) <= width:
        return value
    if width <= 3:
        return value[:width]
    return value[: width - 3] + "..."


def _print_json_as_table(rows: Sequence[Mapping[str, object]], *, terminal_width: int) -> None:
    if not rows:
        print("(no rows)")
        return

    columns = list(rows[0].keys())

    # Aim for a readable layout on typical terminals by capping column widths,
    # especially for the two listagg columns.
    # If the query shape changes, we fall back to a generic cap.
    fixed_caps = {
        "TRAIT_NAME": 30,
        "TRAIT_VALUE": 20,
        "SPECIES_COUNT": 13,
    }

    sep_len = 3  # len(" | ")
    num_seps = max(0, len(columns) - 1)

    # Reserve space for fixed columns (or header lengths if missing).
    reserved = num_seps * sep_len
    for c in columns:
        if c in fixed_caps:
            reserved += fixed_caps[c]
        else:
            reserved += min(len(c), 16)

    remaining = max(20, terminal_width - reserved)

    # Give the remaining space primarily to the example columns.
    example_cols = [c for c in columns if c in ("EXAMPLE_SPECIES", "EXAMPLE_COMMON_NAMES")]
    example_width = max(20, remaining // max(1, len(example_cols)))

    caps: dict[str, int] = {}
    for c in columns:
        if c in fixed_caps:
            caps[c] = fixed_caps[c]
        elif c in ("EXAMPLE_SPECIES", "EXAMPLE_COMMON_NAMES"):
            caps[c] = example_width
        else:
            caps[c] = min(16, max(8, len(c)))

    # Materialize rows as strings (truncated) and compute printed widths.
    str_rows: list[list[str]] = []
    widths = [min(len(c), caps.get(c, len(c))) for c in columns]

    for row in rows:
        values: list[str] = []
        for i, c in enumerate(columns):
            raw = "" if row.get(c) is None else str(row.get(c))
            raw = raw.replace("\n", " ").replace("\r", " ")
            v = _truncate_cell(raw, caps.get(c, 32))
            values.append(v)
            widths[i] = max(widths[i], len(v))
        str_rows.append(values)

    # Final clamp to caps (in case headers were longer).
    for i, c in enumerate(columns):
        widths[i] = min(widths[i], caps.get(c, widths[i]))

    header = " | ".join(_truncate_cell(c, widths[i]).ljust(widths[i]) for i, c in enumerate(columns))
    sep = "-+-".join("-" * widths[i] for i in range(len(columns)))
    print(header)
    print(sep)
    for values in str_rows:
        print(" | ".join(_truncate_cell(values[i], widths[i]).ljust(widths[i]) for i in range(len(columns))))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Given lat/lon, list common plant traits nearby (with common names).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Lat/lon must be decimal degrees. Examples:\n"
            "  --lat 41.2369444444 --lon -73.5680555556\n"
            "  --lat 37.7749 --lon -122.4194\n"
        ),
    )

    parser.add_argument("--lat", type=float, required=True, help="Latitude in decimal degrees (North positive)")
    parser.add_argument("--lon", type=float, required=True, help="Longitude in decimal degrees (East positive)")

    parser.add_argument("--k", type=int, default=3, help="H3 grid disk radius (default: 3)")
    parser.add_argument("--res7", type=int, default=7, help="H3 resolution for h3_cell_7 neighborhood (default: 7)")
    parser.add_argument("--res6", type=int, default=6, help="H3 resolution for h3_cell_6 neighborhood (default: 6)")
    parser.add_argument("--limit", type=int, default=30, help="Max rows to return (default: 30)")

    parser.add_argument("--connection", default="arbq_pat", help='Snowflake CLI connection name (default: "arbq_pat")')
    parser.add_argument(
        "--pat-file",
        default=None,
        help="Path to PAT token file (default: $SNOWFLAKE_PAT_FILE or ~/.config/snowflake/pat.token)",
    )

    parser.add_argument("--database", default="TEAM_ARQ", help="Snowflake database (default: TEAM_ARQ)")
    parser.add_argument("--schema", default="PUBLIC", help="Snowflake schema (default: PUBLIC)")

    parser.add_argument("--observation-table", default="OBSERVATION_10K", help="Observation table name (default: OBSERVATION_10K)")
    parser.add_argument("--taxon-table", default="TAXON", help="Taxon table name (default: TAXON)")
    parser.add_argument("--plants-table", default="PLANTS", help="Plants table name (default: PLANTS)")
    parser.add_argument("--plant-traits-table", default="PLANT_TRAITS", help="Plant traits table name (default: PLANT_TRAITS)")

    parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    parser.add_argument(
        "--terminal-width",
        type=int,
        default=0,
        help="Override detected terminal width in columns (default: auto)",
    )

    args = parser.parse_args(argv)

    try:
        _validate_lat_lon(args.lat, args.lon)
        _ensure_snow_password_env(args.connection, args.pat_file)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    query = _nearby_traits_query(
        lat=args.lat,
        lon=args.lon,
        k=args.k,
        res7=args.res7,
        res6=args.res6,
        limit=args.limit,
        database=args.database,
        schema=args.schema,
        observation_table=args.observation_table,
        taxon_table=args.taxon_table,
        plants_table=args.plants_table,
        plant_traits_table=args.plant_traits_table,
    )

    try:
        if args.output == "json":
            raw = _run_snow_sql(connection=args.connection, query=query, output_format="JSON")
            print(raw)
            return 0

        # Default: parse JSON and print a stable, dependency-free table.
        raw = _run_snow_sql(connection=args.connection, query=query, output_format="JSON")
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise ValueError("Unexpected JSON output (expected a list of rows)")
        detected_width = shutil.get_terminal_size((120, 20)).columns
        terminal_width = args.terminal_width if args.terminal_width and args.terminal_width > 0 else detected_width
        _print_json_as_table(rows, terminal_width=terminal_width)
        return 0
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
