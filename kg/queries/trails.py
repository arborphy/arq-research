"""Queries for Trail data."""
from relationalai.semantics import where

import kg.loaders.trails  # noqa: F401
import kg.loaders.observations  # noqa: F401
import kg.loaders.ecosites  # noqa: F401

from kg.model.core.trails import Trail
from kg.model.core.h3cell import H3Cell, EcoSite
from kg.model.core.observations import Observation
from kg.model.core.taxonomy import Species
from kg.model.core.provenance import DataSource
from webapp.backend.cache import ttl_cache


# Trail geometry is static reference data (loaded once from OSM) → long TTL.
# Anything that joins trails with observations gets the shorter `trails` TTL
# so it picks up new observations within 5 minutes.
@ttl_cache(ttl_seconds=3600, namespace="ref")
def list_trails():
    """Return all trails with basic metadata."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    return (
        where(trail.h3_cells(cell))
        .select(trail.osm_id, trail.name, trail.highway, trail.surface)
        .to_df()
    )


@ttl_cache(ttl_seconds=3600, namespace="ref")
def all_trail_cells():
    """Return H3 res-13 cell indices for all trails."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    return where(trail.h3_cells(cell)).select(cell.index).to_df()


@ttl_cache(ttl_seconds=300, namespace="trails")
def all_trail_observations():
    """Return all observations that fall on any trail cell."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    obs = Observation.ref()
    species = Species.ref()
    datasource = DataSource.ref()
    return (
        where(
            trail.h3_cells(cell),
            obs.h3cell(cell),
            Observation.species(obs, species),
            Observation.source(obs, datasource),
        )
        .select(obs.inat_id, obs.latitude, obs.longitude, obs.date, obs.image_url, species.name, datasource.name)
        .to_df()
    )


@ttl_cache(ttl_seconds=3600, namespace="ref")
def cells_for_trail(osm_id: str):
    """Return H3 res-13 cell indices for a given trail."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    return (
        where(trail.osm_id == osm_id, trail.h3_cells(cell))
        .select(cell.index)
        .to_df()
    )


@ttl_cache(ttl_seconds=3600, namespace="ref")
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


@ttl_cache(ttl_seconds=3600, namespace="ref")
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


@ttl_cache(ttl_seconds=3600, namespace="ref")
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


@ttl_cache(ttl_seconds=3600, namespace="ref")
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


@ttl_cache(ttl_seconds=300, namespace="trails")
def observations_on_trail(osm_id: str):
    """Return observations whose res-13 H3 cell overlaps with the trail."""
    trail = Trail.ref()
    cell = H3Cell.ref()
    obs = Observation.ref()
    species = Species.ref()
    datasource = DataSource.ref()
    return (
        where(
            trail.osm_id == osm_id,
            trail.h3_cells(cell),
            obs.h3cell(cell),
            Observation.species(obs, species),
            Observation.source(obs, datasource),
        )
        .select(obs.inat_id, obs.latitude, obs.longitude, obs.date, obs.image_url, species.name, datasource.name)
        .to_df()
    )
