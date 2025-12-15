#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Sets up Snowflake Programmatic Access Token (PAT) usage for this repo without committing secrets.

This script can:
  - (optional) apply Snowflake network policy prerequisites (requires ACCOUNTADMIN via a Snowflake CLI connection)
  - store the PAT secret locally in ~/.config/snowflake/pat.token
  - generate raiconfig.toml from raiconfig.example.toml (with no password embedded)

Required args:
  --user <SNOWFLAKE_USER>
  --account <ACCOUNT_IDENTIFIER>       e.g. WOTEIWV-MAC88464
  --role <ROLE>                        e.g. RAI_DEVELOPER
  --warehouse <WAREHOUSE>              e.g. TEAM_ARQ

Optional args:
  --admin-connection <name>            snowflake-cli connection name with ACCOUNTADMIN
  --allowed-ip <CIDR>                  only used with --admin-connection (default: auto-detect public IP and use /32)
  --network-policy <name>              default: ARQ_PAT_POLICY
  --no-write-raiconfig                 skip generating ./raiconfig.toml
  --snow-connection <name>             print env var export for this snowflake-cli connection
  --verify-connection <name>           run `snow sql -c <name> -q "select current_user()"` using PAT
  -h, --help

Environment variables:
  SNOWFLAKE_PAT_FILE                   token file path (default: ~/.config/snowflake/pat.token)
  SNOWFLAKE_PAT_SECRET                 if set, uses this token secret instead of prompting

Notes:
  - You still must generate the PAT in Snowsight; Snowflake does not expose the token secret again.
  - For PERSON users, Snowflake requires a network policy on the user to *use* a PAT.
EOF
}

fail() {
  echo "error: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

python_cmd() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return
  fi
  fail "Missing required command: python3 (or python)"
}

detect_public_ip() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsS https://api.ipify.org || true
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://api.ipify.org || true
  else
    return 1
  fi
}

to_sf_identifier() {
  # Best-effort conversion to a safe Snowflake identifier (unquoted).
  # Caller can still pass a valid identifier explicitly.
  echo "$1" | tr '[:lower:]-' '[:upper:]_' | tr -cd 'A-Z0-9_'
}

to_snowcli_env_key() {
  # Snowflake CLI env var keys are like SNOWFLAKE_CONNECTIONS_<NAME>_PASSWORD
  # where <NAME> is uppercased and '-' becomes '_'.
  local name="$1"
  name="${name^^}"
  name="${name//-/_}"
  echo "$name"
}

SNOWFLAKE_USER=""
SNOWFLAKE_ACCOUNT=""
SNOWFLAKE_ROLE=""
SNOWFLAKE_WAREHOUSE=""
ADMIN_CONNECTION=""
SNOW_CONNECTION=""
VERIFY_CONNECTION=""
ALLOWED_IP=""
NETWORK_POLICY_NAME="ARQ_PAT_POLICY"
WRITE_RAICONFIG=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user)
      SNOWFLAKE_USER="${2:-}"; shift 2 ;;
    --account)
      SNOWFLAKE_ACCOUNT="${2:-}"; shift 2 ;;
    --role)
      SNOWFLAKE_ROLE="${2:-}"; shift 2 ;;
    --warehouse)
      SNOWFLAKE_WAREHOUSE="${2:-}"; shift 2 ;;
    --admin-connection)
      ADMIN_CONNECTION="${2:-}"; shift 2 ;;
    --snow-connection)
      SNOW_CONNECTION="${2:-}"; shift 2 ;;
    --verify-connection)
      VERIFY_CONNECTION="${2:-}"; shift 2 ;;
    --allowed-ip)
      ALLOWED_IP="${2:-}"; shift 2 ;;
    --network-policy)
      NETWORK_POLICY_NAME="${2:-}"; shift 2 ;;
    --no-write-raiconfig)
      WRITE_RAICONFIG=0; shift 1 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      fail "Unknown argument: $1 (use --help)" ;;
  esac
done

[[ -n "$SNOWFLAKE_USER" ]] || fail "--user is required"
[[ -n "$SNOWFLAKE_ACCOUNT" ]] || fail "--account is required"
[[ -n "$SNOWFLAKE_ROLE" ]] || fail "--role is required"
[[ -n "$SNOWFLAKE_WAREHOUSE" ]] || fail "--warehouse is required"

TOKEN_FILE="${SNOWFLAKE_PAT_FILE:-$HOME/.config/snowflake/pat.token}"

