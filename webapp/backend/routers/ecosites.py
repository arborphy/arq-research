from fastapi import APIRouter, HTTPException

from webapp.backend.utils import h3_int_to_hex

router = APIRouter(prefix="/ecosites", tags=["ecosites"])


@router.get("")
def list_ecosites():
    from kg.queries.ecosites import list_ecosites as _list
    df = _list()
    if df.empty:
        return {"data": [], "total": 0}
    col = df.columns[0]
    ids = sorted(df[col].tolist())
    return {"data": ids, "total": len(ids)}


@router.get("/{ecosite_id}/cells")
def ecosite_cells(ecosite_id: str):
    from kg.queries.ecosites import cells_for_ecosite
    df = cells_for_ecosite(ecosite_id)
    if df.empty:
        raise HTTPException(404, f"No cells found for ecosite '{ecosite_id}'")
    df.columns = ["h3_index"]
    df["h3_index"] = df["h3_index"].map(h3_int_to_hex)
    return {"data": df["h3_index"].tolist(), "total": len(df)}


@router.get("/{ecosite_id}/cells/compacted")
def ecosite_cells_compacted(ecosite_id: str):
    from kg.queries.ecosites import compacted_cells_for_ecosite
    df = compacted_cells_for_ecosite(ecosite_id)
    if df.empty:
        raise HTTPException(404, f"No compacted cells found for ecosite '{ecosite_id}'")
    df.columns = ["h3_index"]
    df["h3_index"] = df["h3_index"].map(h3_int_to_hex)
    return {"data": df["h3_index"].tolist(), "total": len(df)}


@router.get("/with-observations")
def ecosites_with_observations():
    """Ecosite IDs that have at least one iNaturalist observation."""
    from kg.queries.ecosite_species import ecosites_with_observations as _query
    df = _query()
    if df.empty:
        return {"data": [], "total": 0}
    ids = sorted(df["ecosite_id"].tolist())
    return {"data": ids, "total": len(ids)}


@router.get("/{ecosite_id}/species")
def ecosite_species(ecosite_id: str):
    """Species observed within a given ecosite."""
    from kg.queries.ecosite_species import species_in_ecosite
    df = species_in_ecosite(ecosite_id)
    if df.empty:
        return {"data": [], "total": 0}
    return {"data": sorted(df["species"].tolist()), "total": len(df)}
