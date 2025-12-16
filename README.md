# ARQ Starter

Contains 
- [SnowSQL scripts](/script) for uploading source data
- [DBT models](/dbt/models) for preprocessing and documenting source data 
  - https://github.com/dbt-labs/dbt-core
- [RAI model](/kg/model) for building semantics and queries
  - https://private.relational.ai/early-access/pyrel
  - https://private.relational.ai/manage/install

## Setup

Requires [uv](https://github.com/astral-sh/uv) for python runtime management.
Assumes RAI Native App has been installed and configured.

```bash
uv sync

# input Snowflake config
# if using user/pass auth, you can leave fields after schema blank
# https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/configure-cli
uvx --from snowflake-cli snow connection add
uvx --from snowflake-cli snow connection set-default <name>

# Programmatic Access Tokens (PAT)
# Snowflake supports using a PAT secret anywhere you'd normally paste a password.
# Prereq: your user must be subject to a network policy to *use* a PAT (and service
# users must be subject to a network policy to *generate* one).
# https://docs.snowflake.com/en/user-guide/programmatic-access-tokens
#
# If you have `ACCOUNTADMIN`, the usual setup is:
#
# 1) Create a network policy that allows your IPs (recommended), then attach it to your user.
#    NOTE: adjust IPs to match your NAT/egress; if you're on a dynamic IP/VPN, include the
#    right ranges.
#
#    CREATE NETWORK POLICY arq_pat_policy
#      ALLOWED_IP_LIST = ('203.0.113.10/32')
#      COMMENT = 'Allow PAT usage from approved egress IPs';
#
#    ALTER USER <your_user> SET NETWORK_POLICY = arq_pat_policy;
#
# 2) If you use an authentication policy that restricts allowed methods, ensure it includes
#    PROGRAMMATIC_ACCESS_TOKEN:
#
#    ALTER AUTHENTICATION POLICY <your_auth_policy>
#      SET AUTHENTICATION_METHODS = ('OAUTH', 'PASSWORD', 'PROGRAMMATIC_ACCESS_TOKEN');
#
# Suggested pattern:
# - Generate a PAT in Snowsight (Governance & security → Users & roles → <user> → Programmatic access tokens)
# - Store it in a secrets manager or environment variable (do not commit it)
# - Use it as the “password” for:
#   - Snowflake CLI connections
#   - dbt profiles (password: "{{ env_var('SNOWFLAKE_PAT') }}")
#   - `raiconfig.toml` used by `rai` / this repo (see `raiconfig.example.toml`)

# Quickstart (recommended)
# Use the setup script to:
# - save your PAT secret locally (not in git)
# - generate `raiconfig.toml` without embedding secrets
# - print the env vars to use the PAT with this repo + snowflake-cli
#
#   ./script/setup_pat.sh \
#     --user <your_user> \
#     --account <your_account_identifier> \
#     --role <your_role> \
#     --warehouse <your_warehouse> \
#     --snow-connection <pat_connection_name>
#
# Optional (only if you need to change Snowflake-side policy prerequisites):
#   --admin-connection <accountadmin_connection_name>

# create ARQ role, db, and warehouse. the code assumes these exist
uvx --from snowflake-cli snow sql -f script/team_arq.sql

# GBIF Backbone Taxonomy
# https://drive.google.com/file/d/19KbBCcfZ5Mpwbo4y9UdO3nDMBL_7yAUp/view?usp=drive_link
# download & unzip this file, and give the script the full path to the folder
# it will create tables in team_arq.source from the given data
uvx --from snowflake-cli snow sql -f script/gbif_backbone.sql -D "path=/Users/agarrard/arq/data/backbone"

# GBIF Observation
# https://drive.google.com/file/d/1DZHHo08eJnVG-Eju5t-n6ECK6MDUyHNV/view?usp=drive_link
# download & unzip this file, and give the script the full path to the file
uvx --from snowflake-cli snow sql -f script/gbif_observation.sql -D "path=/Users/agarrard/arq/data/gbif_observation.csv"

# Plants (SQLite → Snowflake)
# This repo includes a local SQLite database `plants.db`. To use this data in Snowflake + dbt:
#
# 1) Export CSVs from SQLite (writes to ./.local/plants_csv, which is gitignored)
python script/export_plants_sqlite_to_csv.py --db ./plants.db

# 2) Load raw tables into team_arq.source (SnowSQL)
uvx --from snowflake-cli snow sql -f script/plants.sql -D "path=./.local/plants_csv"

# 3) Build dbt staging tables (materialized in team_arq.public)
uv run dbt build --select plants plant_characteristics plant_native_statuses plant_traits

# Optional: if you host the CSVs at static URLs (e.g. Google Drive direct download links)
# you can load from links instead of exporting locally:
#   export PLANTS_CSV_URL='https://.../plants.csv'
#   export PLANT_CHARACTERISTICS_CSV_URL='https://.../plant_characteristics.csv'
#   export PLANT_NATIVE_STATUSES_CSV_URL='https://.../plant_native_statuses.csv'
#   ./script/load_plants_from_links.sh
#
# Note: `./script/load_plants_from_links.sh` is also pre-configured with default
# Google Drive file IDs for this repo; if those links remain valid, you can run it
# without setting any env vars.

# DBT
# create a config file https://docs.getdbt.com/docs/core/connect-data-platform/snowflake-setup
# dbt_project.yaml assumes a profile named "default".
# This repo includes a repo-local `./profiles.yml` (gitignored) that is configured
# for PAT auth (no interactive prompts) by reading the `password` env var.
#
# Recommended: use the wrapper so dbt picks up the repo-local profile automatically:
#   export SNOWFLAKE_PAT_FILE="$HOME/.config/snowflake/pat.token"
#   ./script/dbt_pat.sh deps
#   ./script/dbt_pat.sh build
uv run dbt deps
uv run dbt build

# RAI
uv run rai init

# Run tests
uv run pytest

# Run apps
uv run -m kg.apps.observation_eda observations_per_genus --threshold 100
uv run -m kg.apps.observation_eda nearby_observations

# Nearby traits (lat/lon)
#
# This app takes a latitude/longitude (decimal degrees) and returns a table of
# USDA traits inferred to be "nearby" by looking at GBIF observations in an H3
# neighborhood, mapping:
#   Observation -> Taxon (canonical name) -> USDA Plants -> Plant Traits
#
# Lat/lon format:
# - Decimal degrees as floats.
# - North/East are positive; South/West are negative.
# - Latitude must be in [-90, 90], longitude in [-180, 180].
#
# Auth:
# Uses Snowflake CLI (snow) under the hood. Recommended PAT setup:
#   export SNOWFLAKE_PAT_FILE="$HOME/.config/snowflake/pat.token"
#
# Example runs:
uv run -m kg.apps.nearby_traits --lat 37.6125 --lon -77.5652777778 --limit 20
uv run -m kg.apps.nearby_traits --lat 41.2369444444 --lon -73.5680555556 --limit 20
```

## AI Assistance
Some useful prompts which Claude Code has been pretty good with:
- "add the core model definition for the concept MyCoolConcept which is sourced from dbt/models/staging/boop.yml, following the example in kg/model/core/observation.py"
- "add a test for the bindings of MyCoolConcept to kg/tests/test_bindings.py"
- "update the protocols in kg/model/__init__.py to reflect the dynamic assignments to the RAI model"
- "update the comments in kg/model/core/taxon.py to reflect the documentation in the dbt/models/staging/taxon.yml"

You can try asking it to generate queries, but it seems pretty hit or miss. maybe it will be better with more queries to serve as examples.





