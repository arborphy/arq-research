import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/debug", tags=["debug"])

DEBUG_FILES = [
    Path(__file__).resolve().parents[3] / "debug.jsonl",
    Path(__file__).resolve().parents[2] / "debug.jsonl",
    Path.cwd() / "debug.jsonl",
]


def _find_debug_file():
    """Return the most recently modified debug.jsonl."""
    candidates = [p for p in DEBUG_FILES if p.exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


@router.get("/queries")
def recent_queries(limit: int = 20):
    path = _find_debug_file()
    if not path:
        return {"data": []}

    queries = []
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            if d.get("event") == "span_start":
                span = d.get("span", {})
                if span.get("type") == "query":
                    attrs = span.get("attrs", {})
                    queries.append({
                        "id": span.get("id"),
                        "timestamp": span.get("start_timestamp"),
                        "source": attrs.get("source", ""),
                        "dsl": attrs.get("dsl", ""),
                        "file": attrs.get("file", ""),
                        "line": attrs.get("line"),
                    })

    return {"data": queries[-limit:]}
