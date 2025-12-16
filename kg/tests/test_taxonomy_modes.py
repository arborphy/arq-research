import relationalai.semantics as rai

import os
import pytest

from kg.model import define_arq


def _query_species_family(arq, family_id: int):
    return (
        rai.where(
            arq.Family.id == family_id,
            arq.Species.family(arq.Family),
        )
        .select(arq.Species.id, arq.Family.id)
        .to_df()
    )


def test_taxonomy_modes_strict_is_subset_of_ancestor():
    """Research-style test: ancestor mode should be a superset in practice.

    We keep the query small by filtering to a single well-known family.
    """

    if os.getenv("ARQ_ENABLE_TAXONOMY_MODE_COMPARISON") != "1":
        pytest.skip("Set ARQ_ENABLE_TAXONOMY_MODE_COMPARISON=1 to run mode comparison (expensive / requires fresh auth)")

    strict = define_arq(rai.Model("arq_test_taxonomy_strict"), taxonomy_mode="strict")
    ancestor = define_arq(rai.Model("arq_test_taxonomy_ancestor"), taxonomy_mode="ancestor")

    family_id = 3797
    strict_df = _query_species_family(strict, family_id)
    ancestor_df = _query_species_family(ancestor, family_id)

    print({"strict_rows": strict_df.shape[0], "ancestor_rows": ancestor_df.shape[0]})

    strict_pairs = set(zip(strict_df["id"].tolist(), strict_df["id2"].tolist()))
    ancestor_pairs = set(zip(ancestor_df["id"].tolist(), ancestor_df["id2"].tolist()))

    assert strict_pairs.issubset(ancestor_pairs)
