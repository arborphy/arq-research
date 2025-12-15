import relationalai.semantics as rai
import relationalai.semantics.std as std

# Core temporal concepts used across multiple models


def define_calendar(m: rai.Model):
    """Define core calendar and temporal concepts.

    These concepts are used by observations, astronomical events, and other
    time-based entities in the knowledge graph.
    """
    m.Year = m.Concept("Year", extends=[rai.Integer])
    m.DayOfYear = m.Concept("DayOfYear", extends=[rai.Integer])

    m.CalendarEvent = m.Concept("CalendarEvent", identify_by={
        "datetime": rai.DateTime,
    })
    m.CalendarEvent.year = m.Property("{CalendarEvent} occurs within {Year}")
    m.CalendarEvent.day_of_year = m.Property("{CalendarEvent} occurs on {DayOfYear}")

    dt = std.datetime.datetime
    rai.define(m.CalendarEvent.year(m.Year(dt.year(m.CalendarEvent.datetime))))
    rai.define(m.CalendarEvent.day_of_year(m.DayOfYear(dt.dayofyear(m.CalendarEvent.datetime))))
