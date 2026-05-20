from kg.model import m
from relationalai.semantics import String  # used for osm_id, highway, surface
from .entity import Location
from .h3cell import H3Cell

Trail = m.Concept("Trail", extends=[Location])

Trail.osm_id = m.Property(f"{Trail} has osm id {String:osm_id}")
Trail.highway = m.Property(f"{Trail} has highway type {String:highway}")
Trail.surface = m.Property(f"{Trail} has surface {String:surface}")

Trail.h3_cells = m.Relationship(f"{Trail} passes through {H3Cell:h3_cells}")
