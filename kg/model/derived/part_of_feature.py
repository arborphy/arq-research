"""Derive part_of for Category → Feature and Measurement → Feature.

This makes the global part_of predicate span multiple concept domains:
  - H3Cell hierarchy (res12 → res9 → res7)  [from observations loader]
  - Category → Feature                       [this file]
  - Measurement → Feature                    [this file]
"""
from relationalai.semantics import define

from kg.model.core.features import Feature, Category, Measurement
from kg.model.core.predicates import part_of

define(part_of(Category, Feature)).where(Category.feature(Feature))
define(part_of(Measurement, Feature)).where(Measurement.feature(Feature))
