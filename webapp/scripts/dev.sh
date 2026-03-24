#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PYTHONPATH="$ROOT"

echo "Starting backend on :8000 and frontend on :5173..."

uvicorn webapp.backend.main:app --reload --port 8000 &
BACKEND_PID=$!

cd "$ROOT/webapp/frontend"
npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
