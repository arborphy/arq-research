"""
Observation Exploratory Data Analysis

This module provides queries for analyzing plant observation data from GBIF,
including taxonomic distributions, temporal patterns, and spatial analysis.
"""

import argparse
import inspect
import sys
from typing import Callable, Dict

import relationalai.semantics as rai

from kg.model import define_arq, ARQModel


def observations_per_genus(arq: ARQModel, threshold: int = 10) -> rai.Fragment:
    """Count the number of observations classified as each taxonomic genus,
    above the given threshold.

    Returns:
        A query fragment with columns:
        - observation_count: Number of observations for that genus
        - genus_name: The canonical name of the genus
        - genus_id: The taxonomic ID of the genus
    """

    return rai.where(
        arq.Observation.classification(arq.Taxon),
        arq.Taxon.genus(arq.Genus),
        obs_count := rai.count(arq.Observation).per(arq.Genus),
        obs_count > threshold
    ).select(
        obs_count.alias("observation_count"),
        rai.sum(obs_count),
        arq.Genus.canonical_name.alias("genus_name"),
        arq.Genus.id.alias("genus_id"),
    )


def nearby_observations(arq: ARQModel) -> rai.Fragment:
    """Count pairs of observations that co-occur in space and time.

    Finds pairs of observations that occurred:
    - In the same H3 cell (resolution 6, ~36km² area)
    - on the same day
    - Are different observations (not the same observation paired with itself)

    Returns:
        A query fragment with columns:
        - cooccurrence_count: Number of observation pairs meeting the criteria
    """
    obs1 = arq.Observation.ref()
    obs2 = arq.Observation.ref()

    return rai.where(
        obs1 < obs2,
        obs1.year == obs2.year,
        obs1.h3_cell_6 == obs2.h3_cell_6,
        obs1.day_of_year == obs2.day_of_year,
    ).select(
        rai.count(obs1, obs2).alias("cooccurrence_count"),
    )

## ↓ brought to you by Claude

def _get_query_functions() -> Dict[str, Callable]:
    """Get all query functions defined in this module.

    Returns a dictionary mapping function names to function objects.
    Only includes functions that take ARQModel as first parameter and
    return rai.Fragment.
    """
    current_module = sys.modules[__name__]
    query_functions = {}

    for name, obj in inspect.getmembers(current_module, inspect.isfunction):
        if name.startswith('_'):
            continue

        sig = inspect.signature(obj)
        params = list(sig.parameters.values())

        # Check if first parameter is ARQModel and return type is rai.Fragment
        if (params and
            params[0].annotation == ARQModel and
            sig.return_annotation == rai.Fragment):
            query_functions[name] = obj

    return query_functions


def main():
    """Main entry point for running queries from the command line.

    Usage:
        python -m kg.apps.observation_eda <query_name> [--param value ...]

    Example:
        python -m kg.apps.observation_eda observations_per_family
    """
    parser = argparse.ArgumentParser(
        description="Run observation EDA queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Get available query functions
    query_functions = _get_query_functions()

    if not query_functions:
        print("Error: No query functions found in this module", file=sys.stderr)
        sys.exit(1)

    parser.add_argument(
        'query_name',
        choices=list(query_functions.keys()),
        help=f"Name of the query to run. Available queries: {', '.join(query_functions.keys())}"
    )

    parser.add_argument(
        '--model-name',
        default='arq_eda',
        help='Name for the RAI model (default: arq_eda)'
    )

    # Parse known args first to get the query name
    args, remaining = parser.parse_known_args()

    # Get the selected query function
    query_func = query_functions[args.query_name]

    # Get the function signature to add appropriate parameters
    sig = inspect.signature(query_func)
    params = list(sig.parameters.values())[1:]  # Skip the first parameter (arq)

    # Add arguments for function parameters
    for param in params:
        param_name = f'--{param.name.replace("_", "-")}'
        param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
        param_default = param.default if param.default != inspect.Parameter.empty else None

        parser.add_argument(
            param_name,
            type=param_type,
            default=param_default,
            help=f"Parameter {param.name} (type: {param_type.__name__})"
        )

    # Parse all arguments
    args = parser.parse_args()

    # Instantiate the model
    print(f"Initializing model: {args.model_name}")
    arq = define_arq(rai.Model(args.model_name))

    # Build kwargs for the query function
    kwargs = {}
    for param in params:
        value = getattr(args, param.name)
        if value is not None:
            kwargs[param.name] = value

    # Run the query
    print(f"Running query: {args.query_name}")
    if kwargs:
        print(f"Parameters: {kwargs}")

    result = query_func(arq, **kwargs)

    # Execute and display results
    df = result.to_df()
    print(f"\nResults ({len(df)} rows):")
    print(df)


if __name__ == '__main__':
    main()
