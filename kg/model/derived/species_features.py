"""Derived rules: Taxon → Category and Measurement shortcuts.

Collapses the Description hop so queries can go directly from a Taxon to
its categorical or quantitative feature observations.

    Description.describes → Taxon
    Description.category  → Category   ⟹  Taxon.categories  → Category
    Description.measurement → Measurement  ⟹  Taxon.measurements → Measurement
"""
from relationalai.semantics import define

from kg.model import m
from kg.model.core.taxonomy import Taxon
from kg.model.core.features import Category, Measurement
from kg.model.core.keys.key import Description

# Declare as multi-valued relationships (no :field_name — a taxon has MANY measurements/categories)
Taxon.categories = m.Relationship(f"{Taxon} has categories {Category}")
Taxon.measurements = m.Relationship(f"{Taxon} has measurements {Measurement}")

taxon = Taxon.ref()
category = Category.ref()
measurement = Measurement.ref()

define(Taxon.categories(taxon, category)).where(
    Description.describes(taxon),
    Description.category(category),
)

define(Taxon.measurements(taxon, measurement)).where(
    Description.describes(taxon),
    Description.measurement(measurement),
)
