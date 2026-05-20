#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PYTHONPATH="$ROOT"

DEBUG=0
for arg in "$@"; do
  [ "$arg" = "--debug" ] && DEBUG=1
done

if [ "$DEBUG" = "1" ]; then
  echo "Starting backend in debug mode (pdb-compatible) on :8000 and frontend on :5173..."
  uv run python -m uvicorn webapp.backend.main:app --port 8000 &
else
  echo "Starting backend on :8000 and frontend on :5173..."
  uv run uvicorn webapp.backend.main:app --reload --port 8000 &
fi
BACKEND_PID=$!

cd "$ROOT/webapp/frontend"
npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
