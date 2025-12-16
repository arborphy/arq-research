import relationalai.semantics as rai

from kg.model import ARQModel


def _values(df, col: str):
    return [v for v in df[col].tolist() if v is not None]


def _contains(df, col: str, value) -> bool:
    return value in set(_values(df, col))


def _unique_equals(df, col: str, value) -> bool:
    vals = [v for v in _values(df, col) if v == v]
    return set(vals) == {value}


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
    assert result.shape[1] == 4
    assert _contains(result, "id", 1000005)
    assert _contains(result, "canonicalname", "Pyrodictium occultum")
    assert _unique_equals(result, "id2", 1000004)
    assert _unique_equals(result, "canonicalname2", "Pyrodictium")

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
    assert result.shape[1] == 4
    assert _contains(result, "id", 1000005)
    assert _contains(result, "canonicalname", "Pyrodictium occultum")
    assert _unique_equals(result, "id2", 3797)
    assert _unique_equals(result, "canonicalname2", "Pyrodictiaceae")

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
    assert result.shape[1] == 4
    assert _contains(result, "id", 1000004)
    assert _contains(result, "canonicalname", "Pyrodictium")
    assert _unique_equals(result, "id2", 3797)
    assert _unique_equals(result, "canonicalname2", "Pyrodictiaceae")

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
    assert result.shape[1] == 4
    assert _contains(result, "id", 1000003)
    assert _contains(result, "canonicalname", "Caldisphaera lagunensis")
    assert _unique_equals(result, "id2", 564)
    assert _unique_equals(result, "canonicalname2", "Sulfolobales")

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
    assert result.shape[1] == 4
    assert _contains(result, "id", 1000002)
    assert _contains(result, "canonicalname", "Caldisphaera")
    assert _unique_equals(result, "id2", 564)
    assert _unique_equals(result, "canonicalname2", "Sulfolobales")

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
    assert result.shape[1] == 4
    assert _contains(result, "id", 3797)
    assert _contains(result, "canonicalname", "Pyrodictiaceae")
    assert _unique_equals(result, "id2", 564)
    assert _unique_equals(result, "canonicalname2", "Sulfolobales")

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
    assert result.shape[1] == 4
    assert _contains(result, "id", 1000003)
    assert _contains(result, "canonicalname", "Caldisphaera lagunensis")
    assert _unique_equals(result, "id2", 10705623)
    assert _unique_equals(result, "canonicalname2", "Thermoproteia")

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
    assert result.shape[1] == 4
    assert _contains(result, "id", 1000002)
    assert _contains(result, "canonicalname", "Caldisphaera")
    assert _unique_equals(result, "id2", 10705623)
    assert _unique_equals(result, "canonicalname2", "Thermoproteia")

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
    assert result.shape[1] == 4
    assert _contains(result, "id", 3797)
    assert _contains(result, "canonicalname", "Pyrodictiaceae")
    assert _unique_equals(result, "id2", 10705623)
    assert _unique_equals(result, "canonicalname2", "Thermoproteia")

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
    assert result.shape[1] == 4
    assert _contains(result, "id", 564)
    assert _contains(result, "canonicalname", "Sulfolobales")
    assert _unique_equals(result, "id2", 10705623)
    assert _unique_equals(result, "canonicalname2", "Thermoproteia")

