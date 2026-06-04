"""Queries for EcoSite data."""
from relationalai.semantics import select, where

import kg.loaders.ecosites  # noqa: F401
import kg.loaders.ecosites_compacted  # noqa: F401

from kg.model.core.h3cell import EcoSite, H3Cell
from webapp.backend.cache import ttl_cache


# Ecosite geometry is static NRCS data — long TTL.
@ttl_cache(ttl_seconds=3600, namespace="ref")
def list_ecosites():
    """Return all ecosite IDs."""
    ecosite = EcoSite.ref()
    return select(ecosite.ecosite_id).to_df()


@ttl_cache(ttl_seconds=3600, namespace="ref")
def cells_for_ecosite(ecosite_id: str):
    """Return all res-12 H3 cell indexes for a given ecosite."""
    ecosite = EcoSite.ref()
    cell = H3Cell.ref()
    return (
        where(
            ecosite.ecosite_id == ecosite_id,
            ecosite.h3_cells(cell),
        )
        .select(cell.index)
        .to_df()
    )


@ttl_cache(ttl_seconds=3600, namespace="ref")
def compacted_cells_for_ecosite(ecosite_id: str):
    """Return compacted H3 cell indexes (mixed resolution) for a given ecosite."""
    ecosite = EcoSite.ref()
    cell = H3Cell.ref()
    return (
        where(
            ecosite.ecosite_id == ecosite_id,
            ecosite.compacted_h3_cells(cell),
        )
        .select(cell.index)
        .to_df()
    )
