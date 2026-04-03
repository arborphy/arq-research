"""Upload processed CSV files to Snowflake.

Pass-through CSVs (data/) and generated CSVs (dbt/output/) are uploaded into
the target Snowflake schema. Credentials are read from ~/.dbt/profiles.yml.

Usage:
    python scripts/upload_to_snowflake.py                        # all tables
    python scripts/upload_to_snowflake.py --tables stg_trail_cells stg_observations
"""
import argparse
import os
import pathlib

import snowflake.connector
import yaml

REPO_ROOT = pathlib.Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "dbt" / "output"

DB = "RAI_DEMO"
SCHEMA = "CB_WEBAPP"

# (csv_path, [column_definitions])
TABLES: dict[str, tuple[pathlib.Path, list[str]]] = {
    "stg_newcomb_species": (
        DATA_DIR / "Newcomb_Species_Features_Consolidated.csv",
        [
            "newcomb_species_name VARCHAR",
            "species_inat VARCHAR",
            "subspecies_inat VARCHAR",
            "suggested_species_id VARCHAR",
            "species_page FLOAT",
            "key_page_range_start FLOAT",
            "key_page_range_end FLOAT",
            "key_group_number VARCHAR",
            "key_flower_type VARCHAR",
            "key_plant_type VARCHAR",
            "key_leaf_type VARCHAR",
            "key_subgroup_1 VARCHAR",
            "key_subgroup_2 VARCHAR",
            "key_subgroup_3 VARCHAR",
            "key_description VARCHAR",
            "species_inat_link VARCHAR",
            "subspecies_inat_link VARCHAR",
            "warning_species_extraction FLOAT",
            "warning_key_extraction FLOAT",
        ],
    ),
    "stg_observations": (
        OUTPUT_DIR / "stg_observations.csv",
        [
            "id VARCHAR",
            "uuid VARCHAR",
            "scientific_name VARCHAR",
            "common_name VARCHAR",
            "taxon_id VARCHAR",
            "iconic_taxon_name VARCHAR",
            "observed_on DATE",
            "time_observed_at VARCHAR",
            "latitude FLOAT",
            "longitude FLOAT",
            "positional_accuracy FLOAT",
            "coordinates_obscured BOOLEAN",
            "image_url VARCHAR",
            "url VARCHAR",
            "quality_grade VARCHAR",
            "num_identification_agreements INTEGER",
            "num_identification_disagreements INTEGER",
            "captive_cultivated BOOLEAN",
            "place_guess VARCHAR",
            "species_guess VARCHAR",
            "description VARCHAR",
            "license VARCHAR",
            "h3_res7 NUMBER(38,0)",
            "h3_res9 NUMBER(38,0)",
            "h3_res12 NUMBER(38,0)",
            "h3_res13 NUMBER(38,0)",
        ],
    ),
    "stg_ecosites": (
        OUTPUT_DIR / "stg_ecosites.csv",
        [
            "ecosite_id VARCHAR",
            "h3_res13 NUMBER(38,0)",
        ],
    ),
    "stg_ecosites_compacted": (
        OUTPUT_DIR / "stg_ecosites_compacted.csv",
        [
            "ecosite_id VARCHAR",
            "h3_cell NUMBER(38,0)",
        ],
    ),
    "stg_trail_cells": (
        OUTPUT_DIR / "stg_trail_cells.csv",
        [
            "osm_id VARCHAR",
            "name VARCHAR",
            "highway VARCHAR",
            "surface VARCHAR",
            "h3_res13 NUMBER(38,0)",
        ],
    ),
}


def get_connection():
    profile_name = os.environ.get("DBT_PROFILE", "default")
    profiles = yaml.safe_load((pathlib.Path.home() / ".dbt" / "profiles.yml").read_text())
    dev = profiles[profile_name]["outputs"]["dev"]
    kwargs = dict(
        account=dev["account"],
        user=dev["user"],
        role=dev.get("role"),
        warehouse=dev.get("warehouse"),
        database=DB,
        schema=SCHEMA,
    )
    if "token" in dev:
        kwargs["authenticator"] = dev["authenticator"]
        kwargs["token"] = dev["token"]
    else:
        kwargs["password"] = dev["password"]
    return snowflake.connector.connect(**kwargs)


def upload_table(cur, table: str, csv_path: pathlib.Path, columns: list[str]):
    if not csv_path.exists():
        print(f"  [{table}] skipping — {csv_path} not found")
        return

    size_mb = csv_path.stat().st_size / 1e6
    print(f"\n[{table}] {csv_path.name} ({size_mb:.1f} MB)")

    col_defs = ",\n        ".join(columns)
    cur.execute(f"CREATE OR REPLACE TABLE {DB}.{SCHEMA}.{table} (\n        {col_defs}\n    )")

    cur.execute(
        f"PUT 'file://{csv_path}' @%{table} "
        f"AUTO_COMPRESS=TRUE OVERWRITE=TRUE PARALLEL=8"
    )
    for row in cur.fetchall():
        print(f"  put: {row[0]} → {row[1]}")

    cur.execute(f"""
        COPY INTO {DB}.{SCHEMA}.{table}
        FROM @%{table}
        FILE_FORMAT = (
            TYPE = CSV
            PARSE_HEADER = TRUE
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            NULL_IF = ('', 'NULL', 'None')
        )
        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
    """)
    for row in cur.fetchall():
        print(f"  copy: {row}")

    cur.execute(f"ALTER TABLE {DB}.{SCHEMA}.{table} SET CHANGE_TRACKING = TRUE")
    cur.execute(f"SELECT COUNT(*) FROM {DB}.{SCHEMA}.{table}")
    print(f"  loaded: {cur.fetchone()[0]:,} rows")


def main():
    parser = argparse.ArgumentParser(description="Upload CSVs to Snowflake")
    parser.add_argument(
        "--tables", nargs="+", choices=list(TABLES.keys()), default=list(TABLES.keys()),
        metavar="TABLE", help="Tables to upload (default: all)",
    )
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()
    try:
        for name in args.tables:
            csv_path, columns = TABLES[name]
            upload_table(cur, name, csv_path, columns)
    finally:
        cur.close()
        conn.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
