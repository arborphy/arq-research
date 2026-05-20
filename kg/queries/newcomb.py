"""Sample queries for the Newcomb wildflower knowledge graph.

These queries demonstrate common use cases achievable with
Newcomb-loaded data. They rely on the derived Species.categories
rule from kg.model.derived.species_features.

Usage:
    import kg.model.derived  # ensure derived rules are loaded
    from kg.queries.newcomb import species_features, identify_by_features

    species_features("Symphyotrichum laeve")
    identify_by_features({"Flower Type": "Irregular Flowers", "Plant Type": "Vines"})
"""
from relationalai.semantics import where, count

from kg.model.core.taxonomy import Species
from kg.model.core.features import Feature, Category
from kg.model.core.keys.key import Description


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
    cat = Category.ref()
    feat = Feature.ref()
    return where(
        Species.name == species_name,
        Species.categories(cat),
        Category.feature(cat, feat),
    ).select(
        Species.name,
        feat.name.alias("feature"),
        cat.value.alias("value"),
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
        cat = Category.ref()
        feat = Feature.ref()
        conditions.extend([
            Species.categories(cat),
            Category.feature(cat, feat),
            feat.name == feature_name,
            cat.value == value,
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
    cat = Category.ref()
    feat = Feature.ref()
    return where(
        Category.feature(cat, feat),
        feat.name == feature_name,
        Species.categories(cat),
    ).select(
        cat.value,
        count(Species).per(cat),
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
    cat_src = Category.ref()
    cat_tgt = Category.ref()
    feat_src = Feature.ref()
    feat_tgt = Feature.ref()
    return where(
        Species.categories(cat_src),
        Category.feature(cat_src, feat_src),
        feat_src.name == source_feature,
        cat_src.value == source_value,
        Species.categories(cat_tgt),
        Category.feature(cat_tgt, feat_tgt),
        feat_tgt.name == target_feature,
    ).select(
        cat_tgt.value,
        count(Species).per(cat_tgt),
    ).to_df()


# ------------------------------------------------------------------
# 5. Similarity: Species pairs sharing feature values
# ------------------------------------------------------------------
def species_sharing_features():
    """Find species pairs and how many feature values they share.

    Example:
        species_sharing_features()
        #   species_1           species_2           shared_features
        # 0 Asclepias syriaca   Asclepias tuberosa  3
        # ...
    """
    s2 = Species.ref()
    desc2 = Description.ref()
    return where(
        Description.describes(Species),
        desc2.describes(s2),
        Description.category(Category),
        desc2.category(Category),
        Species.name < s2.name,
    ).select(
        Species.name,
        s2.name,
        count(Category).per(Species, s2),
    ).to_df()


def newcomb_key_for_species(species_name: str):
    """Return the raw Newcomb key entry (group number + 3 feature values) for a species."""
    from kg.loaders.newcomb import newcomb_table
    return where(
        newcomb_table.SPECIES_INAT == species_name,
    ).select(
        newcomb_table.KEY_GROUP_NUMBER,
        newcomb_table.KEY_FLOWER_TYPE,
        newcomb_table.KEY_PLANT_TYPE,
        newcomb_table.KEY_LEAF_TYPE,
    ).to_df()


def datasources_for_species(species_name: str):
    """Return the datasources a species was loaded from."""
    from kg.model.core.provenance import DataSource
    return where(
        Species.name == species_name,
        Species.source(DataSource),
    ).select(
        DataSource.name,
    ).to_df()
