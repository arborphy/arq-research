"""Upload GoBotany parquet files to Snowflake.

Reads parquet files from the arq-refdata repo sibling directory and loads them
into RAI_DEMO.CB_WEBAPP via Snowflake PUT + COPY INTO (parquet format).
After upload, creates a denormalised view used by the RAI loader.

Usage:
    python scripts/upload_gobotany.py                        # all tables + view
    python scripts/upload_gobotany.py --tables gobotany_taxon gobotany_character
    python scripts/upload_gobotany.py --no-view              # skip view creation
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
    "gobotany_taxon": (
        PARQUET_DIR / "gobotany_taxon.parquet",
        [
            "taxon_id INTEGER",
            "pile_slug VARCHAR",
            "scientific_name VARCHAR",
            "common_name VARCHAR",
            "genus VARCHAR",
            "family VARCHAR",
            "taxonomic_authority VARCHAR",
            "species_url VARCHAR",
        ],
    ),
    "gobotany_character": (
        PARQUET_DIR / "gobotany_character.parquet",
        [
            "character_id INTEGER",
            "pile_slug VARCHAR",
            "character_short_name VARCHAR",
            "friendly_name VARCHAR",
            "character_group VARCHAR",
            "question VARCHAR",
            "hint VARCHAR",
            "image_url VARCHAR",
            "unit VARCHAR",
            "value_type VARCHAR",
        ],
    ),
    "gobotany_character_value_label": (
        PARQUET_DIR / "gobotany_character_value_label.parquet",
        [
            "pile_slug VARCHAR",
            "character_short_name VARCHAR",
            "value_type VARCHAR",
            "value_index INTEGER",
            "choice VARCHAR",
            "display_label VARCHAR",
            "friendly_text VARCHAR",
            "value_range_min FLOAT",
            "value_range_max FLOAT",
            "scalar FLOAT",
            "image_url VARCHAR",
            "taxa_count_api INTEGER",
        ],
    ),
    "gobotany_taxon_character_value": (
        PARQUET_DIR / "gobotany_taxon_character_value.parquet",
        [
            "taxon_id INTEGER",
            "pile_slug VARCHAR",
            "character_short_name VARCHAR",
            "character_name VARCHAR",
            "character_group VARCHAR",
            "ease INTEGER",
            "value_type VARCHAR",
            "value_index INTEGER",
        ],
    ),
    "gobotany_pile": (
        PARQUET_DIR / "gobotany_pile.parquet",
        [
            "pile_id INTEGER",
            "pile_name VARCHAR",
            "pile_slug VARCHAR",
            "pile_friendly_name VARCHAR",
            "description VARCHAR",
            "character_group_count INTEGER",
            "default_filter_count INTEGER",
            "preview_character_count INTEGER",
            "resource_uri VARCHAR",
        ],
    ),
    "gobotany_pile_group": (
        PARQUET_DIR / "gobotany_pile_group.parquet",
        [
            "pile_group_id INTEGER",
            "pilegroup_name VARCHAR",
            "pilegroup_friendly_name VARCHAR",
            "key_characteristics VARCHAR",
            "notable_exceptions VARCHAR",
            "resource_uri VARCHAR",
            "default_image VARCHAR",
        ],
    ),
    "gobotany_character_discriminative_power": (
        PARQUET_DIR / "gobotany_character_discriminative_power.parquet",
        [
            "pile_slug VARCHAR",
            "character_short_name VARCHAR",
            "character_name VARCHAR",
            "character_group VARCHAR",
            "ease INTEGER",
            "num_value_buckets INTEGER",
            "total_taxa_covered FLOAT",
            "max_bucket_taxa INTEGER",
            "min_bucket_taxa INTEGER",
            "shannon_entropy FLOAT",
            "evenness_score FLOAT",
            "discrimination_score FLOAT",
        ],
    ),
}

# Denormalised view joining taxon + taxon_character_value + character_value_label.
# Used by the RAI loader to avoid multi-table joins in Datalog.
SPECIES_FEATURE_VALUES_VIEW = f"""
CREATE OR REPLACE VIEW {DB}.{SCHEMA}.gobotany_species_feature_values AS
SELECT
    t.scientific_name,
    tcv.pile_slug,
    tcv.character_short_name,
    tcv.value_index,
    cvl.choice
FROM {DB}.{SCHEMA}.gobotany_taxon t
JOIN {DB}.{SCHEMA}.gobotany_taxon_character_value tcv
    ON t.taxon_id = tcv.taxon_id
JOIN {DB}.{SCHEMA}.gobotany_character_value_label cvl
    ON  tcv.pile_slug            = cvl.pile_slug
    AND tcv.character_short_name = cvl.character_short_name
    AND tcv.value_index          = cvl.value_index
WHERE cvl.choice IS NOT NULL
"""


def get_connection():
    config_path = REPO_ROOT / "raiconfig.yaml"
    config = yaml.safe_load(config_path.read_text())
    conn_name = config.get("default_connection", "sf")
    sf = config["connections"][conn_name]
    return snowflake.connector.connect(
        account=sf["account"],
        user=sf["user"],
        role=sf.get("role"),
        warehouse=sf.get("warehouse"),
        authenticator=sf.get("authenticator"),
        token=sf.get("token"),
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


def create_view(cur, dry_run: bool = False):
    print("\n[view] gobotany_species_feature_values")
    if dry_run:
        print(f"  sql: {SPECIES_FEATURE_VALUES_VIEW.strip()}")
        return
    cur.execute(SPECIES_FEATURE_VALUES_VIEW)
    cur.execute(f"SELECT COUNT(*) FROM {DB}.{SCHEMA}.gobotany_species_feature_values")
    print(f"  rows: {cur.fetchone()[0]:,}")


def main():
    parser = argparse.ArgumentParser(description="Upload GoBotany parquets to Snowflake")
    parser.add_argument(
        "--tables", nargs="+", choices=list(TABLES.keys()), default=list(TABLES.keys()),
        metavar="TABLE", help="Tables to upload (default: all)",
    )
    parser.add_argument("--no-view", action="store_true", help="Skip view creation")
    parser.add_argument("--dry-run", action="store_true", help="Print operations without executing")
    args = parser.parse_args()

    if args.dry_run:
        print("[dry-run] no Snowflake connection will be made\n")
        for name in args.tables:
            parquet_path, columns = TABLES[name]
            upload_table(None, name, parquet_path, columns, dry_run=True)
        if not args.no_view:
            create_view(None, dry_run=True)
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
        if not args.no_view:
            create_view(cur)
    finally:
        cur.close()
        conn.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
