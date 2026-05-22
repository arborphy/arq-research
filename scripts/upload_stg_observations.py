"""
upload_stg_observations.py — merge local + iNat observations and load to Snowflake.

Replaces the dbt run step for stg_observations when dbt cannot authenticate
via PAT (dbt-snowflake only supports oauth/jwt, not programmatic_access_token).
Uses snowflake-connector-python directly, which fully supports PAT.

Usage:
    SNOWFLAKE_PAT=$(cat ~/.config/snowflake/pat.token) \\
        python3 scripts/upload_stg_observations.py

    # Or with explicit paths:
    python3 scripts/upload_stg_observations.py \\
        --data-dir arq-research/data \\
        --token-file ~/.config/snowflake/pat.token

Loads into: RAI_DEMO.CB_WEBAPP.stg_observations
Uses CREATE OR REPLACE TABLE so schema changes (e.g. new SOURCE column) are
handled automatically — existing iNat observations are always re-merged.
"""

import argparse
import os
import sys
from pathlib import Path

# Make arq-research importable
_HERE = Path(__file__).resolve().parent
_ARQ_ROOT = _HERE.parent
sys.path.insert(0, str(_ARQ_ROOT))

import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

from dbt.models.staging.stg_observations import merge_observations

# ---------------------------------------------------------------------------
# Snowflake target
# ---------------------------------------------------------------------------
ACCOUNT   = "WOTEIWV-MAC88464"
USER      = "valeriew"
WAREHOUSE = "TEAM_ARQ"
ROLE      = "team_arq"
DATABASE  = "RAI_DEMO"
SCHEMA    = "CB_WEBAPP"
TABLE     = "stg_observations"


def connect(pat: str):
    return snowflake.connector.connect(
        account=ACCOUNT,
        user=USER,
        authenticator="programmatic_access_token",
        token=pat,
        warehouse=WAREHOUSE,
        database=DATABASE,
        schema=SCHEMA,
        role=ROLE,
    )


def _ensure_source_column(cur, target: str):
    """Add SOURCE VARCHAR column to the existing table if it doesn't exist."""
    cur.execute(f"SHOW COLUMNS IN TABLE {target}")
    cols = {row[2].upper() for row in cur.fetchall()}  # col[2] = column name
    if "SOURCE" not in cols:
        print(f"[upload] adding SOURCE column to {target}")
        cur.execute(f"ALTER TABLE {target} ADD COLUMN SOURCE VARCHAR(32)")
    else:
        print(f"[upload] SOURCE column already present in {target}")
    return "SOURCE" in cols


def upload(pat: str, data_dir: Path) -> dict:
    """Merge observations and load to Snowflake. Returns stats dict.

    Strategy (non-destructive — no CREATE TABLE required):
      1. Merge locally to get full DataFrame
      2. Connect to Snowflake
      3. Ensure SOURCE column exists (ALTER TABLE ADD COLUMN if missing)
      4. Backfill SOURCE='inat' on existing rows that have it null
      5. Delete any existing arborphy rows (idempotent re-run)
      6. INSERT only the arborphy local rows from the merged DataFrame
    """
    import pandas as pd

    # ── 1. Merge locally ────────────────────────────────────────────────────
    print(f"[upload] merging observations from {data_dir}")
    df, stats = merge_observations(data_dir)
    print(
        f"[upload] merged: inat={stats['inat_rows']:,} local={stats['local_rows']:,} "
        f"total={stats['total_rows']:,} dropped_no_gps={stats['dropped_no_gps']}"
    )

    local_df = df[df["source"] == "arborphy"].copy()
    if local_df.empty:
        print("[upload] no local observations to upload — local_observations.csv missing or empty")
        return stats

    local_df.columns = [c.upper() for c in local_df.columns]

    # ── 2. Connect ───────────────────────────────────────────────────────────
    print(f"[upload] connecting to {ACCOUNT} as {USER}...")
    conn = connect(pat)
    cur = conn.cursor()
    target = f"{DATABASE}.{SCHEMA}.{TABLE}"

    try:
        # ── 3. Verify table exists and row count ─────────────────────────────
        cur.execute(f"SELECT COUNT(*) FROM {target}")
        existing = cur.fetchone()[0]
        print(f"[upload] {target}: {existing:,} existing rows")

        # ── 4. Ensure SOURCE column ──────────────────────────────────────────
        _ensure_source_column(cur, target)

        # ── 5. Back-fill inat source on existing null rows ───────────────────
        cur.execute(f"UPDATE {target} SET SOURCE = 'inat' WHERE SOURCE IS NULL")
        backfilled = cur.rowcount
        if backfilled:
            print(f"[upload] backfilled SOURCE='inat' on {backfilled:,} existing rows")

        # ── 6. Remove any previous arborphy rows (idempotent) ────────────────
        cur.execute(f"DELETE FROM {target} WHERE SOURCE = 'arborphy'")
        deleted = cur.rowcount
        if deleted:
            print(f"[upload] removed {deleted} previous arborphy rows")

        # ── 7. INSERT 16 local rows ──────────────────────────────────────────
        print(f"[upload] inserting {len(local_df)} arborphy rows → {target} …")
        success, nchunks, nrows, output = write_pandas(
            conn,
            local_df,
            table_name=TABLE.upper(),
            database=DATABASE,
            schema=SCHEMA,
            overwrite=False,
            auto_create_table=False,
            quote_identifiers=False,
        )

        if not success:
            print(f"[upload] write_pandas returned failure: {output}", file=sys.stderr)
            sys.exit(1)

        # ── 8. Verify final count ────────────────────────────────────────────
        cur.execute(f"SELECT COUNT(*) FROM {target}")
        final_count = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM {target} WHERE SOURCE = 'arborphy'")
        arborphy_count = cur.fetchone()[0]

        stats.update({
            "snowflake_table":   target,
            "rows_before":       existing,
            "rows_after":        final_count,
            "arborphy_in_table": arborphy_count,
            "chunks":            nchunks,
            "upload_ok":         success,
        })

        print(
            f"[upload] ✓ {target}: {existing:,} → {final_count:,} rows "
            f"({arborphy_count} arborphy, rest inat)"
        )

    finally:
        cur.close()
        conn.close()

    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir",   type=Path, default=_ARQ_ROOT / "data")
    parser.add_argument("--token-file", type=Path, default=Path("~/.config/snowflake/pat.token").expanduser())
    args = parser.parse_args()

    pat = os.environ.get("SNOWFLAKE_PAT")
    if not pat:
        if not args.token_file.exists():
            print(f"Error: token file {args.token_file} not found and SNOWFLAKE_PAT not set", file=sys.stderr)
            sys.exit(1)
        pat = args.token_file.read_text().strip()

    if not args.data_dir.exists():
        print(f"Error: data dir {args.data_dir} not found", file=sys.stderr)
        sys.exit(1)

    upload(pat, args.data_dir)


if __name__ == "__main__":
    main()
