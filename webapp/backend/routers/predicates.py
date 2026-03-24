from fastapi import APIRouter, Query

router = APIRouter(prefix="/predicates", tags=["predicates"])


@router.get("/summary")
def summary():
    from kg.queries.predicates import predicate_summary
    df = predicate_summary()
    return {"data": df.to_dict(orient="records")}


@router.get("/pairs")
def pairs(
    concept_type: str = Query("all", regex="^(all|species|genus|feature)$"),
    limit: int = Query(50, ge=1, le=500),
):
    from kg.queries.predicates import part_of_pairs
    df = part_of_pairs(concept_type, limit)
    if df.empty:
        return {"data": [], "total": 0}
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/graph")
def graph():
    from kg.queries.predicates import predicate_graph
    return predicate_graph()
