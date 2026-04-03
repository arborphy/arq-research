"""Calendar module for Arborphy KG.

Concepts:
    Month        — calendar month (1–12) with name
    Season       — meteorological season with hemisphere awareness
    CalendarDate — a specific date with derived year / month / quarter / season

Derived relationships (rules):
    CalendarDate → Month        (by month number)
    CalendarDate → Season       (by month range, hemisphere-aware)
    Observation  → CalendarDate (via observation date)

Season naming convention: "{Season}_{hemisphere}" e.g. "Spring_north", "Winter_south".
Winter_north / Summer_south wrap across the year boundary (Dec–Jan–Feb).

Query functions:
    observations_by_season(season_name, hemisphere)
    observations_by_month(month_num)
    calendar_date_info(date_str)
    bloom_window_for_species(species_name)
"""

from relationalai.semantics import Date, Integer, String, define, where
from relationalai.semantics.std import datetime as dt

from kg.model import m
from kg.model.core.observations import Observation

# ---------------------------------------------------------------------------
# Concepts
# ---------------------------------------------------------------------------

Month = m.Concept("Month", identify_by={"number": Integer})
Month.name = m.Property(f"{Month} is named {String:name}")

Season = m.Concept("Season", identify_by={"name": String})
Season.hemisphere = m.Property(f"{Season} is in hemisphere {String:hemisphere}")
Season.start_month = m.Property(f"{Season} starts at month {Integer:start_month}")
Season.end_month = m.Property(f"{Season} ends at month {Integer:end_month}")

CalendarDate = m.Concept("CalendarDate", identify_by={"date": Date})
CalendarDate.year = m.Property(f"{CalendarDate} has year {Integer:year}")
CalendarDate.month_num = m.Property(f"{CalendarDate} has month number {Integer:month_num}")
CalendarDate.quarter = m.Property(f"{CalendarDate} has quarter {Integer:quarter}")
CalendarDate.month = m.Relationship(f"{CalendarDate} in {Month:month}")
CalendarDate.season = m.Relationship(f"{CalendarDate} in {Season:season}")

Observation.calendar_date = m.Relationship(
    f"{Observation} has calendar date {CalendarDate:calendar_date}"
)

# ---------------------------------------------------------------------------
# Seed: Months
# ---------------------------------------------------------------------------

_MONTH_NAMES = [
    (1, "January"),   (2, "February"),  (3, "March"),     (4, "April"),
    (5, "May"),       (6, "June"),      (7, "July"),       (8, "August"),
    (9, "September"), (10, "October"),  (11, "November"),  (12, "December"),
]

for _num, _label in _MONTH_NAMES:
    define(mo := Month.new(number=_num), mo.name(_label))

# ---------------------------------------------------------------------------
# Seed: Seasons (meteorological, hemisphere-aware)
# Winter_north / Summer_south span Dec–Jan–Feb; start/end are informational only.
# ---------------------------------------------------------------------------

_SEASON_SEED = [
    #  key               hemisphere  start  end
    ("Spring_north",   "north",      3,     5),
    ("Summer_north",   "north",      6,     8),
    ("Autumn_north",   "north",      9,    11),
    ("Winter_north",   "north",     12,     2),  # wraps
    ("Spring_south",   "south",      9,    11),
    ("Summer_south",   "south",     12,     2),  # wraps
    ("Autumn_south",   "south",      3,     5),
    ("Winter_south",   "south",      6,     8),
]

for _key, _hemi, _sm, _em in _SEASON_SEED:
    define(
        se := Season.new(name=_key),
        se.hemisphere(_hemi),
        se.start_month(_sm),
        se.end_month(_em),
    )

# ---------------------------------------------------------------------------
# Rules: CalendarDate properties derived from its date value
# ---------------------------------------------------------------------------

define(CalendarDate.year(dt.date.year(CalendarDate.date)))
define(CalendarDate.month_num(dt.date.month(CalendarDate.date)))
define(CalendarDate.quarter(dt.date.quarter(CalendarDate.date)))

