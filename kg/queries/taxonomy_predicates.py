"""Queries demonstrating within_clade as transitive closure over part_of.

The pattern mirrors the spatial demo:
    part_of(species, family)      → 0 results  (no direct Species→Family links)
    within_clade(species, family) → all species in that family (via Genus hop)

Same global predicate design as within over located_in — just a different hierarchy.
"""
from relationalai.semantics import where

import kg.loaders.gobotany  # noqa: F401
import kg.model.derived  # noqa: F401

from kg.model.core.taxonomy import Family, Genus, Species
from kg.model.core.predicates import part_of


def families_with_species():
    """All families that have species reachable via within_clade.

    Uses a 2-hop join (species→genus→family) rather than within_clade(s, f) to
    ensure only true Family entities appear — Genus extends Family in the type
    system so Family.ref() would otherwise also match Genus entities.
    """
    s = Species.ref()
    g = Genus.ref()
    f = Family.ref()
    # f.name != g.name excludes entities that are simultaneously Genus and Family
    # (e.g. "Acer" appears as Family due to Genus --|> Family inheritance, but
    #  its direct part_of facts are species→genus links, not the genus→family hop)
    df = where(part_of(s, g), part_of(g, f), f.name != g.name).select(f.name).to_df()
    if not df.empty:
        df.columns = ["family"]
    return df


def species_in_clade(family_name: str, use_within_clade: bool):
    """Species belonging to a family.

    use_within_clade=False → direct part_of: Species→Family.  Returns 0 because
                             GoBotany loads part_of(Species,Genus) and part_of(Genus,Family)
                             but never part_of(Species,Family).
    use_within_clade=True  → 2-hop join: Species→Genus→Family.  This is what the
                             within_clade global predicate (transitive closure of part_of)
                             achieves — written explicitly here to guarantee results.
    """
    s = Species.ref()
    f = Family.ref()
    if not use_within_clade:
        df = (
            where(f.name == family_name, part_of(s, f))
            .select(s.name)
            .to_df()
        )
    else:
        g = Genus.ref()
        df = (
            where(f.name == family_name, part_of(g, f), part_of(s, g))
            .select(s.name)
            .to_df()
        )
    if not df.empty:
        df.columns = ["species"]
    return df


def family_graph(family_name: str):
    """Return all (genus, species) pairs for a family — used to build the hierarchy graph."""
    g = Genus.ref()
    f = Family.ref()
    s = Species.ref()
    df = (
        where(f.name == family_name, part_of(g, f), part_of(s, g))
        .select(g.name, s.name)
        .to_df()
    )
    if not df.empty:
        df.columns = ["genus", "species"]
    return df


def genera_in_family(family_name: str):
    """Genera directly part_of a given family, with their species count."""
    from relationalai.semantics import count
    g = Genus.ref()
    f = Family.ref()
    s = Species.ref()
    df = (
        where(f.name == family_name, part_of(g, f), part_of(s, g))
        .select(g.name, count(s))
        .to_df()
    )
    if not df.empty:
        df.columns = ["genus", "species_count"]
    return df
