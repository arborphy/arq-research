"""
gobotany.py — GoBotany feature data endpoints.

Reads directly from the arq-refdata parquet files so this works without
loading GoBotany into the RAI knowledge graph first.

Parquet source: arq-refdata/hierarchy_etl/data/parquet_models/gobotany_*.parquet
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/features/gobotany", tags=["gobotany"])

# ---------------------------------------------------------------------------
# Parquet loading — cached at module level (loaded once per process)
# ---------------------------------------------------------------------------

_PARQUET_DIR = (
    Path(__file__).resolve().parents[4]   # → repo root
    / "arq-refdata"
    / "hierarchy_etl"
    / "data"
    / "parquet_models"
)


@lru_cache(maxsize=1)
def _load_tables():
    p = _PARQUET_DIR
    if not p.exists():
        raise RuntimeError(f"GoBotany parquet dir not found: {p}")
    return {
        "taxon":    pd.read_parquet(p / "gobotany_taxon.parquet"),
        "feat_val": pd.read_parquet(p / "gobotany_taxon_feature_value.parquet"),
        "feature":  pd.read_parquet(p / "gobotany_feature.parquet"),
        "value":    pd.read_parquet(p / "gobotany_feature_value.parquet"),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _features_for_taxon(taxon_id: int) -> pd.DataFrame:
    """Return enriched feature assertions for a taxon as a flat DataFrame."""
    t = _load_tables()

    facts = (
        t["feat_val"][t["feat_val"]["taxon_id"] == taxon_id]
        .merge(
            t["feature"][[
                "feature_id", "display_name", "feature_group",
                "question", "hint", "image_url", "is_default_filter", "is_preview_character",
            ]],
            on="feature_id",
            how="left",
        )
        .merge(
            t["value"][[
                "feature_value_id", "display_label", "image_url",
            ]].rename(columns={"image_url": "value_image_url"}),
            on="feature_value_id",
            how="left",
        )
    )
    return facts


def _nan_to_none(v):
    """Convert pandas NaN / empty string to None for clean JSON."""
    if v is None:
        return None
    if isinstance(v, float) and v != v:   # NaN check
        return None
    s = str(v).strip()
    return s if s else None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/{species_name:path}")
def gobotany_features(species_name: str):
    """
    GoBotany feature assertions for a species, grouped by feature_group.

    Response shape:
    {
      "species":        "Carpinus caroliniana",
      "taxon_id":       3104,
      "total_features": 94,
      "groups": [
        {
          "group": "leaves",
          "features": [
            {
              "feature":       "Leaf blade shape",
              "value":         "ovate",
              "question":      "What is the shape of the leaf blade?",
              "hint":          "...",
              "feature_image": "https://...",   // or null
              "value_image":   "https://...",   // or null
              "is_default":    true,
              "is_preview":    false
            },
            ...
          ]
        },
        ...
      ]
    }
    """
    t = _load_tables()

    # Case-insensitive match
    matches = t["taxon"][
        t["taxon"]["scientific_name"].str.lower() == species_name.lower()
    ]
    if matches.empty:
        raise HTTPException(404, f"'{species_name}' not found in GoBotany")

    row = matches.iloc[0]
    taxon_id = int(row["taxon_id"])

    facts = _features_for_taxon(taxon_id)
    if facts.empty:
        return {
            "species":        row["scientific_name"],
            "taxon_id":       taxon_id,
            "common_name":    _nan_to_none(row.get("common_name")),
            "family":         _nan_to_none(row.get("family")),
            "species_url":    _nan_to_none(row.get("species_url")),
            "total_features": 0,
            "groups":         [],
        }

    # Group by feature_group, then feature display_name
    groups = []
    for group_name, group_df in facts.groupby("feature_group", sort=True):
        features = []
        for _, r in group_df.sort_values("display_name").iterrows():
            features.append({
                "feature":       _nan_to_none(r["display_name"]),
                "value":         _nan_to_none(r["display_label"]),
                "question":      _nan_to_none(r.get("question")),
                "hint":          _nan_to_none(r.get("hint")),
                "feature_image": _nan_to_none(r.get("image_url")),
                "value_image":   _nan_to_none(r.get("value_image_url")),
                "is_default":    bool(r.get("is_default_filter", False)),
                "is_preview":    bool(r.get("is_preview_character", False)),
            })
        groups.append({"group": group_name, "features": features})

    # Sort groups: preview/default groups first, then alphabetical
    priority = {"growth form": 0, "leaves": 1, "flowers": 2, "fruits or seeds": 3}
    groups.sort(key=lambda g: (priority.get(g["group"], 99), g["group"]))

    return {
        "species":        row["scientific_name"],
        "taxon_id":       taxon_id,
        "common_name":    _nan_to_none(row.get("common_name")),
        "family":         _nan_to_none(row.get("family")),
        "species_url":    _nan_to_none(row.get("species_url")),
        "total_features": len(facts),
        "groups":         groups,
    }
