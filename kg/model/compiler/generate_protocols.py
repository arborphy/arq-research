"""Generate Protocol stubs from declarative EntitySpec classes.

Run:
  uv run -m kg.model.compiler.generate_protocols

This writes:
  kg/model/_generated_protocols.py

Only spec-driven entities are generated (currently Observation).
"""

from __future__ import annotations

from pathlib import Path

from kg.model.compiler.protocol_gen import generate_protocol_module
from kg.model.specs import ENTITY_SPECS


OUT_PATH = Path(__file__).resolve().parents[1] / "_generated_protocols.py"


def main() -> int:
    content = generate_protocol_module(specs=ENTITY_SPECS)
    OUT_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
