"""Staging model: convert OSM trail ways to res-13 H3 cells with path interpolation."""
import json
import os
import pathlib

import h3
import pandas as pd

RESOLUTION = 13


def _repo_root() -> pathlib.Path:
    if "ARBORPHY_ROOT" in os.environ:
        return pathlib.Path(os.environ["ARBORPHY_ROOT"])
    for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents]:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("Set ARBORPHY_ROOT or run dbt from within the arborphy repo")


def _arq_refdata(repo_root: pathlib.Path) -> pathlib.Path:
    if "ARQ_REFDATA_DIR" in os.environ:
        return pathlib.Path(os.environ["ARQ_REFDATA_DIR"])
    return repo_root.parent / "arq-refdata"


def model(dbt, session):
    dbt.config(materialized="table")

    root = _repo_root()
    output_dir = root / "dbt" / "output"
    data_file = _arq_refdata(root) / "data" / "gis" / "wpr_trails_cache.json"

    data = json.loads(data_file.read_text())
    elements = data["elements"]

    nodes = {e["id"]: (e["lat"], e["lon"]) for e in elements if e["type"] == "node"}
    ways = [e for e in elements if e["type"] == "way"]

    rows = []
    for way in ways:
        tags = way.get("tags", {})
        osm_id = str(way["id"])
        seen_cells: set[int] = set()
        prev_cell = None

        for node_id in way.get("nodes", []):
            coord = nodes.get(node_id)
            if coord is None:
                continue
            lat, lon = coord
            cell_hex = h3.latlng_to_cell(lat, lon, RESOLUTION)
            path = h3.grid_path_cells(prev_cell, cell_hex) if prev_cell else [cell_hex]
            for c in path:
                cell_int = int(c, 16)
                if cell_int not in seen_cells:
                    seen_cells.add(cell_int)
                    rows.append({
                        "osm_id": osm_id,
                        "name": tags.get("name", ""),
                        "highway": tags.get("highway", ""),
                        "surface": tags.get("surface", ""),
                        "h3_res13": cell_int,
                    })
            prev_cell = cell_hex

    df = pd.DataFrame(rows)
    output_dir.mkdir(exist_ok=True)
    df.to_csv(output_dir / "stg_trail_cells.csv", index=False)
    print(f"stg_trail_cells: wrote {len(df):,} rows")
    return df
