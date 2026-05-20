from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from webapp.backend.utils import h3_int_to_hex

router = APIRouter(prefix="/trails", tags=["trails"])


@router.get("")
def list_trails():
    from kg.queries.trails import list_trails as _list
    df = _list()
    if df.empty:
        return {"data": []}
    df.columns = ["osm_id", "name", "highway", "surface"]
    df = df.fillna("")
    return {"data": df.to_dict(orient="records")}


@router.get("/observations")
def all_observations():
    from kg.queries.trails import all_trail_observations
    df = all_trail_observations()
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["inat_id", "latitude", "longitude", "date", "image_url", "species"]
    df["date"] = df["date"].astype(str)
    df = df.fillna("")
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/ecosites")
def all_ecosites():
    from kg.queries.trails import all_trail_ecosites
    df = all_trail_ecosites()
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["ecosite_id"]
    return {"data": sorted(df["ecosite_id"].tolist()), "total": len(df)}


@router.get("/ecosite-cells")
def all_ecosite_cells():
    from kg.queries.trails import all_trail_ecosite_cells
    df = all_trail_ecosite_cells()
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["ecosite_id", "h3_index"]
    df["h3_index"] = df["h3_index"].map(h3_int_to_hex)
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/cells")
def all_cells():
    from kg.queries.trails import all_trail_cells
    df = all_trail_cells()
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["h3_index"]
    df["h3_index"] = df["h3_index"].map(h3_int_to_hex)
    return {"data": df["h3_index"].tolist(), "total": len(df)}


@router.get("/{osm_id}/cells")
def trail_cells(osm_id: str):
    from kg.queries.trails import cells_for_trail
    df = cells_for_trail(osm_id)
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["h3_index"]
    df["h3_index"] = df["h3_index"].map(h3_int_to_hex)
    return {"data": df["h3_index"].tolist(), "total": len(df)}


@router.get("/{osm_id}/ecosite-cells")
def trail_ecosite_cells(osm_id: str):
    from kg.queries.trails import trail_ecosite_cells as _cells
    df = _cells(osm_id)
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["ecosite_id", "h3_index"]
    df["h3_index"] = df["h3_index"].map(h3_int_to_hex)
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/{osm_id}/ecosites")
def trail_ecosites(osm_id: str):
    from kg.queries.trails import ecosites_on_trail
    df = ecosites_on_trail(osm_id)
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["ecosite_id"]
    return {"data": sorted(df["ecosite_id"].tolist()), "total": len(df)}


class FeatureFilter(BaseModel):
    feature: str
    value: str


@router.get("/{osm_id}/features")
def trail_features(osm_id: str):
    from kg.queries.trails import features_for_trail
    df = features_for_trail(osm_id)
    if df.empty:
        return {"data": {}}
    df.columns = ["feature", "value", "species_count"]
    results: dict = {}
    for feature_name, group in df.groupby("feature"):
        results[feature_name] = group[["value", "species_count"]].to_dict(orient="records")
    return {"data": results}


@router.post("/{osm_id}/species/filter")
def filter_trail_species(osm_id: str, filters: List[FeatureFilter]):
    from kg.queries.trails import filtered_species_on_trail
    if not filters:
        from kg.queries.trails import species_on_trail
        df = species_on_trail(osm_id)
    else:
        df = filtered_species_on_trail(osm_id, [f.model_dump() for f in filters])
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["name"]
    return {"data": sorted(df["name"].tolist()), "total": len(df)}


@router.get("/{osm_id}/species")
def trail_species(osm_id: str):
    from kg.queries.trails import species_on_trail
    df = species_on_trail(osm_id)
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["name"]
    df = df.sort_values("name")
    return {"data": df["name"].tolist(), "total": len(df)}


@router.get("/{osm_id}/observations")
def trail_observations(osm_id: str):
    from kg.queries.trails import observations_on_trail
    df = observations_on_trail(osm_id)
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["inat_id", "latitude", "longitude", "date", "image_url", "species"]
    df["date"] = df["date"].astype(str)
    df = df.fillna("")
    return {"data": df.to_dict(orient="records"), "total": len(df)}
