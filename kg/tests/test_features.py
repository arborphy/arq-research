"""Tests for feature and category use cases.

Verifies Newcomb's wildflower guide features (Flower Symmetry, Plant Type,
Leaf Type, Leaf Arrangement) and their categories using RAI queries.
"""

from relationalai.semantics import define, select, where

from kg.model.core.features import Feature, Category


class TestNewcombFeatures:
    """Verify the four Newcomb features are created correctly."""

    def test_four_features_exist(self, newcomb_features):
        """All four Newcomb features should be queryable."""
        df = select(Feature.name).to_df()
        names = df["name"].tolist()
        assert "Flower Symmetry" in names
        assert "Plant Type" in names
        assert "Leaf Type" in names
        assert "Leaf Arrangement" in names

    def test_feature_query_by_name(self, newcomb_features):
        """Query a specific feature by name."""
        df = where(Feature.name == "Plant Type").select(Feature.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Plant Type"


class TestCategories:
    """Verify categories and their relationships to features."""

    def test_plant_type_values(self, newcomb_features):
        """Plant Type should have Shrubs, Vines, Wildflowers categories."""
        feat = Feature.ref()
        cat = Category.ref()
        df = where(
            feat.name == "Plant Type",
            Category.feature(cat, feat),
        ).select(cat.value).to_df()
        values = df["value"].tolist()
        assert "Shrubs" in values
        assert "Vines" in values
        assert "Wildflowers" in values
        assert len(values) == 3

    def test_leaf_type_values(self, newcomb_features):
        """Leaf Type should have four categories."""
        feat = Feature.ref()
        cat = Category.ref()
        df = where(
            feat.name == "Leaf Type",
            Category.feature(cat, feat),
        ).select(cat.value).to_df()
        values = df["value"].tolist()
        assert "No apparent leaves" in values
        assert "Leaves entire" in values
        assert "Leaves toothed or lobed" in values
        assert "Leaves divided" in values
        assert len(values) == 4

    def test_value_belongs_to_one_feature(self, newcomb_features):
        """Each category value should belong to exactly one feature."""
        feat = Feature.ref()
        cat = Category.ref()
        df = where(
            cat.value == "Shrubs",
            Category.feature(cat, feat),
        ).select(feat.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Plant Type"

    def test_add_new_category(self, newcomb_features):
        """Add a new category to an existing feature and query it."""
        define(
            pt_trees := Category.new(value="Trees"),
            pt_trees.feature(newcomb_features["plant_type"]),
        )

        feat = Feature.ref()
        cat = Category.ref()
        df = where(
            feat.name == "Plant Type",
            Category.feature(cat, feat),
        ).select(cat.value).to_df()
        values = df["value"].tolist()
        assert "Trees" in values
