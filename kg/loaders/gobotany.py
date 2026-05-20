"""Load GoBotany data from Snowflake into the KG.

Tables consumed:
  - gobotany_taxon                    → Species, Family, Genus + taxonomy hierarchy
  - gobotany_feature                  → Feature
  - gobotany_feature_value            → Category
  - gobotany_taxon_feature_value      → (species × feature × value assertions)
"""
from relationalai.semantics import Integer, String, define, where

from kg.model import m
from kg.model.core.taxonomy import Family, Genus, Species
from kg.model.core.predicates import part_of
from kg.model.core.features import Feature, Category
from kg.model.core.provenance import DataSource
from kg.model.core.keys.key import Description

DB = "RAI_DEMO"
SCHEMA = "CB_WEBAPP"

taxon_table = m.Table(f"{DB}.{SCHEMA}.gobotany_taxon", schema={
    "TAXON_ID": Integer,
    "SCIENTIFIC_NAME": String,
    "COMMON_NAME": String,
    "GENUS": String,
    "FAMILY": String,
    "SPECIES_URL": String,
})

feature_table = m.Table(f"{DB}.{SCHEMA}.gobotany_feature", schema={
    "FEATURE_ID": String,
    "SOURCE_FEATURE_NAME": String,
    "DISPLAY_NAME": String,
    "FEATURE_GROUP": String,
    "VALUE_TYPE": String,
})

fv_table = m.Table(f"{DB}.{SCHEMA}.gobotany_feature_value", schema={
    "FEATURE_VALUE_ID": String,
    "FEATURE_ID": String,
    "VALUE_LABEL": String,
    "DISPLAY_LABEL": String,
})

# Links taxon_id → feature_id + feature_value_id
tfv_table = m.Table(f"{DB}.{SCHEMA}.gobotany_taxon_feature_value", schema={
    "TAXON_ID": Integer,
    "FEATURE_ID": String,
    "FEATURE_VALUE_ID": String,
})


# -- DataSource --
define(DataSource.new(name="GoBotany"))

# -- Taxonomy --
define(Family.new(name=taxon_table.FAMILY))
define(Genus.new(name=taxon_table.GENUS))
define(Species.new(name=taxon_table.SCIENTIFIC_NAME))

where(s := Species.filter_by(name=taxon_table.SCIENTIFIC_NAME)).define(
    s.common_name(taxon_table.COMMON_NAME),
    Species.source(s, DataSource.filter_by(name="GoBotany")),
)

where(
    g := Genus.filter_by(name=taxon_table.GENUS),
    f := Family.filter_by(name=taxon_table.FAMILY),
).define(part_of(g, f))

where(
    s := Species.filter_by(name=taxon_table.SCIENTIFIC_NAME),
    g := Genus.filter_by(name=taxon_table.GENUS),
).define(part_of(s, g))

# -- Features --
define(Feature.new(name=feature_table.DISPLAY_NAME))
where(feat := Feature.filter_by(name=feature_table.DISPLAY_NAME)).define(
    Feature.source(feat, DataSource.filter_by(name="GoBotany")),
)

# -- Categories (discrete values only; skip numeric ranges, "NA" sentinels, and "absent" values) --
where(
    fv_table.VALUE_LABEL != "", fv_table.VALUE_LABEL != "NA", fv_table.VALUE_LABEL != "absent",
).define(Category.new(value=fv_table.VALUE_LABEL))

where(
    fv_table.VALUE_LABEL != "", fv_table.VALUE_LABEL != "NA", fv_table.VALUE_LABEL != "absent",
    fv_table.FEATURE_ID == feature_table.FEATURE_ID,
    cat := Category.filter_by(value=fv_table.VALUE_LABEL),
    feat := Feature.filter_by(name=feature_table.DISPLAY_NAME),
).define(
    cat.name(fv_table.DISPLAY_LABEL),
    Category.feature(cat, feat),
    Category.source(cat, DataSource.filter_by(name="GoBotany")),
)

# -- Descriptions: one per species, seeded from taxon_feature_value --
where(taxon_table.SCIENTIFIC_NAME != "").define(
    Description.new(name=taxon_table.SCIENTIFIC_NAME, version="gobotany_api_v2")
)

where(
    taxon_table.SCIENTIFIC_NAME != "",
    desc := Description.filter_by(name=taxon_table.SCIENTIFIC_NAME, version="gobotany_api_v2"),
    s := Species.filter_by(name=taxon_table.SCIENTIFIC_NAME),
).define(
    desc.describes(s),
    Description.source(desc, DataSource.filter_by(name="GoBotany")),
)

where(
    tfv_table.TAXON_ID == taxon_table.TAXON_ID,
    tfv_table.FEATURE_VALUE_ID == fv_table.FEATURE_VALUE_ID,
    fv_table.VALUE_LABEL != "", fv_table.VALUE_LABEL != "NA", fv_table.VALUE_LABEL != "absent",
    taxon_table.SCIENTIFIC_NAME != "",
    desc := Description.filter_by(name=taxon_table.SCIENTIFIC_NAME, version="gobotany_api_v2"),
    cat := Category.filter_by(value=fv_table.VALUE_LABEL),
).define(
    Description.category(desc, cat),
)
