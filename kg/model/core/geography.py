import relationalai.semantics as rai

# Core geographic concepts


def define_geography(m: rai.Model):
    """Define core geographic concepts.

    Geographic concepts include hemispheres, coordinates, and spatial references
    used across the knowledge graph for location-based analysis.
    """
    # Hemispheres
    m.Hemisphere = m.Concept("Hemisphere", identify_by={"id": rai.String})
    rai.define(north := m.Hemisphere.new(id="north"))
    rai.define(south := m.Hemisphere.new(id="south"))
    rai.define(east := m.Hemisphere.new(id="east"))
    rai.define(west := m.Hemisphere.new(id="west"))

    # Store references for use by other modules
    m.HemisphereNorth = north
    m.HemisphereSouth = south
    m.HemisphereEast = east
    m.HemisphereWest = west

    m.Latitude = m.Concept("Latitude", extends=[rai.Float])
    m.Latitude.hemisphere = m.Property("{Latitude} is within {Hemisphere}")
    rai.define(m.Latitude.hemisphere(north)).where(m.Latitude >= 0)
    rai.define(m.Latitude.hemisphere(south)).where(m.Latitude < 0)

    m.Longitude = m.Concept("Longitude", extends=[rai.Float])
    m.Longitude.hemisphere = m.Property("{Longitude} is within {Hemisphere}")
    rai.define(m.Longitude.hemisphere(east)).where(m.Longitude >= 0)
    rai.define(m.Longitude.hemisphere(west)).where(m.Longitude < 0)

    m.H3Cell = m.Concept("H3Cell", extends=[rai.Integer])

