import os
from pathlib import Path

import pytest
import relationalai.semantics as sem
import relationalai as rai

from kg.model import define_arq, ARQModel


def _maybe_set_snowflake_password_from_pat_file() -> None:
    # `relationalai`'s config loader falls back to `os.environ.get("password")`.
    # For local/dev, allow sourcing a Snowflake Programmatic Access Token (PAT)
    # from a file without committing secrets to the repo.
    existing = os.environ.get("password")
    if existing is not None and existing.strip() != "":
        return

    token_path = os.environ.get(
        "SNOWFLAKE_PAT_FILE",
        str(Path.home() / ".config" / "snowflake" / "pat.token"),
    )
    p = Path(token_path).expanduser()
    if not p.exists():
        return

    token = p.read_text(encoding="utf-8").strip()
    if token:
        os.environ["password"] = token


_maybe_set_snowflake_password_from_pat_file()


@pytest.fixture(scope="session")
def arq() -> ARQModel:
    return define_arq(sem.Model(f"arq_test"))