define(CalendarDate.month(CalendarDate, Month.filter_by(number=CalendarDate.month_num)))

# ---------------------------------------------------------------------------
# Rules: Season assignment
# Non-wrapping ranges (Spring / Summer[NH] / Autumn / Winter[SH])
# ---------------------------------------------------------------------------

_SEASON_RANGES = [
    ("Spring_north",  3,  5),
    ("Summer_north",  6,  8),
    ("Autumn_north",  9, 11),
    ("Autumn_south",  3,  5),
    ("Winter_south",  6,  8),
    ("Spring_south",  9, 11),
]

for _key, _lo, _hi in _SEASON_RANGES:
    where(
        cd := CalendarDate.ref(),
        (cd.month_num >= _lo) & (cd.month_num <= _hi),
    ).define(cd.season(Season.filter_by(name=_key)))

# Wrapping seasons: Winter_north and Summer_south cover Dec, Jan, Feb
for _wrap_key in ("Winter_north", "Summer_south"):
    where(
        cd := CalendarDate.ref(),
        (cd.month_num == 12) | (cd.month_num <= 2),
    ).define(cd.season(Season.filter_by(name=_wrap_key)))

# ---------------------------------------------------------------------------
# Rules: Observation → CalendarDate
# ---------------------------------------------------------------------------

# Materialise a CalendarDate entity for every unique observation date
define(CalendarDate.new(date=Observation.date))

# Link each Observation to its CalendarDate
define(
    Observation.calendar_date(
        Observation, CalendarDate.filter_by(date=Observation.date)
    )
)

# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------


def observations_by_season(season_name: str, hemisphere: str = "north"):
    """Return observations with species name for a season + hemisphere.

    Args:
        season_name: "Spring", "Summer", "Autumn", or "Winter"
        hemisphere:  "north" (default) or "south"
    """
    from kg.model.core.taxonomy import Species

    key = f"{season_name.capitalize()}_{hemisphere}"
    obs = Observation.ref()
    cd = CalendarDate.ref()
    se = Season.ref()
    sp = Species.ref()

    return (
        where(
            obs.calendar_date(cd),
            cd.season(se),
            se.name == key,
            obs.species(sp),
        )
        .select(obs.inat_id, sp.name, cd.year, cd.month_num)
        .to_df()
    )


def observations_by_month(month_num: int):
    """Return observations (with species name and year) for a calendar month (1–12)."""
    from kg.model.core.taxonomy import Species

    obs = Observation.ref()
    cd = CalendarDate.ref()
    sp = Species.ref()

    return (
        where(
            obs.calendar_date(cd),
            cd.month_num == month_num,
            obs.species(sp),
        )
        .select(obs.inat_id, sp.name, cd.year)
        .to_df()
    )


def calendar_date_info(date_str: str):
    """Return year, month number, quarter, month name, and season for an ISO date.

    Args:
        date_str: ISO 8601 date string e.g. "2024-05-15"
    """
    import datetime as _dt

    d = _dt.date.fromisoformat(date_str)
    cd = CalendarDate.filter_by(date=d)
    mo = Month.ref()
    se = Season.ref()

    return (
        where(cd.month(mo), cd.season(se))
        .select(cd.year, cd.month_num, cd.quarter, mo.name, se.name)
        .to_df()
    )


def bloom_window_for_species(species_name: str):
    """Return the distinct seasons in which a species has been observed.

    Useful for inferring bloom windows from iNaturalist observation data.
    """
    from kg.model.core.taxonomy import Species

    sp = Species.ref()
    obs = Observation.ref()
    cd = CalendarDate.ref()
    se = Season.ref()

    return (
        where(
            sp.name == species_name,
            obs.species(sp),
            obs.calendar_date(cd),
            cd.season(se),
        )
        .select(se.name, se.hemisphere, cd.month_num)
        .to_df()
    )
