import logging
import traceback
from typing import List

from fastapi import APIRouter, Query
from pydantic import BaseModel
from relationalai.semantics import select, where, count

logger = logging.getLogger(__name__)

import kg.loaders.observations  # noqa: F401
import kg.loaders.newcomb  # noqa: F401
import kg.loaders.gobotany  # noqa: F401

from kg.model.core.taxonomy import Species
from kg.model.core.features import Feature, Category
from kg.model.core.keys.key import Description
from kg.model.core.provenance import DataSource

router = APIRouter(prefix="/features", tags=["features"])


class FeatureFilter(BaseModel):
    feature: str
    value: str


@router.get("/")
def list_features():
    try:
        df = where(
            Description.category(Category),
            Category.feature(Feature),
            Description.describes(Species),
        ).select(
            Feature.name,
            Category.value,
            count(Species).per(Feature, Category),
        ).to_df()
    except Exception as e:
        if hasattr(e, "table_objects"):
            for obj in e.table_objects:
                logger.error("  table: %s | error: %s", obj.source, obj.message)
        logger.error(traceback.format_exc())
        raise
    if df.empty:
        return {"data": {}}
    df.columns = ["feature", "value", "species_count"]
    results = {}
    for feature_name, group in df.groupby("feature"):
        results[feature_name] = group[["value", "species_count"]].to_dict(orient="records")
    return {"data": results}


@router.get("/species")
def species_by_feature(feature: str = Query(...), value: str = Query(...)):
    df = where(
        Description.category(Category),
        Category.feature(Feature),
        Feature.name == feature,
        Category.value == value,
        Description.describes(Species),
    ).select(
        Species.name,
    ).to_df()
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["species"]

    # Fetch datasources per species and merge
    src_df = where(
        Description.category(Category),
        Category.feature(Feature),
        Feature.name == feature,
        Category.value == value,
        Description.describes(Species),
        Species.source(DataSource),
    ).select(
        Species.name,
        DataSource.name,
    ).to_df()
    if not src_df.empty:
        src_df.columns = ["species", "source"]
        sources_map = src_df.groupby("species")["source"].apply(list).to_dict()
    else:
        sources_map = {}

    records = [{"species": s, "sources": sources_map.get(s, [])} for s in df["species"]]
    return {"data": records, "total": len(records)}


@router.get("/newcomb-key/{species_name:path}")
def newcomb_key(species_name: str):
    from kg.queries.newcomb import newcomb_key_for_species
    df = newcomb_key_for_species(species_name)
    if df.empty:
        return {"data": None}
    df.columns = ["group_number", "flower_type", "plant_type", "leaf_type"]
    return {"data": df.iloc[0].to_dict()}


@router.get("/for-species/{species_name:path}")
def species_own_features(species_name: str):
    s = Species.ref()
    fv = Category.ref()
    f = Feature.ref()
    ik = Description.ref()
    src = DataSource.ref()
    try:
        df = where(
            s.name == species_name,
            ik.describes(s),
            ik.category(fv),
            fv.feature(f),
            ik.source(src),
        ).select(
            f.name.alias("feature"),
            fv.value.alias("value"),
            src.name.alias("source"),
        ).to_df()
    except Exception as e:
        if hasattr(e, "table_objects"):
            for obj in e.table_objects:
                logger.error("  table: %s | error: %s", obj.source, obj.message)
        logger.error(traceback.format_exc())
        raise
    if df.empty:
        return {"data": []}
    df.columns = ["feature", "value", "source"]
    df = df.drop_duplicates()
    df = df[df["value"].notna() & (df["value"] != "NA")]
    return {"data": df.sort_values(["source", "feature"]).to_dict(orient="records")}


@router.post("/filter")
def filter_species_by_features(filters: List[FeatureFilter]):
    if not filters:
        return {"data": [], "total": 0}

    def _build_conditions(s_ref):
        conds = []
        for ff in filters:
            fv = Category.ref()
            f = Feature.ref()
            ik = Description.ref()
            conds.extend([
                ik.describes(s_ref),
                ik.category(fv),
                fv.feature(f),
                f.name == ff.feature,
                fv.value == ff.value,
            ])
        return conds

    try:
        s = Species.ref()
        df = where(*_build_conditions(s)).select(s.name.alias("species")).to_df()
    except Exception as e:
        if hasattr(e, "table_objects"):
            for obj in e.table_objects:
                logger.error("  table: %s | error: %s", obj.source, obj.message)
        logger.error(traceback.format_exc())
        raise

    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["species"]
    species_list = sorted(df["species"].drop_duplicates().tolist())

    # Get sources using the same filter conditions + DataSource join
    s2 = Species.ref()
    src = DataSource.ref()
    src_df = where(*_build_conditions(s2), s2.source(src)).select(
        s2.name.alias("species"), src.name.alias("source")
    ).to_df()

    sources_map: dict = {}
    if not src_df.empty:
        src_df.columns = ["species", "source"]
        sources_map = src_df.groupby("species")["source"].apply(list).to_dict()

    records = [{"species": name, "sources": sources_map.get(name, [])} for name in species_list]
    return {"data": records, "total": len(records)}


@router.get("/sources/{species_name:path}")
def species_sources(species_name: str):
    from kg.queries.newcomb import datasources_for_species
    df = datasources_for_species(species_name)
    if df.empty:
        return {"data": []}
    df.columns = ["name"]
    return {"data": df["name"].tolist()}
