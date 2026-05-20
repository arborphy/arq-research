from fastapi import APIRouter, Query

from kg.queries.spatial import LOCATION_CONCEPTS

router = APIRouter(prefix="/spatial", tags=["spatial"])


@router.get("/places")
def place_hierarchy():
    """Geographic hierarchy counts: obs reachable at Park/City/State/Country level."""
    from kg.queries.spatial import place_hierarchy_stats
    rows = place_hierarchy_stats()
    return {"data": rows}


@router.get("/within")
def within_pairs(
    subject: str = Query(..., pattern="^(Observation|Park|City|State|Country)$"),
    container: str = Query(..., pattern="^(EcoSite|Park|City|State|Country)$"),
):
    """All (subject, container) pairs where within(subject, container) holds."""
    from kg.queries.spatial import within_pairs as _within_pairs
    df = _within_pairs(subject, container)
    if df.empty:
        return {"data": [], "subject": subject, "container": container}
    return {
        "data": df.to_dict(orient="records"),
        "subject": subject,
        "container": container,
    }
