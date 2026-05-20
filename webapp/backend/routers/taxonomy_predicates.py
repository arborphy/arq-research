from fastapi import APIRouter, Query

router = APIRouter(prefix="/taxonomy-predicates", tags=["taxonomy-predicates"])


@router.get("/families")
def families():
    """Families that have species reachable via within_clade."""
    from kg.queries.taxonomy_predicates import families_with_species
    df = families_with_species()
    if df.empty:
        return {"data": []}
    return {"data": sorted(df["family"].tolist())}


@router.get("/family/{family_name}/species")
def family_species(
    family_name: str,
    predicate: str = Query("within_clade", pattern="^(within_clade|part_of)$"),
):
    """Species in a family via within_clade (transitive) or part_of (direct)."""
    from kg.queries.taxonomy_predicates import species_in_clade
    df = species_in_clade(family_name, use_within_clade=(predicate == "within_clade"))
    if df.empty:
        return {"data": [], "total": 0}
    return {"data": sorted(df["species"].tolist()), "total": len(df)}


@router.get("/family/{family_name}/graph")
def family_graph(family_name: str):
    """Full hierarchy graph: family → genera → species for force-directed visualization."""
    from kg.queries.taxonomy_predicates import family_graph as _family_graph
    df = _family_graph(family_name)
    if df.empty:
        return {"family": family_name, "data": []}
    return {"family": family_name, "data": df.to_dict(orient="records")}


@router.get("/family/{family_name}/genera")
def family_genera(family_name: str):
    """Genera in a family with their species count (via direct part_of)."""
    from kg.queries.taxonomy_predicates import genera_in_family
    df = genera_in_family(family_name)
    if df.empty:
        return {"data": [], "total": 0}
    df_sorted = df.sort_values("species_count", ascending=False)
    return {
        "data": df_sorted.to_dict(orient="records"),
        "total": len(df_sorted),
    }
