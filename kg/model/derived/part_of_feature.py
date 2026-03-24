"""Derive part_of for FeatureValue → Feature.

This makes the global Entity.part_of predicate span multiple concept domains:
  - H3Cell hierarchy (res12 → res9 → res7)  [from observations loader]
  - FeatureValue → Feature                   [this file]
"""
from relationalai.semantics import define

from kg.model.core.features import Feature, FeatureValue

define(FeatureValue.part_of(FeatureValue, Feature)).where(
    FeatureValue.feature(Feature),
)
