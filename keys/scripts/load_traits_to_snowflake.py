#!/usr/bin/env python3
"""
Load trait JSON files to Snowflake as VARIANT columns.

This script:
1. Reads Snowflake connection details (including password) from raiconfig.toml
2. Creates raw staging tables with VARIANT columns
3. Loads Newcomb_refined.json and trait_synonyms.json as VARIANT objects
4. Uses full refresh strategy (CREATE OR REPLACE + INSERT)

The data will later be flattened by dbt models for use in RelationalAI KG.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import tomli
except ImportError:
    import tomllib as tomli

import snowflake.connector
from snowflake.connector import SnowflakeConnection


# Paths
HERE = Path(__file__).resolve().parent
KEYS_DIR = HERE.parent
ROOT = KEYS_DIR.parent
RAICONFIG_PATH = ROOT / "raiconfig.toml"
NEWCOMB_JSON = KEYS_DIR / "Newcomb_refined.json"
SYNONYMS_JSON = KEYS_DIR / "trait_synonyms.json"

# Snowflake configuration
DATABASE = "CHAKER_TEMP"
SCHEMA = "PUBLIC"
NEWCOMB_TABLE = "TRAIT_NEWCOMB_RAW"
SYNONYMS_TABLE = "TRAIT_SYNONYMS_RAW"


def load_raiconfig(profile: str = "default") -> Dict[str, Any]:
    """Load Snowflake connection configuration from raiconfig.toml."""
    if not RAICONFIG_PATH.exists():
        print(f"ERROR: raiconfig.toml not found at {RAICONFIG_PATH}", file=sys.stderr)
        print("Please create raiconfig.toml from raiconfig.example.toml", file=sys.stderr)
        sys.exit(1)

    with open(RAICONFIG_PATH, "rb") as f:
        config = tomli.load(f)

    if profile not in config.get("profile", {}):
        print(f"ERROR: Profile '{profile}' not found in raiconfig.toml", file=sys.stderr)
        sys.exit(1)

    return config["profile"][profile]


def get_snowflake_connection(config: Dict[str, Any]) -> SnowflakeConnection:
    """Create Snowflake connection from config.

    All credentials are read from raiconfig.toml.
    """
    # Get password from config
    password = config.get("password", "")

    if not password:
        print("ERROR: No password found in raiconfig.toml", file=sys.stderr)
        print("Please add 'password' to your profile in raiconfig.toml", file=sys.stderr)
        sys.exit(1)

    conn_params = {
        "user": config["user"],
        "password": password,
        "account": config["account"],
        "warehouse": config["warehouse"],
        "database": DATABASE,
        "schema": SCHEMA,
        "role": config["role"],
        "authenticator": config.get("authenticator", "snowflake"),
    }

    return snowflake.connector.connect(**conn_params)


def load_json_file(path: Path) -> str:
    """Load JSON file and return as string."""
    if not path.exists():
        print(f"ERROR: JSON file not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert back to string for PARSE_JSON
    return json.dumps(data)


def create_raw_table(conn: SnowflakeConnection, table_name: str, description: str) -> None:
    """Create or replace raw staging table with VARIANT column."""
    ddl = f"""
    CREATE OR REPLACE TABLE {DATABASE}.{SCHEMA}.{table_name} (
        loaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
        json_data VARIANT
    )
    COMMENT = '{description}'
    """

    with conn.cursor() as cur:
        cur.execute(ddl)
        print(f"✓ Created table {DATABASE}.{SCHEMA}.{table_name}")


def load_json_to_table(
    conn: SnowflakeConnection,
    table_name: str,
    json_str: str,
    description: str
) -> None:
    """Load JSON string into table as VARIANT."""
    # Insert using PARSE_JSON
    insert_sql = f"""
    INSERT INTO {DATABASE}.{SCHEMA}.{table_name} (json_data)
    SELECT PARSE_JSON(%s)
    """

    with conn.cursor() as cur:
        cur.execute(insert_sql, (json_str,))
        print(f"✓ Loaded {description} into {table_name} ({len(json_str):,} bytes)")


def main() -> int:
    """Main execution function."""
    print("=" * 60)
    print("Loading Trait JSON files to Snowflake")
    print("=" * 60)
    print()

    # Load configuration
    print(f"Reading configuration from {RAICONFIG_PATH}")
    config = load_raiconfig()
    print(f"✓ Using profile: default")
    print(f"  - Account: {config['account']}")
    print(f"  - User: {config['user']}")
    print(f"  - Role: {config['role']}")
    print(f"  - Warehouse: {config['warehouse']}")
    print(f"  - Target: {DATABASE}.{SCHEMA}")
    print()

    # Connect to Snowflake
    print("Connecting to Snowflake...")
    try:
        conn = get_snowflake_connection(config)
        print("✓ Connected successfully")
        print()
    except Exception as e:
        print(f"ERROR: Failed to connect to Snowflake: {e}", file=sys.stderr)
        return 1

    try:
        # Load JSON files
        print("Loading JSON files...")
        newcomb_json = load_json_file(NEWCOMB_JSON)
        print(f"✓ Loaded {NEWCOMB_JSON.name} ({len(newcomb_json):,} bytes)")

        synonyms_json = load_json_file(SYNONYMS_JSON)
        print(f"✓ Loaded {SYNONYMS_JSON.name} ({len(synonyms_json):,} bytes)")
        print()

        # Create tables
        print("Creating/replacing raw tables...")
        create_raw_table(
            conn,
            NEWCOMB_TABLE,
            "Raw Newcomb wildflower trait ontology - loaded as VARIANT"
        )
        create_raw_table(
            conn,
            SYNONYMS_TABLE,
            "Raw botanical trait synonym sources and definitions - loaded as VARIANT"
        )
        print()

        # Load data
        print("Loading JSON data to Snowflake...")
        load_json_to_table(conn, NEWCOMB_TABLE, newcomb_json, "Newcomb traits")
        load_json_to_table(conn, SYNONYMS_TABLE, synonyms_json, "Trait synonyms")
        print()

        print("=" * 60)
        print("✓ Successfully loaded all trait data to Snowflake!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run dbt models to flatten the VARIANT data:")
        print("     dbt run --select staging.trait_*")
        print("  2. The flattened tables will be available for RAI KG ingestion")
        print()

        return 0

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    finally:
        conn.close()
        print("✓ Connection closed")


if __name__ == "__main__":
    sys.exit(main())
