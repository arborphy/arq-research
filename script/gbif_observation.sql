-- # https://api.gbif.org/v1/occurrence/download/request/0048885-250525065834625.zip


use role team_arq;
use database team_arq;
use schema source;

create table if not exists gbif_observation
(
    gbifID int,
    datasetKey string,
    occurrenceID string,
    kingdom string,
    phylum string,
    class string,
    "order" string,
    family string,
    genus string,
    species string,
    infraspecificEpithet string,
    taxonRank string,
    scientificName string,
    verbatimScientificName string,
    verbatimScientificNameAuthorship string,
    countryCode string,
    locality string,
    stateProvince string,
    occurrenceStatus string,
    individualCount int, -- no values
    publishingOrgKey string,
    decimalLatitude float,
    decimalLongitude float,
    coordinateUncertaintyInMeters float,
    coordinatePrecision float, -- no values
    elevation float, -- no values
    elevationAccuracy float, -- no values
    depth float, -- no values
    depthAccuracy float, -- no values
    eventDate timestamp_ntz,
    day int,
    month int,
    year int,
    taxonKey int,
    speciesKey int,
    basisOfRecord string,
    institutionCode string,
    collectionCode string,
    catalogNumber int,
    recordNumber int, --no values
    identifiedBy string,
    dateIdentified timestamp_ntz,
    license string,
    rightsHolder string,
    recordedBy string,
    typeStatus string, -- no values
    establishmentMeans string, -- no values
    lastInterpreted timestamp_tz,
    mediaType string,
    issue string
);

PUT file://<% path %> @gbif/observation parallel=32;

COPY INTO gbif_observation
FROM @gbif/observation
FILE_FORMAT = (
    TYPE = CSV,
    FIELD_DELIMITER = '\t',
    SKIP_HEADER = 1,
    ESCAPE_UNENCLOSED_FIELD = None -- todo: lastInterpreted is missing / malformed in some cases
);

select count(*) from gbif_observation;
-- 23279065
select count(gbifID) from gbif_observation;
-- 23279065
select count(distinct gbifID) from gbif_observation;
-- 23279065
