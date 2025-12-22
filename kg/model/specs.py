"""Registry of declarative entity specs.

Keeping this separate makes codegen and model wiring deterministic without
creating circular imports in `kg.model.__init__`.
"""

from kg.model.core.observation import ObservationSpec
from kg.model.core.plant import PlantSpec
from kg.model.core.taxon import TaxonSpec
from kg.model.core.trait import TraitSpec

ENTITY_SPECS = [
    TaxonSpec,
    ObservationSpec,
    PlantSpec,
    TraitSpec,
]
