"""Graph traversal playground for the ARQ semantic model.

This CLI is meant to make the "graph navigation" aspect of the RAI semantics
model concrete: you provide an anchor node (e.g. a Taxon canonical name), and
then choose a traversal/query (parent, siblings, traits, etc).

Examples:
  uv run -m kg.apps.graph_explore --canonical-name "Juglans nigra" --query traits
  uv run -m kg.apps.graph_explore --canonical-name "Juglans nigra" --query parent
  uv run -m kg.apps.graph_explore --taxon-id 8103240 --query usda-plant

Auth:
  This uses the same config mechanism as tests. If you use Snowflake PAT-based
  auth, set $SNOWFLAKE_PAT_FILE or pass --pat-file.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path
from typing import Sequence

import relationalai.semantics as rai
import relationalai.semantics as sem

from kg.model import define_arq


def _maybe_set_password_from_pat_file(pat_file: str | None) -> None:
    # `relationalai` config loader falls back to `os.environ.get("password")`.
    existing = os.environ.get("password")
    if existing is not None and existing.strip() != "":
        return

    token_path = pat_file or os.environ.get(
        "SNOWFLAKE_PAT_FILE",
        str(Path.home() / ".config" / "snowflake" / "pat.token"),
    )
    p = Path(token_path).expanduser()
    if not p.exists():
        return

    token = p.read_text(encoding="utf-8").strip()
    if token:
        os.environ["password"] = token


def _print_df(df) -> None:
    # Keep printing dependency-free: pandas is already in the dep tree via relationalai.
    if df is None:
        print("(no result)")
        return
    if getattr(df, "empty", False):
        print("(no rows)")
        return
    print(df)


def _anchor_taxon_constraints(*, arq, taxon, canonical_name: str | None, taxon_id: int | None):
    if canonical_name is not None:
        return [taxon.canonical_name == canonical_name]
    if taxon_id is not None:
        return [taxon.id == taxon_id]
    raise ValueError("Must provide --canonical-name or --taxon-id")


def query_parent(*, arq, canonical_name: str | None, taxon_id: int | None):
    child = arq.Taxon.ref()
    parent = arq.Taxon.ref()

    where = [
        *(_anchor_taxon_constraints(arq=arq, taxon=child, canonical_name=canonical_name, taxon_id=taxon_id)),
        child.parent(parent),
    ]

    return rai.where(*where).select(
        child.id,
        child.canonical_name,
        child.rank,
        parent.id,
        parent.canonical_name,
        parent.rank,
    ).to_df()


def query_siblings_by_parent(*, arq, canonical_name: str | None, taxon_id: int | None):
    anchor = arq.Taxon.ref()
    sibling = arq.Taxon.ref()
    parent = arq.Taxon.ref()

    where = [
        *(_anchor_taxon_constraints(arq=arq, taxon=anchor, canonical_name=canonical_name, taxon_id=taxon_id)),
        anchor.parent(parent),
        sibling.parent(parent),
        anchor != sibling,
    ]

    return rai.where(*where).select(
        parent.canonical_name,
        anchor.canonical_name,
        sibling.canonical_name,
        sibling.rank,
    ).to_df()


def query_siblings_by_genus(*, arq, canonical_name: str | None, taxon_id: int | None):
    # This query is most meaningful when the anchor is a Species.
    anchor = arq.Species.ref()
    sibling = arq.Species.ref()
    genus = arq.Genus.ref()

    where = [
        *(_anchor_taxon_constraints(arq=arq, taxon=anchor, canonical_name=canonical_name, taxon_id=taxon_id)),
        anchor.genus(genus),
        sibling.genus(genus),
        anchor != sibling,
    ]

    return rai.where(*where).select(
        genus.canonical_name,
        anchor.canonical_name,
        sibling.canonical_name,
        sibling.id,
    ).to_df()


def query_usda_plant(*, arq, canonical_name: str | None, taxon_id: int | None):
    taxon = arq.Taxon.ref()
    plant = arq.Plant.ref()

    where = [
        *(_anchor_taxon_constraints(arq=arq, taxon=taxon, canonical_name=canonical_name, taxon_id=taxon_id)),
        taxon.usda_plant(plant),
    ]

    return rai.where(*where).select(
        taxon.id,
        taxon.canonical_name,
        plant.id,
        plant.scientific_name,
        plant.reference,
    ).to_df()


def query_traits(*, arq, canonical_name: str | None, taxon_id: int | None):
    taxon = arq.Taxon.ref()
    plant = arq.Plant.ref()
    trait = arq.Trait.ref()

    where = [
        *(_anchor_taxon_constraints(arq=arq, taxon=taxon, canonical_name=canonical_name, taxon_id=taxon_id)),
        taxon.usda_plant(plant),
        plant.trait(trait),
    ]

    return rai.where(*where).select(
        taxon.canonical_name,
        plant.scientific_name,
        trait.name,
        trait.value,
    ).to_df()


def query_ref_demo(*, arq, canonical_name: str | None, taxon_id: int | None):
    # A small experiment to make ref() meaning concrete:
    # - We create two variables (child, parent)
    # - We show results *with* the edge constraint child.parent(parent)
    child = arq.Taxon.ref()
    parent = arq.Taxon.ref()

    where = [
        *(_anchor_taxon_constraints(arq=arq, taxon=child, canonical_name=canonical_name, taxon_id=taxon_id)),
        child.parent(parent),
    ]

    return rai.where(*where).select(
        child.canonical_name,
        child.rank,
        parent.canonical_name,
        parent.rank,
    ).to_df()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Explore the ARQ semantic graph with small traversal queries.")

    anchor = parser.add_mutually_exclusive_group(required=True)
    anchor.add_argument("--canonical-name", help="Anchor taxon canonical name (e.g. 'Juglans nigra')")
    anchor.add_argument("--taxon-id", type=int, help="Anchor taxon id (GBIF taxon id)")

    parser.add_argument(
        "--query",
        required=True,
        choices=[
            "parent",
            "siblings-parent",
            "siblings-genus",
            "usda-plant",
            "traits",
            "ref-demo",
        ],
        help="Which traversal to run",
    )

    parser.add_argument("--database", default="TEAM_ARQ", help="Snowflake database name for source bindings")
    parser.add_argument("--schema", default="PUBLIC", help="Snowflake schema name for source bindings")
    parser.add_argument(
        "--pat-file",
        default=None,
        help="Path to Snowflake PAT token file (default: $SNOWFLAKE_PAT_FILE or ~/.config/snowflake/pat.token)",
    )

    args = parser.parse_args(argv)

    _maybe_set_password_from_pat_file(args.pat_file)

    m = sem.Model("arq_graph_explore")
    arq = define_arq(m, db=args.database, schema=args.schema)

    try:
        if args.query == "parent":
            df = query_parent(arq=arq, canonical_name=args.canonical_name, taxon_id=args.taxon_id)
        elif args.query == "siblings-parent":
            df = query_siblings_by_parent(arq=arq, canonical_name=args.canonical_name, taxon_id=args.taxon_id)
        elif args.query == "siblings-genus":
            df = query_siblings_by_genus(arq=arq, canonical_name=args.canonical_name, taxon_id=args.taxon_id)
        elif args.query == "usda-plant":
            df = query_usda_plant(arq=arq, canonical_name=args.canonical_name, taxon_id=args.taxon_id)
        elif args.query == "traits":
            df = query_traits(arq=arq, canonical_name=args.canonical_name, taxon_id=args.taxon_id)
        elif args.query == "ref-demo":
            df = query_ref_demo(arq=arq, canonical_name=args.canonical_name, taxon_id=args.taxon_id)
        else:
            raise ValueError(f"Unknown query: {args.query}")

        _print_df(df)
        return 0
    except Exception as e:
        # The semantics layer often raises a wrapper exception (e.g. "Multiple Errors")
        # and prints details elsewhere. Make sure we surface everything here.
        print(f"Error: {e!r}", file=sys.stderr)
        if hasattr(e, "exceptions"):
            try:
                errs = getattr(e, "exceptions")
                print("\nUnderlying errors:", file=sys.stderr)
                for idx, err in enumerate(errs, start=1):
                    print(f"[{idx}] {err!r}", file=sys.stderr)
                    if hasattr(err, "pprint"):
                        err.pprint()
            except Exception:
                pass
        elif hasattr(e, "pprint"):
            try:
                print("\nUnderlying errors:", file=sys.stderr)
                e.pprint()
            except Exception:
                pass
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
