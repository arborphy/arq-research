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
