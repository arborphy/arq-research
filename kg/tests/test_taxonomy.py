import relationalai.semantics as rai

from kg.model import ARQModel


def test_taxon_genus(arq: ARQModel):
    result = rai.where(
        arq.Genus.id == 1000004,
        arq.Species.genus(arq.Genus),
    ).select(
        arq.Species.id,
        arq.Species.canonical_name,
        arq.Genus.id,
        arq.Genus.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (4, 4)
    assert result.iloc[0]["id"] == 1000005
    assert result.iloc[0]["canonicalname"] == "Pyrodictium occultum"
    assert result.iloc[0]["id2"] == 1000004
    assert result.iloc[0]["canonicalname2"] == "Pyrodictium"

def test_taxon_family(arq: ARQModel):
    result = rai.where(
        arq.Family.id == 3797,
        arq.Species.family(arq.Family),
    ).select(
        arq.Species.id,
        arq.Species.canonical_name,
        arq.Family.id,
        arq.Family.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (14, 4)
    assert result.iloc[0]["id"] == 1000005
    assert result.iloc[0]["canonicalname"] == "Pyrodictium occultum"
    assert result.iloc[0]["id2"] == 3797
    assert result.iloc[0]["canonicalname2"] == "Pyrodictiaceae"

    result = rai.where(
        arq.Family.id == 3797,
        arq.Genus.family(arq.Family),
    ).select(
        arq.Genus.id,
        arq.Genus.canonical_name,
        arq.Family.id,
        arq.Family.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (7, 4)
    assert result.iloc[0]["id"] == 1000004
    assert result.iloc[0]["canonicalname"] == "Pyrodictium"
    assert result.iloc[0]["id2"] == 3797
    assert result.iloc[0]["canonicalname2"] == "Pyrodictiaceae"

def test_taxon_order(arq: ARQModel):
    result = rai.where(
        arq.Order.id == 564,
        arq.Species.order(arq.Order),
    ).select(
        arq.Species.id,
        arq.Species.canonical_name,
        arq.Order.id,
        arq.Order.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (139, 4)
    assert result.iloc[0]["id"] == 1000003
    assert result.iloc[0]["canonicalname"] == "Caldisphaera lagunensis"
    assert result.iloc[0]["id2"] == 564
    assert result.iloc[0]["canonicalname2"] == "Sulfolobales"

    result = rai.where(
        arq.Order.id == 564,
        arq.Genus.order(arq.Order),
    ).select(
        arq.Genus.id,
        arq.Genus.canonical_name,
        arq.Order.id,
        arq.Order.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (66, 4)
    assert result.iloc[0]["id"] == 1000002
    assert result.iloc[0]["canonicalname"] == "Caldisphaera"
    assert result.iloc[0]["id2"] == 564
    assert result.iloc[0]["canonicalname2"] == "Sulfolobales"

    result = rai.where(
        arq.Order.id == 564,
        arq.Family.order(arq.Order),
    ).select(
        arq.Family.id,
        arq.Family.canonical_name,
        arq.Order.id,
        arq.Order.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (12, 4)
    assert result.iloc[0]["id"] == 3797
    assert result.iloc[0]["canonicalname"] == "Pyrodictiaceae"
    assert result.iloc[0]["id2"] == 564
    assert result.iloc[0]["canonicalname2"] == "Sulfolobales"

def test_taxon_class(arq: ARQModel):
    result = rai.where(
        arq.Class.id == 10705623,
        arq.Species.class_(arq.Class),
    ).select(
        arq.Species.id,
        arq.Species.canonical_name,
        arq.Class.id,
        arq.Class.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (191, 4)
    assert result.iloc[0]["id"] == 1000003
    assert result.iloc[0]["canonicalname"] == "Caldisphaera lagunensis"
    assert result.iloc[0]["id2"] == 10705623
    assert result.iloc[0]["canonicalname2"] == "Thermoproteia"

    result = rai.where(
        arq.Class.id == 10705623,
        arq.Genus.class_(arq.Class),
    ).select(
        arq.Genus.id,
        arq.Genus.canonical_name,
        arq.Class.id,
        arq.Class.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (86, 4)
    assert result.iloc[0]["id"] == 1000002
    assert result.iloc[0]["canonicalname"] == "Caldisphaera"
    assert result.iloc[0]["id2"] == 10705623
    assert result.iloc[0]["canonicalname2"] == "Thermoproteia"

    result = rai.where(
        arq.Class.id == 10705623,
        arq.Family.class_(arq.Class),
    ).select(
        arq.Family.id,
        arq.Family.canonical_name,
        arq.Class.id,
        arq.Class.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (25, 4)
    assert result.iloc[0]["id"] == 3797
    assert result.iloc[0]["canonicalname"] == "Pyrodictiaceae"
    assert result.iloc[0]["id2"] == 10705623
    assert result.iloc[0]["canonicalname2"] == "Thermoproteia"

    result = rai.where(
        arq.Class.id == 10705623,
        arq.Order.class_(arq.Class),
    ).select(
        arq.Order.id,
        arq.Order.canonical_name,
        arq.Class.id,
        arq.Class.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (10, 4)
    assert result.iloc[0]["id"] == 564
    assert result.iloc[0]["canonicalname"] == "Sulfolobales"
    assert result.iloc[0]["id2"] == 10705623
    assert result.iloc[0]["canonicalname2"] == "Thermoproteia"
