"""Upload GoBotany parquet files to Snowflake.

Reads parquet files from the arq-refdata repo sibling directory and loads them
into RAI_DEMO.CB_WEBAPP via Snowflake PUT + COPY INTO (parquet format).

Tables loaded (v2 uniform claim model):
    gobotany_source_meta, gobotany_taxon, gobotany_feature,
    gobotany_feature_value, gobotany_feature_value_definition,
    gobotany_taxon_feature_value

Usage:
    python scripts/upload_gobotany.py                        # all tables
    python scripts/upload_gobotany.py --tables gobotany_taxon gobotany_feature
    python scripts/upload_gobotany.py --dry-run              # print ops, no execution
"""
import argparse
import pathlib

import snowflake.connector
import yaml

REPO_ROOT = pathlib.Path(__file__).parent.parent
REFDATA_ROOT = REPO_ROOT.parent / "arq-refdata"
PARQUET_DIR = REFDATA_ROOT / "hierarchy_etl" / "data" / "parquet_models"

DB = "RAI_DEMO"
SCHEMA = "CB_WEBAPP"

# (parquet_path, [column_definitions])
TABLES: dict[str, tuple[pathlib.Path, list[str]]] = {
    "gobotany_source_meta": (
        PARQUET_DIR / "gobotany_source_meta.parquet",
        [
            "source_id VARCHAR",
            "source_title VARCHAR",
            "source_type VARCHAR",
            "source_url VARCHAR",
            "api_base_url VARCHAR",
            "pile_slug VARCHAR",
            "extraction_method VARCHAR",
            "extracted_at_utc VARCHAR",
            "taxa_in_scope INTEGER",
            "features_in_scope INTEGER",
            "orphan_taxon_ids VARCHAR",
            "orphan_taxon_assertion_count INTEGER",
            "notes VARCHAR",
        ],
    ),
    "gobotany_taxon": (
        PARQUET_DIR / "gobotany_taxon.parquet",
        [
            "taxon_id INTEGER",
            "source_taxon_id VARCHAR",
            "scientific_name VARCHAR",
            "common_name VARCHAR",
            "genus VARCHAR",
            "family VARCHAR",
            "taxonomic_authority VARCHAR",
            "species_url VARCHAR",
        ],
    ),
    "gobotany_feature": (
        PARQUET_DIR / "gobotany_feature.parquet",
        [
            "feature_id VARCHAR",
            "source_feature_name VARCHAR",
            "display_name VARCHAR",
            "feature_group VARCHAR",
            "question VARCHAR",
            "hint VARCHAR",
            "value_type VARCHAR",
            "unit VARCHAR",
            "image_url VARCHAR",
            "is_default_filter BOOLEAN",
            "is_preview_character BOOLEAN",
        ],
    ),
    "gobotany_feature_value": (
        PARQUET_DIR / "gobotany_feature_value.parquet",
        [
            "feature_value_id VARCHAR",
            "feature_id VARCHAR",
            "value_index INTEGER",
            "value_label VARCHAR",
            "display_label VARCHAR",
            "value_range_min FLOAT",
            "value_range_max FLOAT",
            "scalar FLOAT",
            "image_url VARCHAR",
            "taxa_count_in_bucket INTEGER",
        ],
    ),
    "gobotany_feature_value_definition": (
        PARQUET_DIR / "gobotany_feature_value_definition.parquet",
        [
            "definition_id VARCHAR",
            "feature_value_id VARCHAR",
            "definition_text VARCHAR",
            "definition_type VARCHAR",
        ],
    ),
    "gobotany_taxon_feature_value": (
        PARQUET_DIR / "gobotany_taxon_feature_value.parquet",
        [
            "taxon_id INTEGER",
            "feature_id VARCHAR",
            "feature_value_id VARCHAR",
            "value_index INTEGER",
            "value_type VARCHAR",
            "ease INTEGER",
            "character_group VARCHAR",
            "is_cross_pile_taxon BOOLEAN",
        ],
    ),
}


def get_connection():
    config_path = REPO_ROOT / "raiconfig.yaml"
    config = yaml.safe_load(config_path.read_text())
    conn_name = config.get("default_connection", "sf")
    sf = config["connections"][conn_name]
    token = sf.get("token") or pathlib.Path(sf["token_file_path"]).read_text().strip()
    return snowflake.connector.connect(
        account=sf["account"],
        user=sf["user"],
        role=sf.get("role"),
        warehouse=sf.get("warehouse"),
        authenticator=sf.get("authenticator"),
        token=token,
        database=DB,
        schema=SCHEMA,
    )


def upload_table(cur, table: str, parquet_path: pathlib.Path, columns: list[str], dry_run: bool = False):
    if not parquet_path.exists():
        print(f"  [{table}] skipping — {parquet_path} not found")
        return

    size_mb = parquet_path.stat().st_size / 1e6
    col_defs = ",\n        ".join(columns)
    create_sql = f"CREATE OR REPLACE TABLE {DB}.{SCHEMA}.{table} (\n        {col_defs}\n    )"
    put_sql = f"PUT 'file://{parquet_path}' @%{table} AUTO_COMPRESS=FALSE OVERWRITE=TRUE PARALLEL=8"
    copy_sql = (
        f"COPY INTO {DB}.{SCHEMA}.{table} FROM @%{table} "
        f"FILE_FORMAT = (TYPE = PARQUET SNAPPY_COMPRESSION = TRUE) "
        f"MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE"
    )
    tracking_sql = f"ALTER TABLE {DB}.{SCHEMA}.{table} SET CHANGE_TRACKING = TRUE"

    print(f"\n[{table}] {parquet_path.name} ({size_mb:.1f} MB)")
    if dry_run:
        print(f"  sql: {create_sql}")
        print(f"  sql: {put_sql}")
        print(f"  sql: {copy_sql}")
        print(f"  sql: {tracking_sql}")
        return

    cur.execute(create_sql)
    cur.execute(put_sql)
    for row in cur.fetchall():
        print(f"  put: {row[0]} → {row[1]}")
    cur.execute(copy_sql)
    for row in cur.fetchall():
        print(f"  copy: {row}")
    cur.execute(tracking_sql)
    cur.execute(f"SELECT COUNT(*) FROM {DB}.{SCHEMA}.{table}")
    print(f"  loaded: {cur.fetchone()[0]:,} rows")


def main():
    parser = argparse.ArgumentParser(description="Upload GoBotany parquets to Snowflake")
    parser.add_argument(
        "--tables", nargs="+", choices=list(TABLES.keys()), default=list(TABLES.keys()),
        metavar="TABLE", help="Tables to upload (default: all)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print operations without executing")
    args = parser.parse_args()

    if args.dry_run:
        print("[dry-run] no Snowflake connection will be made\n")
        for name in args.tables:
            parquet_path, columns = TABLES[name]
            upload_table(None, name, parquet_path, columns, dry_run=True)
        print("\nDone.")
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"USE DATABASE {DB}")
    cur.execute(f"USE SCHEMA {DB}.{SCHEMA}")
    try:
        for name in args.tables:
            parquet_path, columns = TABLES[name]
            upload_table(cur, name, parquet_path, columns)
    finally:
        cur.close()
        conn.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
