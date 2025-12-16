#!/usr/bin/env bash
set -euo pipefail

# Downloads plant CSVs from static URLs (e.g., Google Drive direct download links)
# and loads them into Snowflake using script/plants.sql.
#
# Prereqs:
# - `uvx` available (uv installed)
# - snowflake-cli configured (see README)
#
# Configure URLs (either export these env vars, or edit them inline).
: "${PLANTS_CSV_URL:=}"
: "${PLANT_CHARACTERISTICS_CSV_URL:=}"
: "${PLANT_NATIVE_STATUSES_CSV_URL:=}"

# Default: repo-pinned Google Drive files (can override via env vars above).
: "${PLANTS_GDRIVE_FILE_ID:=1zVhjRDEgGsDKEVjDDSSvkV2UpvztuufJ}"
: "${PLANT_CHARACTERISTICS_GDRIVE_FILE_ID:=1Fj3z1cEkA6Y0Ap7VcNWccIXElkV6S-u4}"
: "${PLANT_NATIVE_STATUSES_GDRIVE_FILE_ID:=1TzAAfKF8TIV5pIUuwF_Qob0JpoPbNufz}"

# Snowflake CLI connection name (defaults to the repo's PAT connection).
: "${SNOW_CONNECTION:=arbq_pat}"

# Optional: PAT token file. If present, we will populate the Snowflake CLI password env var
# for the selected connection to ensure non-interactive execution.
: "${SNOWFLAKE_PAT_FILE:=$HOME/.config/snowflake/pat.token}"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "error: missing required command: $1" >&2; exit 1; }
}

require_cmd curl
require_cmd uvx

to_snowcli_env_key() {
  local name="$1"
  name="${name^^}"
  name="${name//-/_}"
  echo "$name"
}

ensure_snowcli_password() {
  local conn_name="$1"
  local conn_key password_env
  conn_key="$(to_snowcli_env_key "$conn_name")"
  password_env="SNOWFLAKE_CONNECTIONS_${conn_key}_PASSWORD"

  # Only set if not already provided.
  if [[ -z "${!password_env:-}" ]]; then
    if [[ -f "$SNOWFLAKE_PAT_FILE" ]]; then
      export "$password_env=$(cat "$SNOWFLAKE_PAT_FILE")"
    fi
  fi

  if [[ -z "${!password_env:-}" ]]; then
    echo "error: Snowflake CLI password env var is empty: ${password_env}" >&2
    echo "Set it from your PAT token file, e.g.:" >&2
    echo "  export ${password_env}=\"\$(cat \"$SNOWFLAKE_PAT_FILE\")\"" >&2
    exit 1
  fi
}

download_google_drive() {
  # Download a Google Drive file by ID, handling the occasional "confirm" flow.
  # Writes to the given output path.
  local file_id="$1"
  local out_path="$2"
  local tmp_html
  local tmp_cookies
  local confirm

  tmp_html="$(mktemp)"
  tmp_cookies="$(mktemp)"

  # First request: may return the file directly or an HTML interstitial.
  curl -fsSL -c "$tmp_cookies" "https://drive.google.com/uc?export=download&id=${file_id}" -o "$tmp_html"

  # If we got HTML with a confirm token, do the confirmed download.
  confirm="$(sed -n 's/.*confirm=\([0-9A-Za-z_\-]*\).*/\1/p' "$tmp_html" | head -n 1)"
  if [[ -n "$confirm" ]]; then
    curl -fsSL -b "$tmp_cookies" "https://drive.google.com/uc?export=download&confirm=${confirm}&id=${file_id}" -o "$out_path"
  else
    mv "$tmp_html" "$out_path"
    tmp_html="" # prevent cleanup removing the moved file
  fi

  [[ -n "${tmp_html:-}" ]] && rm -f "$tmp_html" || true
  rm -f "$tmp_cookies" || true
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out_dir="${repo_root}/.local/plants_csv"
mkdir -p "$out_dir"

if [[ -n "$PLANTS_CSV_URL" || -n "$PLANT_CHARACTERISTICS_CSV_URL" || -n "$PLANT_NATIVE_STATUSES_CSV_URL" ]]; then
  # URL mode: all 3 must be provided.
  if [[ -z "$PLANTS_CSV_URL" || -z "$PLANT_CHARACTERISTICS_CSV_URL" || -z "$PLANT_NATIVE_STATUSES_CSV_URL" ]]; then
    echo "error: if using URL mode, all three URL env vars are required:" >&2
    echo "  PLANTS_CSV_URL" >&2
    echo "  PLANT_CHARACTERISTICS_CSV_URL" >&2
    echo "  PLANT_NATIVE_STATUSES_CSV_URL" >&2
    exit 1
  fi

  curl -fsSL "$PLANTS_CSV_URL" -o "$out_dir/plants.csv"
  curl -fsSL "$PLANT_CHARACTERISTICS_CSV_URL" -o "$out_dir/plant_characteristics.csv"
  curl -fsSL "$PLANT_NATIVE_STATUSES_CSV_URL" -o "$out_dir/plant_native_statuses.csv"
else
  # Google Drive mode (default)
  download_google_drive "$PLANTS_GDRIVE_FILE_ID" "$out_dir/plants.csv"
  download_google_drive "$PLANT_CHARACTERISTICS_GDRIVE_FILE_ID" "$out_dir/plant_characteristics.csv"
  download_google_drive "$PLANT_NATIVE_STATUSES_GDRIVE_FILE_ID" "$out_dir/plant_native_statuses.csv"
fi

# Basic sanity check: avoid silently loading HTML error pages.
if head -n 1 "$out_dir/plants.csv" | grep -qi '<!doctype\|<html'; then
  echo "error: plants.csv download looks like HTML, not CSV (check PLANTS_CSV_URL)" >&2
  exit 1
fi

ensure_snowcli_password "$SNOW_CONNECTION"
uvx --from snowflake-cli snow sql -c "$SNOW_CONNECTION" -f "${repo_root}/script/plants.sql" -D "path=${out_dir}"
