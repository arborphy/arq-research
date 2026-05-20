"""Load Newcomb species data from Snowflake into the KG.

Maps stg_newcomb_species columns to:
  - Species (linked via species_inat)
  - Feature / Category (flower_type, plant_type, leaf_type)
  - Description (one per species, version="1977", describes the species)
  - DataSource (Newcomb's Wildflower Guide)
"""
from relationalai.semantics import String, define, where

from kg.model import m
from kg.model.core.taxonomy import Species
from kg.model.core.features import Feature, Category
from kg.model.core.keys.key import Description
from kg.model.core.provenance import DataSource

DB = "RAI_DEMO"
SCHEMA = "CB_WEBAPP"

newcomb_table = m.Table(f"{DB}.{SCHEMA}.stg_newcomb_species", schema={
    "SPECIES_INAT": String,
    "SPECIES_INAT_LINK": String,
    "KEY_FLOWER_TYPE": String,
    "KEY_PLANT_TYPE": String,
    "KEY_LEAF_TYPE": String,
    "KEY_GROUP_NUMBER": String,
})

# -- Static entities --
define(
    DataSource.new(name="Newcomb's Wildflower Guide"),
    Feature.new(name="flower_type"),
    Feature.new(name="plant_type"),
    Feature.new(name="leaf_type"),
)

# -- Species --
define(Species.new(name=newcomb_table.SPECIES_INAT))

where(species := Species.filter_by(name=newcomb_table.SPECIES_INAT)).define(
    species.inat_link(newcomb_table.SPECIES_INAT_LINK),
    Species.source(species, DataSource.filter_by(name="Newcomb's Wildflower Guide")),
)

# -- Categories (categorical feature values) --
define(Category.new(value=newcomb_table.KEY_FLOWER_TYPE))
define(Category.new(value=newcomb_table.KEY_PLANT_TYPE))
define(Category.new(value=newcomb_table.KEY_LEAF_TYPE))

where(cat := Category.filter_by(value=newcomb_table.KEY_FLOWER_TYPE)).define(
    cat.name(newcomb_table.KEY_FLOWER_TYPE),
    Category.feature(cat, Feature.filter_by(name="flower_type")),
)
where(cat := Category.filter_by(value=newcomb_table.KEY_PLANT_TYPE)).define(
    cat.name(newcomb_table.KEY_PLANT_TYPE),
    Category.feature(cat, Feature.filter_by(name="plant_type")),
)
where(cat := Category.filter_by(value=newcomb_table.KEY_LEAF_TYPE)).define(
    cat.name(newcomb_table.KEY_LEAF_TYPE),
    Category.feature(cat, Feature.filter_by(name="leaf_type")),
)

# -- Description: one per species, linking to its three feature categories --
define(Description.new(name=newcomb_table.SPECIES_INAT, version="1977"))

where(
    desc    := Description.filter_by(name=newcomb_table.SPECIES_INAT, version="1977"),
    species := Species.filter_by(name=newcomb_table.SPECIES_INAT),
).define(
    desc.describes(species),
    Description.source(desc, DataSource.filter_by(name="Newcomb's Wildflower Guide")),
    Description.category(desc, Category.filter_by(value=newcomb_table.KEY_FLOWER_TYPE)),
    Description.category(desc, Category.filter_by(value=newcomb_table.KEY_PLANT_TYPE)),
    Description.category(desc, Category.filter_by(value=newcomb_table.KEY_LEAF_TYPE)),
)
