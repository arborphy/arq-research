"""Queries for Trail data."""
from relationalai.semantics import count, where

import kg.loaders.trails  # noqa: F401
import kg.loaders.observations  # noqa: F401
import kg.loaders.ecosites  # noqa: F401
import kg.loaders.gobotany  # noqa: F401

from kg.model.core.trails import Trail
from kg.model.core.h3cell import H3Cell, EcoSite
from kg.model.core.observations import Observation
from kg.model.core.taxonomy import Species
from kg.model.core.features import Feature, Category
from kg.model.core.keys.key import Description


def list_trails():
    """Return all trails with basic metadata."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    return (
        where(trail.h3_cells(cell))
        .select(trail.osm_id, trail.name, trail.highway, trail.surface)
        .to_df()
    )


def all_trail_cells():
    """Return H3 res-13 cell indices for all trails."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    return where(trail.h3_cells(cell)).select(cell.index).to_df()


def all_trail_observations():
    """Return all observations that fall on any trail cell."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    obs = Observation.ref()
    species = Species.ref()
    return (
        where(
            trail.h3_cells(cell),
            obs.h3cell(cell),
            Observation.species(obs, species),
        )
        .select(obs.inat_id, obs.latitude, obs.longitude, obs.date, obs.image_url, species.name)
        .to_df()
    )


def cells_for_trail(osm_id: str):
    """Return H3 res-13 cell indices for a given trail."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    return (
        where(trail.osm_id == osm_id, trail.h3_cells(cell))
        .select(cell.index)
        .to_df()
    )


def trail_ecosite_cells(osm_id: str):
    """Return trail H3 cells that overlap with an ecosite, with the ecosite id."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    ecosite = EcoSite.ref()
    return (
        where(
            trail.osm_id == osm_id,
            trail.h3_cells(cell),
            ecosite.h3_cells(cell),
        )
        .select(ecosite.ecosite_id, cell.index)
        .to_df()
    )


def all_trail_ecosite_cells():
    """Return all trail H3 cells that overlap with any ecosite, with the ecosite id."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    ecosite = EcoSite.ref()
    return (
        where(
            trail.h3_cells(cell),
            ecosite.h3_cells(cell),
        )
        .select(ecosite.ecosite_id, cell.index)
        .to_df()
    )


def ecosites_on_trail(osm_id: str):
    """Return ecosites whose res-13 H3 cells overlap with the trail."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    ecosite = EcoSite.ref()
    return (
        where(
            trail.osm_id == osm_id,
            trail.h3_cells(cell),
            ecosite.h3_cells(cell),
        )
        .select(ecosite.ecosite_id)
        .to_df()
    )


def all_trail_ecosites():
    """Return all ecosites that overlap with any trail cell."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    ecosite = EcoSite.ref()
    return (
        where(
            trail.h3_cells(cell),
            ecosite.h3_cells(cell),
        )
        .select(ecosite.ecosite_id)
        .to_df()
    )


def species_on_trail(osm_id: str):
    """Return distinct species observed on a trail."""
    species = Species.ref()
    return (
        where(
            Trail.osm_id == osm_id,

            Trail.h3_cells(H3Cell),

            Observation.h3cell(H3Cell),
            Observation.species(species),
        )
        .select(species.name)
        .to_df()
    )


def observations_on_trail(osm_id: str):
    """Return observations whose res-13 H3 cell overlaps with the trail."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    obs = Observation.ref()
    species = Species.ref()
    return (
        where(
            trail.osm_id == osm_id,
            trail.h3_cells(cell),
            obs.h3cell(cell),
            Observation.species(obs, species),
        )
        .select(obs.inat_id, obs.latitude, obs.longitude, obs.date, obs.image_url, species.name)
        .to_df()
    )


def features_for_trail(osm_id: str):
    """Return feature/value pairs (with species count) for species observed on a trail."""
    species = Species.ref()
    desc = Description.ref()
    cat = Category.ref()
    feat = Feature.ref()
    return (
        where(
            Trail.osm_id == osm_id,
            Trail.h3_cells(H3Cell),
            Observation.h3cell(H3Cell),
            Observation.species(species),
            desc.describes(species),
            desc.category(cat),
            cat.feature(feat),
        )
        .select(feat.name, cat.value, count(species).per(feat, cat))
        .to_df()
    )


def filtered_species_on_trail(osm_id: str, filters: list[dict]):
    """Return species on a trail that match all given feature filters."""
    species = Species.ref()
    conds: list = [
        Trail.osm_id == osm_id,
        Trail.h3_cells(H3Cell),
        Observation.h3cell(H3Cell),
        Observation.species(species),
    ]
    for f in filters:
        desc = Description.ref()
        cat = Category.ref()
        feat = Feature.ref()
        conds.extend([
            desc.describes(species),
            desc.category(cat),
            cat.feature(feat),
            feat.name == f["feature"],
            cat.value == f["value"],
        ])
    return where(*conds).select(species.name).to_df()
