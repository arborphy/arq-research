"""Staging model: compute H3 cells at 4 resolutions from iNaturalist observations."""
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


def model(dbt, session):
    dbt.config(materialized="table")

    root = _repo_root()
    output_dir = root / "dbt" / "output"
    data_csv = root / "data" / "observations.csv"

    df = pd.read_csv(data_csv, usecols=COLS, low_memory=False)
    df = df[df["latitude"].notna() & df["longitude"].notna()].copy()

    lats = df["latitude"].tolist()
    lons = df["longitude"].tolist()
    for res in [7, 9, 12, 13]:
        df[f"h3_res{res}"] = [
            int(h3.latlng_to_cell(lat, lon, res), 16)
            for lat, lon in zip(lats, lons)
        ]

    output_dir.mkdir(exist_ok=True)
    df.to_csv(output_dir / "stg_observations.csv", index=False)
    print(f"stg_observations: wrote {len(df):,} rows")
    return df
