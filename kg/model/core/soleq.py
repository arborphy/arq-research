import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

# Sourced from dbt/models/staging/soleq.sql


def define_solstice_equinox(m: rai.Model, source: Table):
    """Define solstice and equinox concepts for astronomical calendar events.

    Source: https://www.astropixels.com/ephemeris/soleq2001.html

    Earth's rotational axis is tilted about 23.5° from the perpendicular with
    respect to Earth's orbit around the Sun. As a result, the amount that Earth's
    axis tilts towards or away from the Sun varies during the year.

    Summer Solstice occurs at the moment the tilt of Earth's axis towards the Sun
    is at a maximum. The Sun then appears at its highest elevation at noon for
    observers in the Northern Hemisphere. Summer Solstice marks the longest day
    and shortest night of the year in the Northern Hemisphere.

    Winter Solstice occurs at the moment the tilt of Earth's axis away the Sun is
    at a maximum. The Sun then appears at its lowest elevation at noon for
    observers in the Northern Hemisphere. Winter Solstice marks the shortest day
    and longest night of the year in the Northern Hemisphere.

    There are two times a year when Earth's axis neither tilts towards or away
    from the Sun. In fact, the axis then perpendicular to the Sun resulting in a
    nearly equal length of day and night at all latitudes. These instances are
    referred to as equinoxes (derived from two Latin words: aequus (equal) and
    nox (night)). The two equinoxes are nearly six month apart and are known as
    the Spring Equinox and Fall Equinox.

    [AG] In the astropixels data source, the framing of Spring, Summer, etc.
    assumes Northern Hemisphere. Our model endeavors to capture Solstice's and
    Equinox's relationships to the Northern and Southern Hemispheres.
    """
    m.Solstice = m.Concept("Solstice", extends=[m.CalendarEvent])
    m.Solstice.summer = m.Property("{Solstice} is in the summer for {Hemisphere}")
    m.Solstice.winter = m.Property("{Solstice} is in the winter for {Hemisphere}")
    def_solstice = lambda col, summer, winter: rai.define(
        s := m.Solstice.new(datetime=col),
        s.summer(summer),
        s.winter(winter),
    )
    def_solstice(source.summer_solstice, m.HemisphereNorth, m.HemisphereSouth)
    def_solstice(source.winter_solstice, m.HemisphereSouth, m.HemisphereNorth)

    m.Equinox = m.Concept("Equinox", extends=[m.CalendarEvent])
    m.Equinox.spring = m.Property("{Equinox} is in the spring for {Hemisphere}")
    m.Equinox.fall = m.Property("{Equinox} is in the fall for {Hemisphere}")
    def_equinox = lambda col, spring, fall: rai.define(
        e := m.Equinox.new(datetime=col),
        e.spring(spring),
        e.fall(fall),
    )
    def_equinox(source.spring_equinox, m.HemisphereNorth, m.HemisphereSouth)
    def_equinox(source.fall_equinox, m.HemisphereSouth, m.HemisphereNorth)
