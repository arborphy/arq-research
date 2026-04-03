#!/usr/bin/env bash
# Bulk-load stg_trail_cells.csv into Snowflake using snowsql PUT + COPY INTO.
set -euo pipefail

CSV="$(cd "$(dirname "$0")/.." && pwd)/dbt/seeds/stg_trail_cells.csv"
DB="chaker_temp"
SCHEMA="public_arborphy"
TABLE="stg_trail_cells"

echo "Loading $CSV → $DB.$SCHEMA.$TABLE"

SNOWSQL_PWD="$(python3 -c "import yaml; p=yaml.safe_load(open('$HOME/.dbt/profiles.yml')); print(p['default']['outputs']['dev']['password'])")"
export SNOWSQL_PWD

/Applications/SnowSQL.app/Contents/MacOS/snowsql \
  --accountname mlb08006 \
  --username CHAKER_BENHAMAD \
  --rolename ACCOUNTADMIN \
  --warehouse RAI_WAREHOUSE \
  --dbname "$DB" \
  --schemaname "$SCHEMA" \
  --query "
    CREATE OR REPLACE TABLE $DB.$SCHEMA.$TABLE (
      osm_id    VARCHAR,
      name      VARCHAR,
      highway   VARCHAR,
      surface   VARCHAR,
      h3_res13  NUMBER(38, 0)
    );

    PUT 'file://$CSV' @%$TABLE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;

    COPY INTO $DB.$SCHEMA.$TABLE
    FROM @%$TABLE
    FILE_FORMAT = (
      TYPE = CSV
      SKIP_HEADER = 1
      FIELD_OPTIONALLY_ENCLOSED_BY = '\"'
    );

    ALTER TABLE $DB.$SCHEMA.$TABLE SET CHANGE_TRACKING = TRUE;

    SELECT COUNT(*) AS loaded_rows FROM $DB.$SCHEMA.$TABLE;
  "
