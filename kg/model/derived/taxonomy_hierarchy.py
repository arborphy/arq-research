"""Derive taxonomy hierarchy using part_of.

  Species part_of Genus   — extracted from binomial species name
  Genus   part_of Kingdom — extracted from Species.iconic_taxon
"""
from relationalai.semantics import define, std, where

from kg.model.core.taxonomy import Genus, Kingdom, Species

# --- Species part_of Genus ---
# "Trillium grandiflorum" → Genus "Trillium"
genus_name = std.strings.split_part(Species.name, " ", 0)

define(Genus.new(name=genus_name))

where(g := Genus.filter_by(name=genus_name)).define(
    Species.part_of(Species, g),
)

# --- Genus part_of Kingdom ---
# Derive kingdom from Species.iconic_taxon (e.g. "Plantae")
define(Kingdom.new(name=Species.iconic_taxon))

where(
    k := Kingdom.filter_by(name=Species.iconic_taxon),
    g := Genus.filter_by(name=genus_name),
).define(
    g.part_of(k),
)
