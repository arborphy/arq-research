"""Transitive closure over part_of — the taxonomic analog of within over located_in.

`within_clade` is to `part_of` what `within` is to `located_in`:
a transitive predicate that collapses multi-hop hierarchies into a single query.

    # Is Trillium grandiflorum within the Liliaceae family? (two hops via part_of)
    s = Species.ref()
    f = Family.ref()
    where(s.name == "Trillium grandiflorum", within_clade(s, f), f.name == "Liliaceae")

Rules:
    within_clade(x, anc)  :- part_of(x, anc)
    within_clade(x, anc)  :- within_clade(x, mid), part_of(mid, anc)
"""
from relationalai.semantics import define

from kg.model.core.entity import Entity
from kg.model.core.taxonomy import Taxon
from kg.model.core.predicates import part_of, within_clade

x   = Entity.ref()
mid = Taxon.ref()
anc = Taxon.ref()

# Base: any direct part_of is also within_clade
define(within_clade(x, anc)).where(
    part_of(x, anc),
)

# Recursive: propagate through part_of chains
define(within_clade(x, anc)).where(
    within_clade(x, mid),
    part_of(mid, anc),
)
