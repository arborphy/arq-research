from kg.model import m
from relationalai.semantics import String
from .entity import Entity

DataSource = m.Concept("DataSource", extends=[Entity])

# Properties
DataSource.as_of_date = m.Property(f"{DataSource} as of {String:as_of_date}")
