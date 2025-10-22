# ARQ Starter

Contains 
- [DBT models](/dbt/models) for preprocessing and documenting source data 
  - https://github.com/dbt-labs/dbt-core
  - 
- [RAI model](/kg/model) for building semantics
- []

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

# DBT
# create a config file https://docs.getdbt.com/docs/core/connect-data-platform/snowflake-setup
# dbt_project.yaml assumes a profile named "default" which targets the schema "team_arq.public"
uv run dbt deps
uv run dbt build

# RAI
uv run rai init

# Run tests
uv run pytest

# Run apps
uv run -m kg.apps.observation_eda observations_per_genus --threshold 100
uv run -m  kg.apps.observation_eda nearby_observations
```





