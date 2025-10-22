
use role team_arq;
use database team_arq;
use schema source;

create table if not exists gbif_description (
    taxonID int,
    type string,
    languange string,
    description string,
    source string,
    creator string,
    contributor string,
    license string
);

PUT file://<% path %>/Description.tsv @team_arq.source.gbif/backbone/description parallel=32;

COPY INTO gbif_description
FROM @team_arq.source.gbif/backbone/description
FILE_FORMAT = (
    TYPE = CSV,
    FIELD_DELIMITER = '\t',
    SKIP_HEADER = 1,
    ESCAPE_UNENCLOSED_FIELD = None
);

select * from gbif_description limit 1;
select count(*) from gbif_description; -- todo 1755793 rows in SF vs 1751095 rows in pandas
select
    type,
    count(*) c
from gbif_description
group by type
order by c desc;
select
    languange,
    count(*) c
from gbif_description
group by languange
order by c desc;

create table if not exists gbif_distribution (
    taxonID int,
    locationID string,
    locality string,
    country string,
    countryCode string,
    locationRemarks string,
    establishmentMeans string,
    lifeStage string,
    occurrenceStatus string,
    threatStatus string,
    source string
);

PUT file://<% path %>/Distribution.tsv @team_arq.source.gbif/backbone/distribution parallel=32;

COPY INTO gbif_distribution
FROM @team_arq.source.gbif/backbone/distribution
FILE_FORMAT = (
    TYPE = CSV,
    FIELD_DELIMITER = '\t',
    SKIP_HEADER = 1,
    ESCAPE_UNENCLOSED_FIELD = None
);

select * from gbif_distribution limit 1;
select count(*) from gbif_distribution;
select
    source,
    count(*) c
from gbif_distribution
group by source
order by c desc
limit 10;
select
    country,
    count(*) c
from gbif_distribution
group by country
order by c desc
limit 10;

create table if not exists gbif_multimedia (
    taxonID int,
    identifier string,
    "references" string,
    title string,
    description string,
    license string,
    creator string,
    created string,
    contributor string,
    publisher string,
    rightsHolder string,
    source string
);

PUT file://<% path %>/Multimedia.tsv @team_arq.source.gbif/backbone/multimedia parallel=32;

COPY INTO gbif_multimedia
FROM @team_arq.source.gbif/backbone/multimedia
FILE_FORMAT = (
    TYPE = CSV,
    FIELD_DELIMITER = '\t',
    SKIP_HEADER = 1,
    ESCAPE_UNENCLOSED_FIELD = None
);

select * from gbif_multimedia limit 1;
select count(*) from gbif_multimedia;
select
    publisher,
    count(*) c
from gbif_multimedia
group by publisher
order by c desc
limit 10;
select
    source,
    count(*) c
from gbif_multimedia
group by source
order by c desc
limit 10;

create table if not exists gbif_reference (
    taxonID int,
    bibliographicCitation string,
    identifier string,
    "references" string,
    source string
);

PUT file://<% path %>/Reference.tsv @team_arq.source.gbif/backbone/reference parallel=32;

COPY INTO gbif_reference
FROM @team_arq.source.gbif/backbone/reference
FILE_FORMAT = (
    TYPE = CSV,
    FIELD_DELIMITER = '\t',
    SKIP_HEADER = 1,
    ESCAPE_UNENCLOSED_FIELD = None
);
select * from gbif_reference limit 1;
select count(*) from gbif_reference;
select
    source,
    count(*) c
from gbif_reference
group by source
order by c desc
limit 10;


create table if not exists gbif_taxon (
    taxonID int,
    datasetID string,
    parentNameUsageID int,
    acceptedNameUsageID int,
    originalNameUsageID int,
    scientificName string,
    scientificNameAuthorship string,
    canonicalName string,
    genericName string,
    specificEpithet string,
    infraspecificEpithet string,
    taxonRank string,
    nameAccordingTo string,
    namePublishedIn string,
    taxonomicStatus string,
    nomenclaturalStatus string,
    taxonRemarks string,
    kingdom string,
    phylum string,
    class string,
    "order" string,
    family string,
    genus string
);

PUT file://<% path %>/Taxon.tsv @team_arq.source.gbif/backbone/taxon parallel=32;

COPY INTO gbif_taxon
FROM @team_arq.source.gbif/backbone/taxon
FILE_FORMAT = (
    TYPE = CSV,
    FIELD_DELIMITER = '\t',
    SKIP_HEADER = 1,
    ESCAPE_UNENCLOSED_FIELD = None
)
ON_ERROR = CONTINUE
RETURN_FAILED_ONLY = TRUE;

select * from gbif_taxon limit 1;
select count(*) from gbif_taxon; -- todo 7746724 SF vs 7694320 pandas
select
    datasetID,
    count(*) c
from gbif_taxon
group by datasetID
order by c desc
limit 10;
select
    kingdom,
    count(*) c
from gbif_taxon
group by kingdom
order by c desc
limit 10;

-- TypesAndSpecimen (42261)
-- taxonID                                                          1033506
-- typeDesignationType                                                  NaN
-- typeDesignatedBy                                               Grouvelle
-- scientificName                                       Phanocerus congener
-- taxonRank                                                            NaN
-- source                 Listado de las especies de Elmidae (Coleoptera...
create table if not exists gbif_types_and_specimen (
    taxonID int,
    typeDesignationType string,
    typeDesignatedBy string,
    scientificName string,
    taxonRank string,
    source string
);

PUT file://<% path %>/TypesAndSpecimen.tsv @team_arq.source.gbif/backbone/typesandspecimen parallel=32;

COPY INTO gbif_types_and_specimen
FROM @team_arq.source.gbif/backbone/typesandspecimen
FILE_FORMAT = (
    TYPE = CSV,
    FIELD_DELIMITER = '\t',
    SKIP_HEADER = 1,
    ESCAPE_UNENCLOSED_FIELD = None
)
ON_ERROR = CONTINUE
RETURN_FAILED_ONLY = TRUE;

select * from gbif_types_and_specimen limit 1;
select count(*) from gbif_types_and_specimen;
select
    source,
    count(*) c
from gbif_types_and_specimen
group by source
order by c desc
limit 10;

create table if not exists gbif_vernacular_name (
    taxonID int,
    vernacularName string,
    language string,
    country string,
    countryCode string,
    sex string,
    lifeStage string,
    source string
);

PUT file://<% path %>/VernacularName.tsv @team_arq.source.gbif/backbone/vernacular_name parallel=32;

COPY INTO gbif_vernacular_name
FROM @team_arq.source.gbif/backbone/vernacular_name
FILE_FORMAT = (
    TYPE = CSV,
    FIELD_DELIMITER = '\t',
    SKIP_HEADER = 1,
    ESCAPE_UNENCLOSED_FIELD = None
)
ON_ERROR = CONTINUE
RETURN_FAILED_ONLY = TRUE;

select * from gbif_vernacular_name limit 1;
select count(*) from gbif_vernacular_name;
select
    source,
    count(*) c
from gbif_vernacular_name
group by source
order by c desc
limit 10;