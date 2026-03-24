from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/co-occurrence", tags=["co-occurrence"])


@router.get("/top")
def top(limit: int = Query(50, ge=1, le=500)):
    from kg.queries.co_occurrence import species_co_occurrence
    df = species_co_occurrence()
    if df.empty:
        return {"data": [], "total": 0}
    return {"data": df.head(limit).to_dict(orient="records"), "total": len(df)}


@router.get("/species-list")
def species_list():
    from kg.queries.co_occurrence import species_co_occurrence
    df = species_co_occurrence()
    if df.empty:
        return {"data": []}
    return {"data": sorted(df["species"].tolist())}


@router.get("/graph")
def graph():
    from kg.queries.co_occurrence import species_co_occurrence_graph, species_communities
    edges_df = species_co_occurrence_graph()
    comm_df = species_communities()
    if edges_df.empty:
        return {"nodes": [], "edges": [], "communities": {}}
    nodes = sorted(set(edges_df["source"].tolist() + edges_df["target"].tolist()))
    edges = edges_df.to_dict(orient="records")
    communities = {}
    if not comm_df.empty:
        communities = dict(zip(comm_df["species"], comm_df["community"]))
    return {"nodes": nodes, "edges": edges, "communities": communities}


@router.get("/communities")
def communities():
    from kg.queries.co_occurrence import community_summary
    df = community_summary()
    if df.empty:
        return {"data": [], "total": 0}
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/species/{species_name}/shared-features")
def shared_features(species_name: str):
    from kg.queries.co_occurrence import shared_features_for_co_occurring_species
    df = shared_features_for_co_occurring_species(species_name)
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["feature", "value", "species_count"]
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/species/{species_name:path}")
def for_species(species_name: str, granularity: str = Query("day")):
    from kg.queries.co_occurrence import co_occurrence_for_species
    df = co_occurrence_for_species(species_name, granularity=granularity)
    if df.empty:
        raise HTTPException(404, f"No co-occurrences found for '{species_name}'")
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/cell/{h3_index}")
def in_cell(h3_index: int, limit: int = Query(100, ge=1, le=1000)):
    from kg.queries.co_occurrence import species_co_occurrence_in_cell
    df = species_co_occurrence_in_cell(h3_index)
    if df.empty:
        raise HTTPException(404, f"No observations in cell {h3_index}")
    df.columns = ["observation_count", "species_name"]
    return {"data": df.head(limit).to_dict(orient="records"), "total": len(df)}
