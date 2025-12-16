"""Taxonomy Graph Demo Queries

Run graph/ancestor-based taxonomy queries against the ARQ model.

Usage:
  uv run -m kg.apps.taxonomy_graph_demo <query_name> [--param value ...]

Examples:
  uv run -m kg.apps.taxonomy_graph_demo lineage_for_species --species-id 1000005
  uv run -m kg.apps.taxonomy_graph_demo species_in_order --order-id 564

Notes:
- This script uses `taxonomy_mode="ancestor"` so `Taxon.ancestor` is available.
- Queries return a `rai.Fragment` and are executed via `.to_df()`.
"""

import argparse
import inspect
import sys
from typing import Callable, Dict

import relationalai.semantics as rai

from kg.model import ARQModel, define_arq


def lineage_for_species(arq: ARQModel, species_id: int = 1000005) -> rai.Fragment:
    """Return all ancestors for a given species (any rank)."""
    s = arq.Species.ref()
    a = arq.Taxon.ref()

    return (
        rai.where(
            s.id == species_id,
            s.ancestor(a),
        )
        .select(
            s.id.alias("species_id"),
            s.canonical_name.alias("species_name"),
            a.id.alias("ancestor_id"),
            a.rank.alias("ancestor_rank"),
            a.canonical_name.alias("ancestor_name"),
        )
    )


def species_in_order(arq: ARQModel, order_id: int = 564) -> rai.Fragment:
    """All species that have the given Order as an ancestor."""
    sp = arq.Species.ref()
    o = arq.Order.ref()

    return (
        rai.where(
            o.id == order_id,
            sp.ancestor(o),
        )
        .select(
            sp.id,
            sp.canonical_name,
            o.id.alias("order_id"),
            o.canonical_name.alias("order_name"),
        )
    )


def detect_skipped_genus(arq: ARQModel, limit: int = 50) -> rai.Fragment:
    """Species whose immediate parent isn't a genus but they still have a genus ancestor."""
    sp = arq.Species.ref()
    g = arq.Genus.ref()

    q = (
        rai.where(
            sp.parent.rank != "genus",
            sp.genus(g),
        )
        .select(
            sp.id,
            sp.canonical_name,
            sp.parent.id.alias("parent_id"),
            sp.parent.rank.alias("parent_rank"),
            g.id.alias("genus_id"),
            g.canonical_name.alias("genus_name"),
        )
    )

    # Keep results manageable when exploring.
    if limit is not None and limit > 0:
        q = q.limit(limit)

    return q


def ambiguous_family_ancestors(arq: ARQModel, min_families: int = 2, limit: int = 50) -> rai.Fragment:
    """Species with multiple family ancestors (potential ambiguity / data issues)."""
    sp = arq.Species.ref()
    fam = arq.Family.ref()

    family_count = rai.count(fam).where(sp.family(fam)).per(sp)

    q = (
        rai.where(family_count >= min_families)
        .select(
            sp.id,
            sp.canonical_name,
            family_count.alias("family_ancestor_count"),
        )
    )

    if limit is not None and limit > 0:
        q = q.limit(limit)

    return q


def common_genus(arq: ARQModel, species1_id: int = 1000005, species2_id: int = 1000006) -> rai.Fragment:
    """Find common genus ancestor(s) of two species."""
    s1 = arq.Species.ref()
    s2 = arq.Species.ref()
    g = arq.Genus.ref()

    return (
        rai.where(
            s1.id == species1_id,
            s2.id == species2_id,
            s1.genus(g),
            s2.genus(g),
        )
        .select(
            g.id,
            g.canonical_name,
        )
    )


def _get_query_functions() -> Dict[str, Callable]:
    current_module = sys.modules[__name__]
    out: Dict[str, Callable] = {}

    for name, obj in inspect.getmembers(current_module, inspect.isfunction):
        if name.startswith("_"):
            continue

        sig = inspect.signature(obj)
        params = list(sig.parameters.values())

        if (
            params
            and params[0].annotation == ARQModel
            and sig.return_annotation == rai.Fragment
        ):
            out[name] = obj

    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run taxonomy graph demo queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    query_functions = _get_query_functions()
    if not query_functions:
        print("Error: No query functions found", file=sys.stderr)
        raise SystemExit(1)

    parser.add_argument(
        "query_name",
        choices=sorted(query_functions.keys()),
        help=f"Query to run. Available: {', '.join(sorted(query_functions.keys()))}",
    )

    parser.add_argument(
        "--model-name",
        default="taxonomy_graph_demo",
        help="RAI model name (default: taxonomy_graph_demo)",
    )

    # Parse known args first so we can add query-specific params.
    args, remaining = parser.parse_known_args()
    query_func = query_functions[args.query_name]

    sig = inspect.signature(query_func)
    query_params = list(sig.parameters.values())[1:]  # skip ARQModel

    for param in query_params:
        arg_name = f"--{param.name.replace('_', '-')}"
        param_type = param.annotation if param.annotation != inspect.Parameter.empty else str

        kwargs = {}
        if param.default != inspect.Parameter.empty:
            kwargs["default"] = param.default

        parser.add_argument(
            arg_name,
            type=param_type,
            **kwargs,
        )

    # Parse final args (including query-specific ones).
    args = parser.parse_args()

    print(f"Initializing model: {args.model_name} (taxonomy_mode=ancestor)")
    arq = define_arq(rai.Model(args.model_name), taxonomy_mode="ancestor")

    # Build kwargs for query function
    kwargs = {}
    for param in query_params:
        kwargs[param.name] = getattr(args, param.name)

    print(f"Running query: {args.query_name}({', '.join(f'{k}={v}' for k, v in kwargs.items())})")
    df = query_func(arq, **kwargs).to_df()
    print(df)


if __name__ == "__main__":
    main()
