import relationalai.semantics as rai

# Derived relationships for observations


def define_derived_observation(m: rai.Model):
    """Define derived relationships for observations.

    Includes geographic relationships derived from observation coordinates,
    such as hemisphere assignments based on latitude and longitude.
    """
    # Derived relationship: hemisphere based on latitude and longitude
    m.Observation.hemisphere = m.Relationship("{Observation} is in {Hemisphere}")  # populated in derived/observation.py
    rai.define(
        m.Observation.hemisphere(m.Observation.latitude.hemisphere)
    )
    rai.define(
        m.Observation.hemisphere(m.Observation.longitude.hemisphere)
    )

    # Derived relationship: visible traits implied by the matched species
    m.Observation.visible_trait = m.Relationship("{Observation} has visible trait {Trait}")
    rai.define(
        m.Observation.visible_trait(m.Observation.species.trait)
    )
