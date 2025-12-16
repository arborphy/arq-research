from __future__ import annotations

import argparse
import csv
import os
import sqlite3
from pathlib import Path
from typing import Iterable


def iter_rows(cursor: sqlite3.Cursor, chunk_size: int) -> Iterable[tuple]:
    while True:
        rows = cursor.fetchmany(chunk_size)
        if not rows:
            return
        for row in rows:
            yield row


def export_table(conn: sqlite3.Connection, table: str, out_path: Path, chunk_size: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")

    column_names = [desc[0] for desc in cursor.description]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(column_names)
        for row in iter_rows(cursor, chunk_size=chunk_size):
            writer.writerow(list(row))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export plants-related tables from a SQLite DB to CSV files."
    )
    parser.add_argument(
        "--db",
        default=str(Path(__file__).resolve().parents[1] / "plants.db"),
        help="Path to plants.db (default: ./plants.db)",
    )
    parser.add_argument(
        "--out-dir",
        default=str(Path(__file__).resolve().parents[1] / ".local" / "plants_csv"),
        help="Output directory for CSV files (default: ./.local/plants_csv)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10_000,
        help="Rows per fetch when streaming (default: 10000)",
    )

    args = parser.parse_args()

    db_path = Path(args.db).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    if not db_path.exists():
        raise SystemExit(f"SQLite database not found: {db_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    # Make sure SQLite uses deterministic text decoding.
    os.environ.setdefault("PYTHONUTF8", "1")

    conn = sqlite3.connect(str(db_path))
    try:
        for table in ["plants", "plant_characteristics", "plant_native_statuses"]:
            export_table(conn, table=table, out_path=out_dir / f"{table}.csv", chunk_size=args.chunk_size)
    finally:
        conn.close()

    print(f"Exported CSVs to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
