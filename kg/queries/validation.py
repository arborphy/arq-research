"""Validation queries to verify data was loaded correctly.

Usage:
    from kg.queries.validation import run_all
    run_all()
"""
from relationalai.semantics import select, where, count

# Import loaders so define() calls execute
import kg.loaders.observations  # noqa: F401
import kg.loaders.newcomb  # noqa: F401

from kg.model.core.taxonomy import Species
from kg.model.core.observations import Observation
from kg.model.core.h3cell import H3Cell
from kg.model.core.features import Feature, Category, Measurement
from kg.model.core.keys.key import Description
from kg.model.core.provenance import DataSource


def count_observations():
    """Total number of observations loaded."""
    return select(count(Observation)).to_df()


def count_species():
    """Total number of distinct species."""
    return select(count(Species)).to_df()


def count_h3_cells():
    """H3 cell counts by resolution."""
    return select(
        H3Cell.resolution,
        count(H3Cell).per(H3Cell.resolution),
    ).to_df()


def count_features():
    """Number of features, categories, and measurements."""
    return select(
        count(Feature),
        count(Category),
        count(Measurement),
    ).to_df()


def count_identification_keys():
    """Number of identification keys."""
    return select(count(Description)).to_df()


def count_data_sources():
    """List all data sources."""
    return select(DataSource.name).to_df()


def observations_per_species():
    """Species by observation count."""
    df = where(
        Observation.species(Species),
    ).select(
        count(Observation).per(Species),
        Species.name,
    ).to_df()
    return df.sort_values(df.columns[0], ascending=False).reset_index(drop=True)


def observations_per_quality_grade():
    """Observation counts by quality grade."""
    return select(
        Observation.quality_grade,
        count(Observation).per(Observation.quality_grade),
    ).to_df()


def species_with_both_observations_and_keys():
    """Species that appear in both iNat observations and Newcomb keys."""
    return where(
        Observation.species(Species),
        Description.describes(Species),
    ).select(
        count(Species),
    ).to_df()


def run_all():
    """Run all validation queries and print results."""
    checks = [
        ("Observations", count_observations),
        ("Species", count_species),
        ("H3 Cells by resolution", count_h3_cells),
        ("Features & values", count_features),
        ("Identification keys", count_identification_keys),
        ("Data sources", count_data_sources),
        ("Species by observation count", observations_per_species),
        ("Observations by quality grade", observations_per_quality_grade),
        ("Species in both iNat + Newcomb", species_with_both_observations_and_keys),
    ]
    for label, fn in checks:
        print(f"\n--- {label} ---")
        print(fn())


if __name__ == "__main__":
    run_all()
