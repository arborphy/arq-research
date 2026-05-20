"""Named place concepts — Park, City, State, Country.

These are subtypes of Location and participate in the located_in hierarchy,
allowing within(obs, country) to traverse: obs → park → state → country.

The `name` property is inherited from Entity (via GeographicArea --|> Entity).
"""
from relationalai.semantics import Float

from kg.model import m
from kg.model.core.entity import Location

Coordinate = m.Concept("Coordinate", extends=[Location])
Coordinate.lat = m.Property(f"{Coordinate} at latitude {Float:lat}")
Coordinate.lon = m.Property(f"{Coordinate} at longitude {Float:lon}")

Park = m.Concept("Park", extends=[Location])
City = m.Concept("City", extends=[Location])
State = m.Concept("State", extends=[Location])
Country = m.Concept("Country", extends=[Location])
