from fastapi import APIRouter, HTTPException, Query

from webapp.backend.utils import h3_int_to_hex

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/species/{species_name:path}/observations")
def species_observations(species_name: str):
    from kg.queries.geography import observations_for_species
    df = observations_for_species(species_name)
    if df.empty:
        raise HTTPException(404, f"No observations found for '{species_name}'")
    df.columns = ["lat", "lon", "date", "inat_id", "image_url"]
    df["date"] = df["date"].astype(str)
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/species/{species_name:path}/co-occurrence-cells")
def species_co_occurrence_cells(species_name: str):
    from kg.queries.geography import co_occurrence_cells_for_species
    df = co_occurrence_cells_for_species(species_name)
    if df.empty:
        return {"data": [], "total": 0}
    df["h3_index"] = df["h3_index"].map(h3_int_to_hex)
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/species/{species_name:path}/co-occurring-observations")
def co_occurring_observations(species_name: str):
    from kg.queries.geography import co_occurring_observations_for_species
    df = co_occurring_observations_for_species(species_name)
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["lat", "lon", "date", "inat_id", "species_name"]
    df["date"] = df["date"].astype(str)
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/cells")
def list_cells(day_of_year: int = Query(None, ge=1, le=366)):
    if day_of_year is not None:
        from kg.queries.geography import h3_cells_on_day
        df = h3_cells_on_day(day_of_year)
        if df.empty:
            return {"data": []}
        df.columns = ["h3_index", "observation_count"]
        df["h3_index"] = df["h3_index"].map(h3_int_to_hex)
        return {"data": df.to_dict(orient="records")}
    else:
        from kg.queries.geography import all_h3_cells
        df = all_h3_cells()
        if df.empty:
            return {"data": []}
        df.columns = ["h3_index"]
        df["h3_index"] = df["h3_index"].map(h3_int_to_hex)
        return {"data": [{"h3_index": h, "observation_count": 0} for h in df["h3_index"]]}


@router.get("/visible")
def visible_species(h3_index: str = Query(...), day_of_year: int = Query(..., ge=1, le=366)):
    from kg.queries.geography import species_visible_at
    h3_int = int(h3_index, 16)
    df = species_visible_at(h3_int, day_of_year)
    if df.empty:
        return {"data": [], "total": 0}
    return {"data": df.to_dict(orient="records"), "total": len(df)}
