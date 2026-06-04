"""Queries demonstrating global predicates across concept types.

The key insight: select(Child.name, Parent.name) where Child.part_of(Parent)
— same query shape, just swap the Concepts.
"""
from relationalai.semantics import count, select, where

import kg.loaders.newcomb  # noqa: F401
import kg.loaders.observations  # noqa: F401
import kg.model.derived  # noqa: F401

from kg.model.core.features import Feature, FeatureValue
from kg.model.core.taxonomy import Genus, Kingdom, Species
from webapp.backend.cache import ttl_cache

# (label, child_concept, parent_concept)
CONCEPT_PAIRS = [
    ("Species → Genus", Species, Genus),
    ("Genus → Kingdom", Genus, Kingdom),
    ("FeatureValue → Feature", FeatureValue, Feature),
]


def _part_of_query(child_cls, parent_cls):
    """Query part_of between two concept types."""
    c = child_cls.ref()
    p = parent_cls.ref()
    return where(c.part_of(p)).select(c.name, p.name).to_df()


def _part_of_count(child_cls, parent_cls):
    """Count part_of pairs between two concept types."""
    c = child_cls.ref()
    p = parent_cls.ref()
    df = where(c.part_of(p)).select(count(c)).to_df()
    return int(df.iloc[0, 0]) if not df.empty else 0


@ttl_cache(ttl_seconds=600, namespace="ref")
def predicate_summary():
    """Count part_of pairs per concept type."""
    import pandas as pd

    rows = []
    total = 0
    for label, child_cls, parent_cls in CONCEPT_PAIRS:
        c = _part_of_count(child_cls, parent_cls)
        total += c
        rows.append({"concept_type": label, "predicate": "part_of", "count": c})

    rows.append({"concept_type": "ALL (Entity)", "predicate": "part_of", "count": total})
    return pd.DataFrame(rows)


@ttl_cache(ttl_seconds=600, namespace="ref")
def part_of_pairs(concept_type: str = "all", limit: int = 50):
    """Return part_of pairs for a concept type."""
    import pandas as pd

    pair_map = {
        "species": [CONCEPT_PAIRS[0]],
        "genus": [CONCEPT_PAIRS[1]],
        "feature": [CONCEPT_PAIRS[2]],
        "all": CONCEPT_PAIRS,
    }

    frames = []
    for label, child_cls, parent_cls in pair_map.get(concept_type, []):
        df = _part_of_query(child_cls, parent_cls)
        if not df.empty:
            df.columns = ["child", "parent"]
            df = df.head(limit)
            df["concept_type"] = label
            frames.append(df)

    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame(columns=["child", "parent", "concept_type"])


@ttl_cache(ttl_seconds=600, namespace="ref")
def predicate_graph():
    """Build graph data for part_of + feature_values visualization."""
    nodes = {}
    edges = []

    # part_of edges
    graph_pairs = [
        ("Species", "Genus", Species, Genus),
        ("Genus", "Kingdom", Genus, Kingdom),
        ("FeatureValue", "Feature", FeatureValue, Feature),
    ]

    for child_type, parent_type, child_cls, parent_cls in graph_pairs:
        df = _part_of_query(child_cls, parent_cls)
        if not df.empty:
            df.columns = ["child", "parent"]
            df = df.head(40)
            for _, row in df.iterrows():
                child_id = f"{child_type.lower()}:{row['child']}"
                parent_id = f"{parent_type.lower()}:{row['parent']}"
                nodes[child_id] = {"id": child_id, "label": str(row["child"]), "concept_type": child_type}
                nodes[parent_id] = {"id": parent_id, "label": str(row["parent"]), "concept_type": parent_type}
                edges.append({"source": child_id, "target": parent_id, "type": "part_of"})

    # Species → FeatureValue edges (hasFeature) via refs
    species_in_graph = {nid.split(":", 1)[1] for nid, n in nodes.items() if n["concept_type"] == "Species"}
    if species_in_graph:
        try:
            s = Species.ref()
            fv = FeatureValue.ref()
            df = where(s.feature_values(fv)).select(s.name, fv.value).to_df()
            if not df.empty:
                df.columns = ["species", "feature_value"]
                for _, row in df.iterrows():
                    if row["species"] in species_in_graph:
                        s_id = f"species:{row['species']}"
                        fv_id = f"featurevalue:{row['feature_value']}"
                        if fv_id not in nodes:
                            nodes[fv_id] = {"id": fv_id, "label": str(row["feature_value"]), "concept_type": "FeatureValue"}
                        edges.append({"source": s_id, "target": fv_id, "type": "hasFeature"})
        except Exception:
            pass  # hasFeature edges are optional — don't break the graph

    return {"nodes": list(nodes.values()), "edges": edges}
