from kg.model import m
from relationalai.semantics import Bool, Date, Float, Integer, String
from .entity import Entity
from .taxonomy import Species
from .environment import EnvironmentValue

Observation = m.Concept("Observation", extends=[Entity])
GeographicArea = m.Concept("GeographicArea", extends=[Entity])

# Properties
Observation.inat_id = m.Property(f"{Observation} has iNaturalist id {String:inat_id}")
Observation.uuid = m.Property(f"{Observation} has uuid {String:uuid}")
Observation.date = m.Property(f"{Observation} observed on {Date:date}")
Observation.time_observed_at = m.Property(f"{Observation} observed at time {String:time_observed_at}")
Observation.latitude = m.Property(f"{Observation} at latitude {Float:latitude}")
Observation.longitude = m.Property(f"{Observation} at longitude {Float:longitude}")
Observation.positional_accuracy = m.Property(f"{Observation} has positional accuracy {Float:positional_accuracy}")
Observation.coordinates_obscured = m.Property(f"{Observation} has coordinates obscured {Bool:coordinates_obscured}")
Observation.image_url = m.Property(f"{Observation} has image {String:image_url}")
Observation.sound_url = m.Property(f"{Observation} has sound {String:sound_url}")
Observation.url = m.Property(f"{Observation} has url {String:url}")
Observation.quality_grade = m.Property(f"{Observation} has quality grade {String:quality_grade}")
Observation.num_identification_agreements = m.Property(f"{Observation} has {Integer:num_identification_agreements} identification agreements")
Observation.num_identification_disagreements = m.Property(f"{Observation} has {Integer:num_identification_disagreements} identification disagreements")
Observation.captive_cultivated = m.Property(f"{Observation} is captive or cultivated {Bool:captive_cultivated}")
Observation.place_guess = m.Property(f"{Observation} place guess is {String:place_guess}")
Observation.species_guess = m.Property(f"{Observation} species guess is {String:species_guess}")
Observation.description = m.Property(f"{Observation} has description {String:description}")
Observation.license = m.Property(f"{Observation} has license {String:license}")
GeographicArea.type = m.Property(f"{GeographicArea} has type {String:type}")

# Relationships
Observation.co_occurs_with = m.Relationship(f"{Observation} co-occurs with {Observation:co_occurs_with}")
Observation.species = m.Relationship(f"{Observation} of species {Species:species}")
Observation.area = m.Relationship(f"{Observation} located in {GeographicArea:area}")
GeographicArea.environment = m.Relationship(f"{GeographicArea} has environment {EnvironmentValue:environment}")
