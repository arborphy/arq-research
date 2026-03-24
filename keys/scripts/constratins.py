


# Uniquness Constraint:
# Ensure that each species has a unique identifier (e.g., 'species_id').
m.unique(Species.species_id)

# Existence Constraint:
# Ensure that every species has a 'name' property.
m.mandatory(Species.name)

# Integrity Constraint:
# Scope the requirement to Species where the plant_type is 4 or 5.
# This ensures that for these specific types, an 'is_woody' property must exist and be True.
m.where(Species).where((Species.plant_type == 4) | (Species.plant_type == 5)).require(
    Species.is_woody == True
)