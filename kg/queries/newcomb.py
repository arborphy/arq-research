"""Sample queries for the Newcomb wildflower knowledge graph.

These queries demonstrate common use cases achievable with
Newcomb-loaded data. They rely on the derived Species.feature_values
rule from kg.model.derived.species_features.

Usage:
    import kg.model.derived  # ensure derived rules are loaded
    from kg.queries.newcomb import species_features, identify_by_features

    species_features("Symphyotrichum laeve")
    identify_by_features({"Flower Type": "Irregular Flowers", "Plant Type": "Vines"})
"""
from relationalai.semantics import select, where, count

from kg.model.core.taxonomy import Species
from kg.model.core.features import Feature, FeatureValue
from kg.model.core.keys.key import IdentificationKey
from kg.model.core.keys.newcomb import NewcombKey


# ------------------------------------------------------------------
# 1. Lookup: What features does a species have?
# ------------------------------------------------------------------
def species_features(species_name: str):
    """Return all feature-value pairs for a given species.

    Example:
        species_features("Symphyotrichum laeve")
        #   name                    feature          value
        # 0 Symphyotrichum laeve    Flower Type      Asters (Aster)
        # 1 Symphyotrichum laeve    Plant Type       Wildflowers ...
        # 2 Symphyotrichum laeve    Leaf Type        Leaves entire
    """
    return where(
        Species.name == species_name,
        Species.feature_values(FeatureValue),
        feat := FeatureValue.feature.name,
    ).select(
        Species.name,
        feat,
        FeatureValue.value,
    ).to_df()


# ------------------------------------------------------------------
# 2. Identification: Find species matching a set of traits
# ------------------------------------------------------------------
def identify_by_features(traits: dict[str, str]):
    """Find species that match ALL given {feature_name: value} pairs.

    Each entry adds an AND constraint — only species possessing every
    listed trait are returned.

    Example:
        identify_by_features({
            "Flower Type": "Irregular Flowers",
            "Plant Type": "Vines",
            "Leaf Type": "Leaves Divided",
        })
    """
    conditions = []
    for feature_name, value in traits.items():
        fv = FeatureValue.ref()
        conditions.extend([
            Species.feature_values(fv),
            fv.feature.name == feature_name,
            fv.value == value,
        ])
    return where(*conditions).select(Species.name).to_df()


# ------------------------------------------------------------------
# 3. Aggregation: How many species per feature value?
# ------------------------------------------------------------------
def species_count_per_value(feature_name: str):
    """Count species for each value of a given feature.

    Example:
        species_count_per_value("Flower Type")
        #   value                    species_count
        # 0 5 Regular Parts          187
        # 1 Irregular Flowers        143
        # 2 Asters (Aster)            62
        # ...
    """
    return where(
        FeatureValue.feature.name == feature_name,
        Species.feature_values(FeatureValue),
    ).select(
        FeatureValue.value,
        count(Species).per(FeatureValue),
    ).to_df()


# ------------------------------------------------------------------
# 4. Cross-feature: What values of feature B co-occur with a value
#    of feature A?
# ------------------------------------------------------------------
def cross_feature_analysis(
    source_feature: str,
    source_value: str,
    target_feature: str,
):
    """For species with source_feature=source_value, count how many
    have each value of target_feature.

    Example:
        cross_feature_analysis(
            "Flower Type", "Irregular Flowers", "Leaf Type",
        )
        #   target_value              species_count
        # 0 Leaves Entire             45
        # 1 Leaves Toothed or Lobed   38
        # ...
    """
    fv_src = FeatureValue.ref()
    fv_tgt = FeatureValue.ref()
    return where(
        Species.feature_values(fv_src),
        fv_src.feature.name == source_feature,
        fv_src.value == source_value,
        Species.feature_values(fv_tgt),
        fv_tgt.feature.name == target_feature,
    ).select(
        fv_tgt.value,
        count(Species).per(fv_tgt),
    ).to_df()


# ------------------------------------------------------------------
# 5. Similarity: Species pairs sharing feature values
# ------------------------------------------------------------------
def species_sharing_features():
    """Find species pairs and how many feature values they share.

    Uses IdentificationKey directly (avoids ref issues with the
    derived shortcut). Species in the same Newcomb key group will
    share all three top-level feature values.

    Example:
        species_sharing_features()
        #   species_1           species_2           shared_features
        # 0 Asclepias syriaca   Asclepias tuberosa  3
        # ...
    """
    s2 = Species.ref()
    ik2 = IdentificationKey.ref()
    return where(
        IdentificationKey.species(Species),
        ik2.species(s2),
        IdentificationKey.feature_value(FeatureValue),
        ik2.feature_value(FeatureValue),
        Species.name < s2.name,
    ).select(
        Species.name,
        s2.name,
        count(FeatureValue).per(Species, s2),
    ).to_df()


# ------------------------------------------------------------------
# 6. Coverage: How many species per key group?
# ------------------------------------------------------------------
def species_per_key_group():
    """Count species per IdentificationKey group (Newcomb key value).

    Example:
        species_per_key_group()
        #   value       species_count
        # 0 Group 511   23
        # 1 Group 522   18
        # ...
    """
    return select(
        IdentificationKey.value,
        count(IdentificationKey.species).per(IdentificationKey.value),
    ).to_df()


# ------------------------------------------------------------------
# 7. Newcomb key info for species
# ------------------------------------------------------------------
def newcomb_key_for_species(species_name: str):
    """Return the NewcombKey group number and trait values for a species."""
    return where(
        NewcombKey.species(Species),
        Species.name == species_name,
    ).select(
        NewcombKey.group_number,
        NewcombKey.flower_type,
        NewcombKey.plant_type,
        NewcombKey.leaf_type,
    ).to_df()


def species_with_newcomb_keys():
    """Return all species with their NewcombKey group numbers."""
    return where(
        NewcombKey.species(Species),
    ).select(
        Species.name,
        NewcombKey.group_number,
        NewcombKey.flower_type,
        NewcombKey.plant_type,
        NewcombKey.leaf_type,
    ).to_df()
