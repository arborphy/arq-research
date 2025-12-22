import relationalai.semantics as rai

from kg.model import ARQModel


def test_taxon_genus(arq: ARQModel):
    result = rai.where(
        arq.TaxonGenus.id == 1000004,
        arq.Species.genus(arq.TaxonGenus),
    ).select(
        arq.Species.name,
        arq.TaxonGenus.id,
        arq.TaxonGenus.canonical_name,
    ).to_df()
    print(result)
    assert result.shape[1] == 3
    assert len(result) > 0
    assert set(result["id"].astype("Int64").unique()) == {1000004}
    assert set(result["canonicalname"].unique()) == {"Pyrodictium"}
    assert "Pyrodictium occultum" in set(result["name"])

def test_taxon_family(arq: ARQModel):
    result = rai.where(
        arq.TaxonFamily.id == 3797,
        arq.Species.family(arq.TaxonFamily),
    ).select(
        arq.Species.name,
        arq.TaxonFamily.id,
        arq.TaxonFamily.canonical_name,
    ).to_df()
    print(result)
    assert result.shape[1] == 3
    assert len(result) > 0
    assert set(result["id"].astype("Int64").unique()) == {3797}
    assert set(result["canonicalname"].unique()) == {"Pyrodictiaceae"}
    assert "Pyrodictium occultum" in set(result["name"])

    result = rai.where(
        arq.TaxonFamily.id == 3797,
        arq.TaxonGenus.family(arq.TaxonFamily),
    ).select(
        arq.TaxonGenus.id,
        arq.TaxonGenus.canonical_name,
        arq.TaxonFamily.id,
        arq.TaxonFamily.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (7, 4)
    assert ((result["id"].astype("Int64") == 1000004) & (result["canonicalname"] == "Pyrodictium")).any()
    assert ((result["id2"].astype("Int64") == 3797) & (result["canonicalname2"] == "Pyrodictiaceae")).any()

def test_taxon_order(arq: ARQModel):
    result = rai.where(
        arq.TaxonOrder.id == 564,
        arq.Species.order(arq.TaxonOrder),
    ).select(
        arq.Species.name,
        arq.TaxonOrder.id,
        arq.TaxonOrder.canonical_name,
    ).to_df()
    print(result)
    assert result.shape[1] == 3
    assert len(result) > 0
    assert set(result["id"].astype("Int64").unique()) == {564}
    assert set(result["canonicalname"].unique()) == {"Sulfolobales"}
    assert "Caldisphaera lagunensis" in set(result["name"])

    result = rai.where(
        arq.TaxonOrder.id == 564,
        arq.TaxonGenus.order(arq.TaxonOrder),
    ).select(
        arq.TaxonGenus.id,
        arq.TaxonGenus.canonical_name,
        arq.TaxonOrder.id,
        arq.TaxonOrder.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (66, 4)
    assert ((result["id"].astype("Int64") == 1000002) & (result["canonicalname"] == "Caldisphaera")).any()
    assert ((result["id2"].astype("Int64") == 564) & (result["canonicalname2"] == "Sulfolobales")).any()

    result = rai.where(
        arq.TaxonOrder.id == 564,
        arq.TaxonFamily.order(arq.TaxonOrder),
    ).select(
        arq.TaxonFamily.id,
        arq.TaxonFamily.canonical_name,
        arq.TaxonOrder.id,
        arq.TaxonOrder.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (12, 4)
    assert ((result["id"].astype("Int64") == 3797) & (result["canonicalname"] == "Pyrodictiaceae")).any()
    assert ((result["id2"].astype("Int64") == 564) & (result["canonicalname2"] == "Sulfolobales")).any()

def test_taxon_class(arq: ARQModel):
    result = rai.where(
        arq.TaxonClass.id == 10705623,
        arq.Species.class_(arq.TaxonClass),
    ).select(
        arq.Species.name,
        arq.TaxonClass.id,
        arq.TaxonClass.canonical_name,
    ).to_df()
    print(result)
    assert result.shape[1] == 3
    assert len(result) > 0
    assert set(result["id"].astype("Int64").unique()) == {10705623}
    assert set(result["canonicalname"].unique()) == {"Thermoproteia"}
    assert "Caldisphaera lagunensis" in set(result["name"])

    result = rai.where(
        arq.TaxonClass.id == 10705623,
        arq.TaxonGenus.class_(arq.TaxonClass),
    ).select(
        arq.TaxonGenus.id,
        arq.TaxonGenus.canonical_name,
        arq.TaxonClass.id,
        arq.TaxonClass.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (86, 4)
    assert ((result["id"].astype("Int64") == 1000002) & (result["canonicalname"] == "Caldisphaera")).any()
    assert ((result["id2"].astype("Int64") == 10705623) & (result["canonicalname2"] == "Thermoproteia")).any()

    result = rai.where(
        arq.TaxonClass.id == 10705623,
        arq.TaxonFamily.class_(arq.TaxonClass),
    ).select(
        arq.TaxonFamily.id,
        arq.TaxonFamily.canonical_name,
        arq.TaxonClass.id,
        arq.TaxonClass.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (25, 4)
    assert ((result["id"].astype("Int64") == 3797) & (result["canonicalname"] == "Pyrodictiaceae")).any()
    assert ((result["id2"].astype("Int64") == 10705623) & (result["canonicalname2"] == "Thermoproteia")).any()

    result = rai.where(
        arq.TaxonClass.id == 10705623,
        arq.TaxonOrder.class_(arq.TaxonClass),
    ).select(
        arq.TaxonOrder.id,
        arq.TaxonOrder.canonical_name,
        arq.TaxonClass.id,
        arq.TaxonClass.canonical_name,
    ).to_df()
    print(result)
    assert result.shape == (10, 4)
    assert ((result["id"].astype("Int64") == 564) & (result["canonicalname"] == "Sulfolobales")).any()
    assert ((result["id2"].astype("Int64") == 10705623) & (result["canonicalname2"] == "Thermoproteia")).any()
