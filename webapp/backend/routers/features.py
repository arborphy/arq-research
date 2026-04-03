from fastapi import APIRouter, Query
from relationalai.semantics import select, where, count

import kg.loaders.observations  # noqa: F401
import kg.loaders.newcomb  # noqa: F401

from kg.model.core.taxonomy import Species
from kg.model.core.features import Feature, FeatureValue
from kg.model.core.keys.key import IdentificationKey

router = APIRouter(prefix="/features", tags=["features"])


@router.get("/")
def list_features():
    results = {}
    for feature_name in ["flower_type", "plant_type", "leaf_type"]:
        df = where(
            IdentificationKey.feature_value(FeatureValue),
            FeatureValue.feature(Feature),
            Feature.name == feature_name,
            IdentificationKey.species(Species),
        ).select(
            FeatureValue.value,
            count(Species).per(FeatureValue),
        ).to_df()
        if not df.empty:
            df.columns = ["value", "species_count"]
            results[feature_name] = df.to_dict(orient="records")
    return {"data": results}


@router.get("/species")
def species_by_feature(feature: str = Query(...), value: str = Query(...)):
    df = where(
        IdentificationKey.feature_value(FeatureValue),
        FeatureValue.feature(Feature),
        Feature.name == feature,
        FeatureValue.value == value,
        IdentificationKey.species(Species),
    ).select(
        Species.name,
    ).to_df()
    if df.empty:
        return {"data": [], "total": 0}
    df.columns = ["species"]
    return {"data": df.to_dict(orient="records"), "total": len(df)}


@router.get("/newcomb-key/{species_name:path}")
def newcomb_key(species_name: str):
    from kg.queries.newcomb import newcomb_key_for_species
    df = newcomb_key_for_species(species_name)
    if df.empty:
        return {"data": None}
    df.columns = ["group_number", "flower_type", "plant_type", "leaf_type"]
    return {"data": df.iloc[0].to_dict()}
