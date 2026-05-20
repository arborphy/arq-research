"""Queries for located_in and within predicates — named place hierarchy."""
from relationalai.semantics import where

import kg.loaders.observations  # noqa: F401
import kg.loaders.location      # noqa: F401
import kg.loaders.ecosites      # noqa: F401
import kg.model.derived         # noqa: F401

from kg.model.core.observations import Observation
from kg.model.core.h3cell import EcoSite
from kg.model.core.location import Park, City, State, Country
from kg.model.core.predicates import located_in, within


def place_hierarchy_stats():
    """Obs counts at each named-place level: direct located_in vs. within (transitive).

    Uses `within` for the transitive counts — it follows the full chain
    obs →[located_in]→ park →[located_in]→ city →[located_in]→ state →[located_in]→ country.

    Returns list of dicts:
        [{"level": "Park",    "name": "...", "within": N, "direct": N},
         {"level": "City",    "name": "...", "within": N, "direct": 0}, ...]
    """
    from relationalai.semantics import count

    rows = []

    for level, Concept in [("Park", Park), ("City", City), ("State", State), ("Country", Country)]:
        obs = Observation.ref()
        place = Concept.ref()

        # within: obs transitively located_in this place (Park is also direct)
        within_df = (
            where(within(obs, place))
            .select(place.name, count(obs))
            .to_df()
        )

        # direct: obs has a located_in fact pointing straight to this place
        direct_df = (
            where(located_in(obs, place))
            .select(place.name, count(obs))
            .to_df()
        )

        if not within_df.empty:
            within_df.columns = ["name", "within"]
            direct_count = 0
            if not direct_df.empty:
                direct_df.columns = ["name", "direct"]
                direct_count = int(direct_df["direct"].iloc[0])
            for _, r in within_df.iterrows():
                rows.append({
                    "level": level,
                    "name": r["name"],
                    "within": int(r["within"]),
                    "direct": direct_count,
                })

    return rows


LOCATION_CONCEPTS = ("Park", "City", "State", "Country")
CONTAINER_CONCEPTS = ("EcoSite",) + LOCATION_CONCEPTS
SUBJECT_CONCEPTS   = ("Observation",) + LOCATION_CONCEPTS


def within_pairs(subject_level: str, container_level: str):
    """Return rows where within(subject, container) holds.

    subject_level: "Observation" | "Park" | "City" | "State" | "Country"
    container_level: "EcoSite" | "Park" | "City" | "State" | "Country"

    For Observation subjects, returns one row per container with a `count` field.
    For place subjects, returns one row per (subject_name, container_name) pair.
    """
    from relationalai.semantics import count

    place_map = {"Park": Park, "City": City, "State": State, "Country": Country}

    # Resolve container — EcoSite uses ecosite_id, places use name
    if container_level == "EcoSite":
        container = EcoSite.ref()
        container_id = container.ecosite_id
    else:
        ContainerConcept = place_map[container_level]
        container = ContainerConcept.ref()
        container_id = container.name

    if subject_level == "Observation":
        obs = Observation.ref()
        df = (
            where(within(obs, container))
            .select(container_id, count(obs))
            .to_df()
        )
        if not df.empty:
            df.columns = ["container", "count"]
            df["subject"] = "Observation"
        return df

    SubjectConcept = place_map[subject_level]
    subject = SubjectConcept.ref()
    df = (
        where(within(subject, container))
        .select(subject.name, container_id)
        .to_df()
    )
    if not df.empty:
        df.columns = ["subject", "container"]
    return df
