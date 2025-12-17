"""Registry of declarative entity specs.

Keeping this separate makes codegen and model wiring deterministic without
creating circular imports in `kg.model.__init__`.
"""

from kg.model.core.observation import ObservationSpec

ENTITY_SPECS = [
    ObservationSpec,
]
