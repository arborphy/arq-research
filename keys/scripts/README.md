# Trait Data Loading Scripts

## Overview

Scripts for loading and validating botanical trait data for the ARQ Knowledge Graph.

## Scripts

### `load_traits_to_snowflake.py`

Loads trait JSON files to Snowflake as VARIANT columns for downstream processing.

**What it does:**
1. Reads Snowflake connection details (including password) from `raiconfig.toml`
2. Creates raw staging tables with VARIANT columns:
   - `TRAIT_NEWCOMB_RAW` - Newcomb wildflower trait ontology
   - `TRAIT_SYNONYMS_RAW` - Botanical synonym sources and definitions
3. Loads JSON files as VARIANT objects (full refresh)

**Usage:**

```bash
# Ensure your raiconfig.toml has password configured
# Then run the script
python keys/scripts/load_traits_to_snowflake.py
```

**Requirements:**
- Python 3.11+ (uses built-in `tomllib`)
- `snowflake-connector-python` (installed via `dbt-snowflake`)
- Valid `raiconfig.toml` with `default` profile and `password` field

**Next Steps:**
After loading, run dbt to flatten the VARIANT data:
```bash
dbt run --select staging.trait_*
```

### `traits_checks.py`

Validates trait synonym JSON files and checks for consistency.

**Usage:**
```bash
# Run all checks
python keys/scripts/traits_checks.py all

# Individual checks
python keys/scripts/traits_checks.py validate-json
python keys/scripts/traits_checks.py check-sources --verbose
python keys/scripts/traits_checks.py check-coverage
python keys/scripts/traits_checks.py scan-usage
```

## File Structure

```
keys/
├── Newcomb_refined.json       # Trait ontology (loaded to Snowflake)
├── trait_synonyms.json        # Synonym definitions (loaded to Snowflake)
└── scripts/
    ├── load_traits_to_snowflake.py  # Snowflake loader
    ├── traits_checks.py             # Validation script
    └── README.md                     # This file
```

## Data Flow

```
JSON Files
    ↓ (load_traits_to_snowflake.py)
CHAKER_TEMP.PUBLIC.*_RAW (VARIANT)
    ↓ (dbt models)
CHAKER_TEMP.PUBLIC.TRAIT_* (flattened tables)
    ↓ (kg/model/core/trait.py)
RelationalAI Knowledge Graph
```
