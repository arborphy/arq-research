"""Geographic queries for observation locations and H3 cells.

Usage:
    from kg.queries.geography import observations_for_species, co_occurrence_cells_for_species
"""
from relationalai.semantics import select, where, count, std

import kg.loaders.observations  # noqa: F401
import kg.loaders.newcomb  # noqa: F401
import kg.model.derived.co_occurrence  # noqa: F401

from kg.model.core.observations import Observation
from kg.model.core.taxonomy import Species
from kg.model.core.h3cell import H3Cell


def observations_for_species(species_name: str):
    """Return lat/lon/date/inat_id for all observations of a species."""
    obs = Observation.ref()
    s = Species.ref()
    return where(
        obs.species(s),
        s.name == species_name,
    ).select(
        obs.latitude,
        obs.longitude,
        obs.date,
        obs.inat_id,
        obs.image_url,
    ).to_df()


def co_occurrence_cells_for_species(species_name: str):
    """Return H3 res-9 cell indexes where this species co-occurs with others."""
    obs1 = Observation.ref()
    obs2 = Observation.ref()
    cell = H3Cell.ref()
    s1 = Species.ref()
    df = where(
        obs1.co_occurs_with(obs2),
        obs1.species(s1),
        s1.name == species_name,
        obs1.h3cell(cell),
    ).select(
    cell.index,
        count(obs2).per(cell),
    ).to_df()
    if df.empty:
        return df
    df.columns = ["h3_index", "co_occurrence_count"]
    return df


def co_occurring_observations_for_species(species_name: str):
    """Return lat/lon/date/inat_id/species of observations that co-occur with a species."""
    obs1 = Observation.ref()
    obs2 = Observation.ref()
    s2 = Species.ref()
    s1 = Species.ref()
    return where(
        obs1.co_occurs_with(obs2),
        obs1.species(s1),
        s1.name == species_name,
        obs2.species(s2),
        s2.name != species_name,
    ).select(
        obs2.latitude,
        obs2.longitude,
        obs2.date,
        obs2.inat_id,
        s2.name,
    ).to_df()


def all_h3_cells():
    """Return all H3 res-13 cell indexes with observations."""
    obs = Observation.ref()
    cell = H3Cell.ref()
    return where(
        obs.h3cell(cell),
    ).select(
        cell.index,
    ).to_df()


def h3_cells_on_day(day_of_year: int):
    """Return H3 res-13 cells that have observations on a given day of year."""
    date = std.datetime.date
    obs = Observation.ref()
    cell = H3Cell.ref()
    return where(
        obs.h3cell(cell),
        date.dayofyear(obs.date) == day_of_year,
    ).select(
        cell.index,
        count(obs).per(cell),
    ).to_df()


def species_visible_at(h3_index: int, day_of_year: int):
    """Species observed in a given H3 res-13 cell on a given day of year (any year)."""
    date = std.datetime.date
    obs = Observation.ref()
    cell = H3Cell.ref()
    s = Species.ref()
    df = where(
        obs.h3cell(cell),
        cell.index == h3_index,
        date.dayofyear(obs.date) == day_of_year,
        obs.species(s),
    ).select(
        s.name,
        obs.image_url,
        obs.inat_id,
        obs.date,
    ).to_df()
    if df.empty:
        return df
    df.columns = ["species", "image_url", "inat_id", "date"]
    df["date"] = df["date"].astype(str)
    return df
