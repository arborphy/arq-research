"""Queries for species co-existence within EcoSites.

Path: Species → Observation → H3Cell → EcoSite

Observations and EcoSite cells must share the same H3 cell index for a match.
Resolution mismatches (compacted ecosite cells vs obs cells) will return no results
for affected ecosites — to be addressed when resolution alignment is added.
"""
import pandas as pd
from relationalai.semantics import where

import kg.loaders.observations  # noqa: F401
import kg.loaders.ecosites  # noqa: F401
import kg.model.derived  # noqa: F401

from kg.model.core.taxonomy import Species
from kg.model.core.observations import Observation
from kg.model.core.h3cell import H3Cell, EcoSite


def ecosites_with_observations() -> pd.DataFrame:
    """Return ecosite IDs that have at least one observation."""
    obs = Observation.ref()
    cell = H3Cell.ref()
    ecosite = EcoSite.ref()
    df = (
        where(
            Observation.h3cell(obs, cell),
            EcoSite.h3_cells(ecosite, cell),
        )
        .select(ecosite.ecosite_id)
        .to_df()
    )
    if not df.empty:
        df.columns = ["ecosite_id"]
    return df


def species_in_ecosite(ecosite_id: str) -> pd.DataFrame:
    """Return all species with observations in an ecosite."""
    obs = Observation.ref()
    cell = H3Cell.ref()
    ecosite = EcoSite.ref()
    s = Species.ref()
    df = (
        where(
            ecosite.ecosite_id == ecosite_id,
            EcoSite.h3_cells(ecosite, cell),
            Observation.h3cell(obs, cell),
            Observation.species(obs, s),
        )
        .select(s.name)
        .to_df()
    )
    if not df.empty:
        df.columns = ["species"]
    return df
