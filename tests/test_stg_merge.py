"""Tests for stg_observations.py — merge logic, source column, H3, row counts.

These tests call merge_observations() directly without dbt.
They use minimal synthetic CSVs so there is no dependency on real data files
or Snowflake connectivity.
"""
import pathlib

import h3
import pandas as pd
import pytest

from dbt.models.staging.stg_observations import COLS, H3_RESOLUTIONS, merge_observations


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

INAT_ROW = {
    "id": "3257308", "uuid": "abc-123", "scientific_name": "Trillium grandiflorum",
    "common_name": "white trillium", "taxon_id": "48035", "iconic_taxon_name": "Plantae",
    "observed_on": "2026-05-20", "time_observed_at": "2026-05-20T10:00:00",
    "latitude": 41.2392, "longitude": -73.5673,
    "positional_accuracy": 8, "coordinates_obscured": False,
    "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/1/medium.jpg",
    "url": "https://www.inaturalist.org/observations/3257308",
    "quality_grade": "research", "num_identification_agreements": 3,
    "num_identification_disagreements": 0, "captive_cultivated": False,
    "place_guess": "Ward Pound Ridge", "species_guess": "Trillium grandiflorum",
    "description": "", "license": "CC-BY-NC",
}

LOCAL_ROW = {
    "id": "arq-20260520-abc123", "uuid": "", "scientific_name": "Arisaema triphyllum",
    "common_name": "", "taxon_id": "", "iconic_taxon_name": "Plantae",
    "observed_on": "2026-05-20", "time_observed_at": "2026-05-20T10:32:18",
    "latitude": 41.2398, "longitude": -73.5671,
    "positional_accuracy": "", "coordinates_obscured": False,
    "image_url": "/local/path/Q1-Arisaema.jpeg",
    "url": "", "quality_grade": "casual",
    "num_identification_agreements": 0, "num_identification_disagreements": 0,
    "captive_cultivated": False, "place_guess": "", "species_guess": "Arisaema triphyllum",
    "description": "Large clump", "license": "CC-BY-NC",
    "source": "arborphy",
}


def _write_csv(path: pathlib.Path, rows: list[dict], cols: list[str]):
    df = pd.DataFrame(rows, columns=cols)
    df.to_csv(path, index=False)


@pytest.fixture()
def data_dir_inat_only(tmp_path):
    """data/ with observations.csv only."""
    _write_csv(tmp_path / "observations.csv", [INAT_ROW], COLS)
    return tmp_path


@pytest.fixture()
def data_dir_with_local(tmp_path):
    """data/ with both observations.csv and local_observations.csv."""
    _write_csv(tmp_path / "observations.csv", [INAT_ROW], COLS)
    _write_csv(tmp_path / "local_observations.csv", [LOCAL_ROW], COLS + ["source"])
    return tmp_path


@pytest.fixture()
def data_dir_no_gps(tmp_path):
    """data/ containing a row with missing GPS to test the drop filter."""
    no_gps = {**INAT_ROW, "id": "no-gps", "latitude": None, "longitude": None}
    _write_csv(tmp_path / "observations.csv", [INAT_ROW, no_gps], COLS)
    return tmp_path


# ---------------------------------------------------------------------------
# iNat-only mode
# ---------------------------------------------------------------------------

class TestInatOnly:
    def test_has_local_false(self, data_dir_inat_only):
        _, stats = merge_observations(data_dir_inat_only)
        assert stats["has_local"] is False

    def test_source_column_is_inat(self, data_dir_inat_only):
        df, _ = merge_observations(data_dir_inat_only)
        assert (df["source"] == "inat").all()

    def test_row_count(self, data_dir_inat_only):
        df, stats = merge_observations(data_dir_inat_only)
        assert len(df) == 1
        assert stats["inat_rows"] == 1
        assert stats["local_rows"] == 0
        assert stats["total_rows"] == 1

    def test_h3_columns_present(self, data_dir_inat_only):
        df, _ = merge_observations(data_dir_inat_only)
        for res in H3_RESOLUTIONS:
            assert f"h3_res{res}" in df.columns

    def test_h3_values_nonzero(self, data_dir_inat_only):
        df, _ = merge_observations(data_dir_inat_only)
        for res in H3_RESOLUTIONS:
            assert df[f"h3_res{res}"].iloc[0] != 0


