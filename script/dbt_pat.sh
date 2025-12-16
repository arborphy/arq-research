#!/usr/bin/env bash
set -euo pipefail

# Run dbt using the repo-local profiles.yml and a Snowflake PAT as the password.
#
# Usage:
#   ./script/dbt_pat.sh build --select plants
#
# Prereqs:
#   export SNOWFLAKE_PAT_FILE="$HOME/.config/snowflake/pat.token"
#   (or export password directly)

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# By default, prefer the PAT token file if present.
# This avoids accidental reuse of a stale `password` env var from earlier commands.
if [[ "${DBT_PAT_NO_OVERRIDE:-0}" != "1" ]]; then
  if [[ -n "${SNOWFLAKE_PAT_FILE:-}" && -f "${SNOWFLAKE_PAT_FILE}" ]]; then
    export password="$(cat "${SNOWFLAKE_PAT_FILE}")"
  fi
fi

if [[ -z "${password:-}" ]]; then
  echo "error: PAT not set. Export either:" >&2
  echo "  SNOWFLAKE_PAT_FILE=... (recommended)" >&2
  echo "  password=..." >&2
  exit 1
fi

cd "$repo_root"
export DBT_PROFILES_DIR="$repo_root"

exec uv run dbt "$@"
