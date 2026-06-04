"""Snowflake upload helper for on-demand observation ingestion.

Mirrors the connection pattern and upsert semantics of
`scripts/upload_stg_observations.py` but factored into a reusable function
the FastAPI route can call directly.

Public surface:
    upload_observations(df, source_tag='gbif') -> dict

The upsert strategy is idempotent: existing rows with the same SOURCE tag
and matching IDs are deleted before insert, so re-running with the same
input is a no-op.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

log = logging.getLogger(__name__)

# ── Target — same as scripts/upload_stg_observations.py ────────────────────
# DEMON: These constants point at PRODUCTION. There is no environment switch
# (dev / staging / prod). Any execution path that imports this module and
# calls upload_observations() writes directly into the 23M-row baseline
# table. When you bring up a staging environment, parameterize these via
# environment variables and refuse to write to RAI_DEMO unless ARQ_ENV=prod.
#
# DEMON: These constants ALSO live in scripts/upload_stg_observations.py
# (the original location). If you change the warehouse, role, or table
# name, you must update both files. Factor into a shared module when this
# bites once.
ACCOUNT   = "WOTEIWV-MAC88464"
USER      = "valeriew"
WAREHOUSE = "TEAM_ARQ"
ROLE      = "team_arq"
DATABASE  = "RAI_DEMO"
SCHEMA    = "CB_WEBAPP"
TABLE     = "stg_observations"


def _read_pat() -> str:
    """Get the Snowflake PAT from env or the standard token file."""
    pat = os.environ.get("SNOWFLAKE_PAT")
    if pat:
        return pat.strip()
    token_file = Path(os.environ.get("SNOWFLAKE_PAT_FILE", "~/.config/snowflake/pat.token")).expanduser()
    if not token_file.exists():
        raise RuntimeError(
            f"Snowflake PAT not configured. Set SNOWFLAKE_PAT or place token at {token_file}"
        )
    return token_file.read_text().strip()


def _connect():
    return snowflake.connector.connect(
        account=ACCOUNT,
        user=USER,
        authenticator="programmatic_access_token",
        token=_read_pat(),
        warehouse=WAREHOUSE,
        database=DATABASE,
        schema=SCHEMA,
        role=ROLE,
    )


def upload_observations(df: pd.DataFrame, source_tag: str = "gbif") -> dict:
    """Upsert a DataFrame of observations into stg_observations.

    Args:
        df: DataFrame with stg_observations columns (uppercase). Must include
            ID, SOURCE, and all H3_RES* columns. The SOURCE column is forced
            to `source_tag` regardless of input.
        source_tag: Value to write to the SOURCE column. Also used as the
            scope for the pre-insert DELETE — only rows with this source AND
            matching IDs are deleted, so other data is never touched.

    Returns:
        Stats dict with keys:
            attempted, inserted, deleted_for_idempotency,
            rows_before, rows_after, snowflake_table
    """
    if df.empty:
        return {
            "attempted":                0,
            "inserted":                 0,
            "deleted_for_idempotency":  0,
            "rows_before":              None,
            "rows_after":               None,
            "snowflake_table":          f"{DATABASE}.{SCHEMA}.{TABLE}",
            "note":                     "input was empty",
        }

    # Force SOURCE column, just in case caller passed mixed values
    df = df.copy()
    df["SOURCE"] = source_tag

    target = f"{DATABASE}.{SCHEMA}.{TABLE}"
    log.info(f"[upload] connecting to {ACCOUNT} as {USER}...")
    conn = _connect()
    # DEMON: snowflake-connector-python defaults to autocommit=True. Without
    # explicitly disabling, each cur.execute("DELETE ...") commits before
    # write_pandas runs — if the INSERT then fails, the deleted rows are
    # gone forever. We open an explicit transaction so the DELETE+INSERT
    # pair is atomic. Note: write_pandas() internally does a PUT/COPY which
    # IS transactional within the same connection as of snowflake-connector
    # 2.7+; we still BEGIN/COMMIT/ROLLBACK around it to be safe.
    conn.autocommit(False)
    cur = conn.cursor()
    try:
        # Pre-check: row count (cheap, table metadata)
        cur.execute(f"SELECT COUNT(*) FROM {target}")
        rows_before = cur.fetchone()[0]

        # Idempotency: drop any prior rows we previously uploaded with this
        # source AND with IDs currently in our DataFrame. This keeps the
        # operation safe to re-run and prevents PK-style duplicates.
        # DEMON: The IN-list is scoped by SOURCE=%s so we can NEVER delete
        # rows uploaded by a different code path (e.g. iNat bulk load with
        # SOURCE='inat'). If you ever change the source_tag semantics, audit
        # this filter — a too-broad DELETE can wipe the 23M-row baseline.
        ids = df["ID"].astype(str).tolist()
        # Guard against empty-string IDs reaching the IN-list — would match
        # any existing rows with empty/null IDs and delete them silently.
        ids = [i for i in ids if i]
        deleted = 0
        if ids:
            # Snowflake supports IN with up to 16,384 elements. Chunk if needed.
            CHUNK = 5000
            for i in range(0, len(ids), CHUNK):
                chunk = ids[i:i + CHUNK]
                # Use parameterized binding to avoid quoting/injection issues.
                placeholders = ",".join(["%s"] * len(chunk))
                cur.execute(
                    f"DELETE FROM {target} WHERE SOURCE = %s AND ID IN ({placeholders})",
                    [source_tag, *chunk],
                )
                deleted += cur.rowcount

        log.info(f"[upload] inserting {len(df)} rows tagged SOURCE='{source_tag}'")
        success, nchunks, nrows, output = write_pandas(
            conn,
            df,
            table_name=TABLE.upper(),
            database=DATABASE,
            schema=SCHEMA,
            overwrite=False,
            auto_create_table=False,
            quote_identifiers=False,
        )
        if not success:
            raise RuntimeError(f"write_pandas failed: {output}")

        cur.execute(f"SELECT COUNT(*) FROM {target}")
        rows_after = cur.fetchone()[0]

        conn.commit()

        return {
            "attempted":                len(df),
            "inserted":                 nrows,
            "deleted_for_idempotency":  deleted,
            "rows_before":              rows_before,
            "rows_after":               rows_after,
            "snowflake_table":          target,
            "chunks":                   nchunks,
        }
    except Exception:
        # On ANY failure, roll back. The DELETEs above are now reversed and
        # the table is left in its pre-upload state.
        log.exception("[upload] failure during upsert; rolling back transaction")
        try:
            conn.rollback()
        except Exception:
            log.exception("[upload] rollback also failed")
        raise
    finally:
        cur.close()
        conn.close()