# Optional: apply Snowflake-side prerequisites.
if [[ -n "$ADMIN_CONNECTION" ]]; then
  require_cmd uvx

  if [[ -z "$ALLOWED_IP" ]]; then
    ip="$(detect_public_ip || true)"
    [[ -n "$ip" ]] || fail "Could not auto-detect public IP. Re-run with --allowed-ip <CIDR>"
    ALLOWED_IP="$ip/32"
  fi

  sf_policy="$(to_sf_identifier "$NETWORK_POLICY_NAME")"
  [[ -n "$sf_policy" ]] || fail "Invalid --network-policy name: $NETWORK_POLICY_NAME"

  echo "Applying network policy via snowflake-cli connection '$ADMIN_CONNECTION'..."
  uvx --from snowflake-cli snow sql -c "$ADMIN_CONNECTION" -q "CREATE OR REPLACE NETWORK POLICY ${sf_policy} ALLOWED_IP_LIST = ('${ALLOWED_IP}') COMMENT = 'Allow PAT usage from approved egress IPs (arq-starter)';"
  uvx --from snowflake-cli snow sql -c "$ADMIN_CONNECTION" -q "ALTER USER \"${SNOWFLAKE_USER}\" SET NETWORK_POLICY = ${sf_policy};"
  echo "Network policy '${sf_policy}' applied to user '${SNOWFLAKE_USER}'."
else
  echo "Skipping Snowflake policy changes (no --admin-connection provided)."
  echo "If PAT auth fails with network policy errors, re-run with --admin-connection."
fi

# Prompt for PAT secret (or use env var).
pat_secret="${SNOWFLAKE_PAT_SECRET:-}"
if [[ -z "$pat_secret" ]]; then
  echo
  echo "Paste the PAT token secret (input hidden), then press Enter:"
  read -r -s pat_secret
  echo
fi
[[ -n "$pat_secret" ]] || fail "PAT token secret is empty"

mkdir -p "$(dirname "$TOKEN_FILE")"
( umask 077 && printf '%s' "$pat_secret" > "$TOKEN_FILE" )
chmod 600 "$TOKEN_FILE" 2>/dev/null || true

echo "Wrote PAT token to $TOKEN_FILE (mode 600)."

# Generate raiconfig.toml for this repo (no secrets embedded).
if [[ "$WRITE_RAICONFIG" -eq 1 ]]; then
  [[ -f "raiconfig.example.toml" ]] || fail "Missing raiconfig.example.toml in repo root"

  export SNOWFLAKE_USER SNOWFLAKE_ACCOUNT SNOWFLAKE_ROLE SNOWFLAKE_WAREHOUSE

  "$(python_cmd)" - <<PY
from pathlib import Path
import os

user = os.environ["SNOWFLAKE_USER"]
account = os.environ["SNOWFLAKE_ACCOUNT"]
role = os.environ["SNOWFLAKE_ROLE"]
warehouse = os.environ["SNOWFLAKE_WAREHOUSE"]

src = Path("raiconfig.example.toml").read_text(encoding="utf-8")
text = (src
    .replace("YOUR_USER", user)
    .replace("YOUR_ORG-YOUR_ACCOUNT", account)
    .replace("YOUR_ROLE", role)
    .replace("YOUR_WAREHOUSE", warehouse)
)

Path("raiconfig.toml").write_text(text, encoding="utf-8")
PY

  echo "Generated ./raiconfig.toml (gitignored)."
fi

# Print recommended exports for the current shell.
echo
echo "Next steps:"
echo "  1) For this repo/RelationalAI client, set:"
echo "       export SNOWFLAKE_PAT_FILE=\"$TOKEN_FILE\""
echo "       export password=\"\$(cat \"$TOKEN_FILE\")\""

snow_conn_name=""
if [[ -n "$VERIFY_CONNECTION" ]]; then
  snow_conn_name="$VERIFY_CONNECTION"
elif [[ -n "$SNOW_CONNECTION" ]]; then
  snow_conn_name="$SNOW_CONNECTION"
fi

if [[ -n "$snow_conn_name" ]]; then
  conn_key="$(to_snowcli_env_key "$snow_conn_name")"
  echo
  echo "  2) For snowflake-cli connection '$snow_conn_name', set:"
  echo "       export SNOWFLAKE_CONNECTIONS_${conn_key}_PASSWORD=\"\$(cat \"$TOKEN_FILE\")\""
fi

if [[ -n "$VERIFY_CONNECTION" ]]; then
  require_cmd uvx
  conn_key="$(to_snowcli_env_key "$VERIFY_CONNECTION")"
  echo
  echo "Verifying PAT works with snowflake-cli..."
  export password="$pat_secret"
  export "SNOWFLAKE_CONNECTIONS_${conn_key}_PASSWORD=$pat_secret"
  uvx --from snowflake-cli snow sql -c "$VERIFY_CONNECTION" -q "select current_user()"

  unset password
  unset "SNOWFLAKE_CONNECTIONS_${conn_key}_PASSWORD" || true
fi

exit 0
