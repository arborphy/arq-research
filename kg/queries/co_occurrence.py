"""Co-occurrence queries.

Usage:
    python -m kg.queries.co_occurrence
"""
from relationalai.semantics import select, where, count, std

# Import loaders + derived rules
import kg.loaders.observations  # noqa: F401
import kg.loaders.newcomb  # noqa: F401
import kg.model.derived.co_occurrence  # noqa: F401
import kg.model.derived.community  # noqa: F401

from kg.model.core.observations import Observation
from kg.model.core.taxonomy import Species
from kg.model.core.features import Feature, Category
from kg.model.core.keys.key import Description
from kg.model.core.h3cell import H3Cell


def species_co_occurrence():
    """Each species with how many distinct species it co-occurs with."""
    obs1 = Observation.ref()
    obs2 = Observation.ref()
    s1 = Species.ref()
    s2 = Species.ref()
    df = where(
        obs1.co_occurs_with(obs2),
        obs1.species(s1),
        obs2.species(s2),
        s1 != s2,
    ).select(
        count(s2).per(s1),
        s1.name.alias("species"),
    ).to_df()
    if df.empty:
        return df
    df.columns = ["co_occurring_count", "species"]
    return df.sort_values("co_occurring_count", ascending=False).reset_index(drop=True)


def species_co_occurrence_graph():
    """All species co-occurrence pairs (edges for a graph)."""
    obs1 = Observation.ref()
    obs2 = Observation.ref()
    s1 = Species.ref()
    s2 = Species.ref()
    return where(
        obs1.co_occurs_with(obs2),
        obs1.species(s1),
        obs2.species(s2),
        s1.name < s2.name,
    ).select(
        s1.name.alias("source"),
        s2.name.alias("target"),
    ).to_df()


def species_co_occurrence_in_cell(h3_index: int):
    """All species observed in a specific H3 res-9 cell."""
    obs = Observation.ref()
    cell = H3Cell.ref()
    s = Species.ref()
    return where(
        obs.h3cell(cell),
        cell.index == h3_index,
        obs.species(s),
    ).select(
        count(obs).per(s),
        s.name,
    ).to_df()


GRANULARITIES = {
    "day": std.datetime.date.dayofyear,
    "week": std.datetime.date.week,
    "month": std.datetime.date.month,
    "quarter": std.datetime.date.quarter,
}


def co_occurrence_for_species(species_name: str, granularity: str = "day"):
    """What species co-occur with a given species at a given temporal granularity?"""
    date_fn = GRANULARITIES.get(granularity)
    if not date_fn:
        raise ValueError(f"Unknown granularity: {granularity}")

    obs1 = Observation.ref()
    obs2 = Observation.ref()
    s1 = Species.ref()
    s2 = Species.ref()
    cell = H3Cell.ref()
    time_cond = date_fn(obs1.date) == date_fn(obs2.date)
    return where(
        obs1.h3cell(cell),
        obs2.h3cell(cell),
        time_cond,
        obs1.species(s1),
        obs2.species(s2),
        s1.name == species_name,
        s1 != s2,
        obs1 != obs2,
    ).select(
        s2.name.alias("co_occurring_species"),
    ).to_df()


def shared_features_for_co_occurring_species(species_name: str):
    """Feature values of co-occurring species, with count of how many share each trait."""
    obs1 = Observation.ref()
    obs2 = Observation.ref()
    s1 = Species.ref()
    s2 = Species.ref()
    fv = Category.ref()
    ik = Description.ref()
    return where(
        obs1.co_occurs_with(obs2),
        obs1.species(s1),
        obs2.species(s2),
        s1.name == species_name,
        s1 != s2,
        ik.describes(s2),
        ik.category(fv),
        ik.feature(Feature),
    ).select(
        Feature.name.alias("feature"),
        fv.value.alias("value"),
        count(s2).per(fv),
    ).to_df()


def species_communities():
    """Species grouped by WCC community."""
    s = Species.ref()
    community = Species.ref()
    return where(
        s.community(community),
    ).select(
        community.name.alias("community"),
        s.name.alias("species"),
    ).to_df()


def community_summary():
    """Count of species per community."""
    s = Species.ref()
    community = Species.ref()
    df = where(
        s.community(community),
    ).select(
        count(s).per(community),
        community.name.alias("community"),
    ).to_df()
    if df.empty:
        return df
    df.columns = ["species_count", "community"]
    return df.sort_values("species_count", ascending=False).reset_index(drop=True)


def _sorted(df):
    if df.empty:
        return df
    return df.sort_values(df.columns[0], ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    print("\n--- Species Co-occurrence ---")
    print(_sorted(species_co_occurrence()).head(20))

    print("\n--- Co-occurring with Euonymus alatus ---")
    print(co_occurrence_for_species("Euonymus alatus").head(20))
