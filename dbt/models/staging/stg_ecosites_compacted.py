"""Staging model: compact res-13 H3 cells per ecosite using h3.compact_cells."""
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


def model(dbt, session):
    dbt.config(materialized="table")

    root = _repo_root()
    output_dir = root / "dbt" / "output"
    ecosites_csv = output_dir / "stg_ecosites.csv"

    dbt.ref("stg_ecosites")  # declare dependency so dbt runs stg_ecosites first

    # Read directly from the CSV — avoids materialising 863M rows into DuckDB.
    result = session.execute(f"""
        SELECT ecosite_id, list(h3_res13::bigint)
        FROM read_csv_auto('{ecosites_csv}')
        GROUP BY ecosite_id
        ORDER BY ecosite_id
    """)

    rows = []
    for ecosite_id, cell_ints in result.fetchall():
        cells_hex = [format(c, "x") for c in cell_ints]
        for cell in h3.compact_cells(cells_hex):
            rows.append({"ecosite_id": ecosite_id, "h3_cell": int(cell, 16)})

    df = pd.DataFrame(rows, columns=["ecosite_id", "h3_cell"])
    output_dir.mkdir(exist_ok=True)
    df.to_csv(output_dir / "stg_ecosites_compacted.csv", index=False)
    print(f"stg_ecosites_compacted: wrote {len(df):,} rows")
    return df
