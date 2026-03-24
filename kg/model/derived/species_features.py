"""Derived rule: Species → FeatureValue shortcut.

Traverses the IdentificationKey chain to derive a direct
Species.feature_values relationship, so queries don't need
to go through IdentificationKey every time.

    IdentificationKey.species → Species
    IdentificationKey.feature_value → FeatureValue
    ⟹  Species.feature_values → FeatureValue
"""
from relationalai.semantics import define

from kg.model.core.taxonomy import Species
from kg.model.core.features import FeatureValue
from kg.model.core.keys.key import IdentificationKey

define(Species.feature_values(Species, FeatureValue)).where(
    IdentificationKey.species(Species),
    IdentificationKey.feature_value(FeatureValue),
)
