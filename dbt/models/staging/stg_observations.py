"""Staging model: merge iNat + arborphy-local observations, compute H3 cells.

Sources merged:
  data/observations.csv        — iNaturalist export (source='inat')
  data/local_observations.csv  — arborphy manual import (source='arborphy')
                                  produced by image_process/exif_to_csv.py
                                  only merged if the file exists

Both files share the same column schema. The `source` column is present in
local_observations.csv (set by exif_to_csv.py) and added as 'inat' for all
rows from observations.csv so downstream consumers can distinguish them.

The core merge logic lives in `merge_observations(data_dir)` — a pure function
that can be called and tested without a dbt context.
"""
import os
import pathlib

import h3
import pandas as pd


def _repo_root() -> pathlib.Path:
    if "ARBORPHY_ROOT" in os.environ:
        return pathlib.Path(os.environ["ARBORPHY_ROOT"])
    for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents]:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("Set ARBORPHY_ROOT or run dbt from within the arborphy repo")


COLS = [
    "id", "uuid", "scientific_name", "common_name", "taxon_id",
    "iconic_taxon_name", "observed_on", "time_observed_at", "latitude",
    "longitude", "positional_accuracy", "coordinates_obscured", "image_url",
    "url", "quality_grade", "num_identification_agreements",
    "num_identification_disagreements", "captive_cultivated",
    "place_guess", "species_guess", "description", "license",
]

H3_RESOLUTIONS = [7, 9, 12, 13]


def merge_observations(data_dir: pathlib.Path) -> tuple[pd.DataFrame, dict]:
    """Merge iNat + local CSVs, compute H3 cells. Returns (df, stats).

    This is the testable core of the staging model — no dbt context needed.

    stats keys:
      inat_rows, local_rows, total_before_filter,
      dropped_no_gps, total_rows, has_local
    """
    stats: dict = {}

    # ── iNat observations ────────────────────────────────────────────────────
    # Force id to str — iNat IDs are integers in CSV but arborphy IDs are strings;
    # keeping both as str avoids mixed-type issues in the merged table.
    inat_csv = data_dir / "observations.csv"
    inat = pd.read_csv(inat_csv, usecols=COLS, dtype={"id": str}, low_memory=False)
    inat["source"] = "inat"
    stats["inat_rows"] = len(inat)

    frames = [inat]

    # ── arborphy local observations (optional) ───────────────────────────────
    local_csv = data_dir / "local_observations.csv"
    if local_csv.exists():
        local_cols = COLS + ["source"]
        # Only read columns that are actually present (source may be absent in old files)
        available = pd.read_csv(local_csv, nrows=0).columns.tolist()
        read_cols = [c for c in local_cols if c in available]
        local = pd.read_csv(local_csv, usecols=read_cols, low_memory=False)
        if "source" not in local.columns:
            local["source"] = "arborphy"
        frames.append(local)
        stats["local_rows"] = len(local)
        stats["has_local"] = True
    else:
        stats["local_rows"] = 0
        stats["has_local"] = False

    combined = pd.concat(frames, ignore_index=True)
    stats["total_before_filter"] = len(combined)

    # ── Drop rows without GPS (can't compute H3 without coords) ──────────────
    has_gps = combined["latitude"].notna() & combined["longitude"].notna()
    stats["dropped_no_gps"] = int((~has_gps).sum())
    df = combined[has_gps].copy()
    stats["total_rows"] = len(df)

    # ── H3 cells ─────────────────────────────────────────────────────────────
    lats = df["latitude"].tolist()
    lons = df["longitude"].tolist()
    for res in H3_RESOLUTIONS:
        df[f"h3_res{res}"] = [
            int(h3.latlng_to_cell(lat, lon, res), 16)
            for lat, lon in zip(lats, lons)
        ]

    return df, stats


def model(dbt, session):
    dbt.config(materialized="table")

    root      = _repo_root()
    data_dir  = root / "data"
    output_dir = root / "dbt" / "output"

    df, stats = merge_observations(data_dir)

    # ── Logging ──────────────────────────────────────────────────────────────
    if stats["has_local"]:
        print(f"stg_observations: merging {stats['local_rows']:,} local observations")
    else:
        print("stg_observations: no local_observations.csv found — iNat only")

    if stats["dropped_no_gps"]:
        print(f"stg_observations: dropped {stats['dropped_no_gps']} rows (no GPS)")

    output_dir.mkdir(exist_ok=True)
    df.to_csv(output_dir / "stg_observations.csv", index=False)
    print(
        f"stg_observations: wrote {stats['total_rows']:,} rows "
        f"(inat={stats['inat_rows']:,}, local={stats['local_rows']:,})"
    )
    return df
