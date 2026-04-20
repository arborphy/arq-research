from kg.model import m
from relationalai.semantics import String

DataSource = m.Concept("DataSource", identify_by={"name": String})
DataSource.as_of_date = m.Property(f"{DataSource} as of date {String:as_of_date}")
DataSource.description = m.Property(f"{DataSource} has description {String:description}")
