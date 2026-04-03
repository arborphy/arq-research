"""Staging model: convert ecosite GeoJSON boundaries to res-13 H3 cells."""
import csv
import json
import os
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import h3
import pandas as pd
from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

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


def _to_polygon_geom(geom):
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        return unary_union(polys) if polys else None
    return None


def _process_geojson(path: pathlib.Path) -> tuple[str, list[int]]:
    """Process a single GeoJSON file → (ecosite_id, [cell_ints])."""
    ecosite_id = path.stem
    feature = json.loads(path.read_text())
    raw_geom = feature.get("geometry")
    if raw_geom is None:
        return ecosite_id, []

    geom = shape(raw_geom)
    if not geom.is_valid:
        geom = make_valid(geom)
    geom = _to_polygon_geom(geom)
    if geom is None:
        return ecosite_id, []

    try:
        cells = h3.geo_to_cells(mapping(geom), RESOLUTION)
        return ecosite_id, [int(c, 16) for c in cells]
    except Exception as e:
        print(f"  {ecosite_id}: skipped ({e})")
        return ecosite_id, []


def model(dbt, session):  # noqa: ARG001
    # Return a lightweight sentinel so DuckDB doesn't materialise 863M rows.
    # The real output is the CSV written to dbt/output/stg_ecosites.csv,
    # which stg_ecosites_compacted reads directly via read_csv_auto.
    dbt.config(materialized="table")

    root = _repo_root()
    output_dir = root / "dbt" / "output"
    geojson_dir = _arq_refdata(root) / "data" / "gis" / "ecosite_boundaries_merged"
    paths = sorted(geojson_dir.glob("*.geojson"))

    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / "stg_ecosites.csv"

    workers = min(os.cpu_count() or 4, len(paths))
    rows_written = 0
    ecosites_done = 0

    # Stream-write to CSV as each future completes — no full accumulation in memory.
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ecosite_id", "h3_res13"])

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_process_geojson, p): p.stem for p in paths}
            for future in as_completed(futures):
                ecosite_id, cells = future.result()
                if cells:
                    writer.writerows((ecosite_id, c) for c in cells)
                    rows_written += len(cells)
                ecosites_done += 1
                if ecosites_done % 10 == 0:
                    print(f"  {ecosites_done}/{len(paths)} ecosites processed, {rows_written:,} rows so far")

    print(f"stg_ecosites: wrote {rows_written:,} rows ({ecosites_done} ecosites, {workers} workers)")
    # Return a minimal sentinel — downstream models read the CSV directly.
    return pd.DataFrame({"ecosite_id": pd.Series([], dtype="str"), "h3_res13": pd.Series([], dtype="int64")})
