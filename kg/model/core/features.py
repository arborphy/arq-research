from kg.model import m
from relationalai.semantics import String
from .entity import Entity

Feature = m.Concept("Feature", extends=[Entity])
Feature.display_name = m.Property(f"{Feature} has display name {String:display_name}")
Unit = m.Concept("Unit", extends=[Entity])

# Measurement: a quantitative observed value of a Feature (e.g. "5 leaves")
Measurement = m.Concept("Measurement", extends=[Entity])
Measurement.value = m.Property(f"{Measurement} has value {String:value}")
Measurement.unit = m.Relationship(f"{Measurement} measured in {Unit:unit}")
Measurement.feature = m.Relationship(f"{Measurement} of {Feature:feature}")

# Category: a categorical observed value of a Feature (e.g. "opposite" leaves)
# Categories form a hierarchy — sub-categories nest inside parent categories.
Category = m.Concept("Category", extends=[Entity])
Category.value = m.Property(f"{Category} has value {String:value}")
Category.feature = m.Relationship(f"{Category} is value for {Feature:feature}")
Category.sub_category = m.Relationship(f"{Category} has sub-category {Category:sub_category}")