"""Global predicates — relationships not bound to any specific concept.

These are first-class objects callable as ``pred(subject, object)`` in both
define and where contexts, making the same predicate reusable across any pair
of Entity subtypes without going through a concept attribute.

Usage in define (loaders):
    from kg.model.core.predicates import part_of
    part_of(cell9, H3Cell.filter_by(index=res7_idx))

Usage in queries:
    from kg.model.core.predicates import part_of
    c = Species.ref()
    p = Genus.ref()
    where(part_of(c, p)).select(c.name, p.name).to_df()

    # Terminal nodes (not contained by anything at the same level):
    leaf = H3Cell.ref()
    parent = H3Cell.ref()
    where(part_of(leaf, H3Cell), ~part_of(parent, leaf)).select(leaf.index).to_df()
"""
from kg.model import m
from kg.model.core.entity import Entity, Location
from kg.model.core.taxonomy import Taxon

part_of = m.Relationship(f"{Entity} part of {Entity:part_of}")
has_part = m.Relationship(f"{Entity} has part {Entity:has_part}")
located_in = m.Relationship(f"{Entity} located in {Location}")
within = m.Relationship(f"{Entity} within {Location}")
within_clade = m.Relationship(f"{Entity}{Taxon}")
observed_in = m.Relationship(f"{Taxon} observed in {Location}")
