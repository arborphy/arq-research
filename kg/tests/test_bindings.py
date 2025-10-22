import relationalai.semantics as rai
from pandas import Timestamp

from kg.model import ARQModel


# assumes TEAM_ARQ.PUBLIC dataset produced by `dbt build`

def test_taxon_bindings(arq: ARQModel):
    """Test that Taxon properties are correctly bound to source data."""
    result = rai.select(
        rai.count(arq.Taxon),
    ).to_df()

    print(result)
    assert result.shape == (1, 1)
    assert result.iloc[0]["v"] == 7746724

    result = rai.where(arq.Taxon.id == 8103240).select(
        arq.Taxon.id,
        arq.Taxon.scientific_name,
        arq.Taxon.canonical_name,
        arq.Taxon.rank,
    ).to_df()
    print(result)
    print(result.iloc[0])
    assert result.shape == (1, 4)
    assert result.iloc[0]["id"] == 8103240
    assert result.iloc[0]["scientificname"] == "Vaccinium angulatum J.J.Sm."
    assert result.iloc[0]["canonicalname"] == "Vaccinium angulatum"
    assert result.iloc[0]["taxonrank"] == "species"

def test_observation_bindings(arq: ARQModel):
    """
    Test that Observation properties are correctly bound to source data.
    Assumes OBSERVATION_10k table.
    """
    result = rai.select(
        rai.count(arq.Observation),
    ).to_df()

    print(result)
    assert result.shape == (1, 1)
    assert result.iloc[0]["v"] == 10000

    result = rai.where(arq.Observation.id == 5176335106).select(
        arq.Observation.id,
        arq.Observation.classification.canonical_name,
        arq.Observation.event_datetime,
        arq.Observation.day_of_year,
        arq.Observation.year,
        arq.Observation.basis_of_record,
        arq.Observation.country_code,
        arq.Observation.state_province,
        arq.Observation.latitude,
        arq.Observation.longitude,
        arq.Observation.h3_cell_6,
        arq.Observation.h3_cell_7,
        arq.Observation.h3_cell_8,
        arq.Observation.h3_cell_9,
        arq.Observation.h3_cell_10,
    ).to_df()
    print(result)
    assert result.shape == (1, 15)
    assert result.iloc[0]["id"] == 5176335106
    assert result.iloc[0]["canonicalname"] == "Kalmia microphylla"
    assert result.iloc[0]["eventdatetime"] == Timestamp("2025-06-02 11:58:33")
    assert result.iloc[0]["dayofyear"] == 153
    assert result.iloc[0]["year"] == 2025
    assert result.iloc[0]["basisofrecord"] == "HUMAN_OBSERVATION"
    assert result.iloc[0]["countrycode"] == "US"
    assert result.iloc[0]["stateprovince"] == "Alaska"
    assert round(result.iloc[0]["latitude"], 6) == 58.648528
    assert round(result.iloc[0]["longitude"], 6) == -134.935024
    assert result.iloc[0]["h3cell"] == 603826595454517247
    assert result.iloc[0]["h3cell2"] == 608330195065110527
    assert result.iloc[0]["h3cell3"] == 612833794677800959
    assert result.iloc[0]["h3cell4"] == 617337394304909311
    assert result.iloc[0]["h3cell5"] == 621840993932247039