# ---------------------------------------------------------------------------
# Merge mode (iNat + local)
# ---------------------------------------------------------------------------

class TestMergeMode:
    def test_has_local_true(self, data_dir_with_local):
        _, stats = merge_observations(data_dir_with_local)
        assert stats["has_local"] is True

    def test_total_row_count(self, data_dir_with_local):
        df, stats = merge_observations(data_dir_with_local)
        assert len(df) == 2
        assert stats["inat_rows"] == 1
        assert stats["local_rows"] == 1
        assert stats["total_rows"] == 2

    def test_source_values(self, data_dir_with_local):
        df, _ = merge_observations(data_dir_with_local)
        sources = set(df["source"].tolist())
        assert sources == {"inat", "arborphy"}

    def test_inat_row_source(self, data_dir_with_local):
        df, _ = merge_observations(data_dir_with_local)
        inat_row = df[df["id"] == "3257308"].iloc[0]
        assert inat_row["source"] == "inat"

    def test_local_row_source(self, data_dir_with_local):
        df, _ = merge_observations(data_dir_with_local)
        local_row = df[df["id"] == "arq-20260520-abc123"].iloc[0]
        assert local_row["source"] == "arborphy"

    def test_no_id_duplication(self, data_dir_with_local):
        df, _ = merge_observations(data_dir_with_local)
        assert df["id"].nunique() == len(df)

    def test_scientific_names_preserved(self, data_dir_with_local):
        df, _ = merge_observations(data_dir_with_local)
        names = set(df["scientific_name"].tolist())
        assert "Trillium grandiflorum" in names
        assert "Arisaema triphyllum" in names


# ---------------------------------------------------------------------------
# GPS filter
# ---------------------------------------------------------------------------

class TestGpsFilter:
    def test_drops_rows_without_gps(self, data_dir_no_gps):
        df, stats = merge_observations(data_dir_no_gps)
        assert len(df) == 1
        assert stats["dropped_no_gps"] == 1
        assert stats["total_rows"] == 1

    def test_retained_row_has_gps(self, data_dir_no_gps):
        df, _ = merge_observations(data_dir_no_gps)
        assert df["latitude"].notna().all()
        assert df["longitude"].notna().all()


# ---------------------------------------------------------------------------
# H3 correctness
# ---------------------------------------------------------------------------

class TestH3Correctness:
    """Spot-check that H3 cells are computed correctly for a known coordinate."""

    # Ward Pound Ridge centre ~41.2392, -73.5673
    LAT, LON = 41.2392, -73.5673

    def test_h3_res9_matches_library(self, tmp_path):
        row = {**INAT_ROW, "latitude": self.LAT, "longitude": self.LON}
        _write_csv(tmp_path / "observations.csv", [row], COLS)
        df, _ = merge_observations(tmp_path)
        expected = int(h3.latlng_to_cell(self.LAT, self.LON, 9), 16)
        assert df["h3_res9"].iloc[0] == expected

    def test_h3_res13_matches_library(self, tmp_path):
        row = {**INAT_ROW, "latitude": self.LAT, "longitude": self.LON}
        _write_csv(tmp_path / "observations.csv", [row], COLS)
        df, _ = merge_observations(tmp_path)
        expected = int(h3.latlng_to_cell(self.LAT, self.LON, 13), 16)
        assert df["h3_res13"].iloc[0] == expected

    def test_all_four_resolutions_differ(self, tmp_path):
        """Different resolutions must produce different H3 indices."""
        row = {**INAT_ROW, "latitude": self.LAT, "longitude": self.LON}
        _write_csv(tmp_path / "observations.csv", [row], COLS)
        df, _ = merge_observations(tmp_path)
        vals = [df[f"h3_res{r}"].iloc[0] for r in H3_RESOLUTIONS]
        assert len(set(vals)) == 4
