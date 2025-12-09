import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

# Sourced from dbt/models/staging/observation.sql


def define_observation(m: rai.Model, source: Table):
    """Define the Observation concept representing GBIF plant observation records.

    An Observation represents a documented occurrence of a plant species at a specific
    location and time. It includes taxonomic identification, spatial coordinates,
    temporal information, and observation metadata.
    """

    # Define ID and main concept
    m.ObservationId = m.Concept("ObservationId", extends=[rai.Integer])
    m.Observation = m.Concept("Observation", identify_by={"id": m.ObservationId})

    # Define value concepts for observation attributes
    m.EventDateTime = m.Concept("EventDateTime", extends=[rai.DateTime])
    m.BasisOfRecord = m.Concept("BasisOfRecord", extends=[rai.String])
    m.CountryCode = m.Concept("CountryCode", extends=[rai.String])
    m.StateProvince = m.Concept("StateProvince", extends=[rai.String])

    # Define properties
    m.Observation.event_datetime = m.Property("{Observation} occurred on {EventDateTime}")
    m.Observation.day_of_year = m.Property("{Observation} occurred on day {DayOfYear}")
    m.Observation.year = m.Property("{Observation} occurred in year {Year}")
    m.Observation.basis_of_record = m.Property("{Observation} has basis of record {BasisOfRecord}")
    m.Observation.country_code = m.Property("{Observation} was recorded in country {CountryCode}")
    m.Observation.state_province = m.Property("{Observation} was recorded in state/province {StateProvince}")
    m.Observation.latitude = m.Property("{Observation} has latitude {Latitude}")
    m.Observation.longitude = m.Property("{Observation} has longitude {Longitude}")

    # H3 spatial index properties
    m.Observation.h3_cell_6 = m.Property("{Observation} is in H3 cell (~36km^2) {H3Cell}")
    m.Observation.h3_cell_7 = m.Property("{Observation} is in H3 cell (~5km^2) {H3Cell}")
    m.Observation.h3_cell_8 = m.Property("{Observation} is in H3 cell (~0.7km^2) {H3Cell}")
    m.Observation.h3_cell_9 = m.Property("{Observation} is in H3 cell (~0.1km^2) {H3Cell}")
    m.Observation.h3_cell_10 = m.Property("{Observation} is in H3 cell (~0.01km^2) {H3Cell}")

    # Relationships
    m.Observation.classification = m.Property("{Observation} is classified as {Taxon}")

    # Bind source data to concepts
    rai.define(m.Observation.new(id=source.GBIFID))
    obs = rai.where(m.Observation.id == source.GBIFID)
    obs.define(m.Observation.event_datetime(source.EVENTDATE))
    obs.define(m.Observation.day_of_year(source.DAYOFYEAR))
    obs.define(m.Observation.year(source.YEAR))
    obs.define(m.Observation.basis_of_record(source.BASISOFRECORD))
    obs.define(m.Observation.country_code(source.COUNTRYCODE))
    obs.define(m.Observation.state_province(source.STATEPROVINCE))
    obs.define(m.Observation.latitude(source.LAT))
    obs.define(m.Observation.longitude(source.LON))
    obs.define(m.Observation.h3_cell_6(source.H3_CELL_6))
    obs.define(m.Observation.h3_cell_7(source.H3_CELL_7))
    obs.define(m.Observation.h3_cell_8(source.H3_CELL_8))
    obs.define(m.Observation.h3_cell_9(source.H3_CELL_9))
    obs.define(m.Observation.h3_cell_10(source.H3_CELL_10))
    obs.define(
        m.Observation.classification(m.Taxon.filter_by(id=source.TAXONKEY))
    )
