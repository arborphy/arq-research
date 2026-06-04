"""Instance — a persistent, spatially-located entity in the world.

An Instance is a concrete manifestation of a taxon (or abiotic feature) at a
specific place. It accumulates observations over time and is distinct from any
single Observation. Multiple Observations may be evidence for a single Instance;
a single Observation may link to multiple Instances (e.g., a patch of plants).

Instance types:
  tree              — an individual tree
  rock              — a rock or boulder (glacial erratic, outcrop, etc.)
  population        — a population of plants (herbaceous, perennial or annual)
  ecosite           — an ecological survey site / community patch
  built_environment — infrastructure: road, bridge, parking lot, catwalk/puncheon, etc.
  trail_feature     — a named feature on or along a trail

Location model:
  - lat/lon provides the precise point
  - h3_cell provides approximate cell membership at a given resolution
    (for trails: the trail geography IS the union of its H3 cells)
  - osm_id links built-environment and trail instances to OpenStreetMap

Subtype details captured via free-type properties:
  - rock_subtype:      'glacial_erratic' | 'igneous' | 'sedimentary' | 'metamorphic'
  - built_env_subtype: 'parking_lot' | 'road' | 'bridge' | 'trail' | 'catwalk_puncheon'
  - lifecycle:         'perennial' | 'annual'   (for population instances)

Temporal existence:
  - first_observed is set on creation
  - last_observed is derived from linked Observations (set by loaders/queries)

NOTE: This concept is a design implementation — populating it requires a loader
that reads from a future Snowflake table or JSON payload (e.g., from Quest Maker
exports). The RAI model is defined here; data population is tracked in
arq-research/kg/loaders/instances.py (to be created).
"""

from kg.model import m
from relationalai.semantics import Date, Float, String
from .entity import Entity
from .h3cell import H3Cell
from .observations import Observation


Instance = m.Concept("Instance", extends=[Entity])

# ---- Instance type -------------------------------------------------------

# The broad category of this instance
Instance.instance_type = m.Property(
    f"{Instance} has instance type {String:instance_type}"
)
# Values: 'tree' | 'rock' | 'population' | 'ecosite' | 'built_environment' | 'trail_feature'

# Subtype refinements (null when not applicable)
Instance.rock_subtype = m.Property(
    f"{Instance} has rock subtype {String:rock_subtype}"
)
# Values: 'glacial_erratic' | 'igneous' | 'sedimentary' | 'metamorphic'

Instance.built_env_subtype = m.Property(
    f"{Instance} has built environment subtype {String:built_env_subtype}"
)
# Values: 'parking_lot' | 'road' | 'bridge' | 'trail' | 'catwalk_puncheon'

Instance.lifecycle = m.Property(
    f"{Instance} has lifecycle {String:lifecycle}"
)
# Values: 'perennial' | 'annual'  (for population instances)

# ---- Location ------------------------------------------------------------

Instance.latitude  = m.Property(f"{Instance} at latitude {Float:latitude}")
Instance.longitude = m.Property(f"{Instance} at longitude {Float:longitude}")

# OSM id for built-environment and trail instances
Instance.osm_id = m.Property(f"{Instance} has OSM id {String:osm_id}")

# H3 cell membership (resolution stored as part of the H3Cell entity)
Instance.h3_cell = m.Relationship(f"{Instance} located in {H3Cell:h3_cell}")

# ---- Temporal existence --------------------------------------------------

Instance.first_observed = m.Property(
    f"{Instance} first observed on {Date:first_observed}"
)
Instance.last_observed = m.Property(
    f"{Instance} last observed on {Date:last_observed}"
)

# ---- Taxon linkage -------------------------------------------------------
# The taxon this instance is of. Null for purely abiotic instances (rocks,
# built environment). Population instances may link to Species or Genus.
# Stored as a string key here; the Taxon relationship is wired in the loader
# (kg/loaders/instances.py, to be created) using the GBIF taxon id.

Instance.taxon_id = m.Property(
    f"{Instance} has taxon id {String:taxon_id}"
)
# Taxon rank context (mirrors Taxon.rank but cached on Instance for query convenience)
Instance.taxon_rank = m.Property(
    f"{Instance} has taxon rank {String:taxon_rank}"
)
# Values: 'species' | 'genus' | 'family' | 'community' | 'abiotic'

# ---- Evidence: Observations linked to this Instance ----------------------

Observation.instance = m.Relationship(
    f"{Observation} is evidence for {Instance:instance}"
)

# ---- Provenance ----------------------------------------------------------

from .provenance import DataSource  # noqa: E402 — deferred to avoid cycle

Instance.source = m.Relationship(f"{Instance} from source {DataSource:source}")
