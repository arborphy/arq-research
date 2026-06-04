"""Tests for quest contract validation endpoint."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from webapp.backend.main import app
from webapp.backend.contracts.quest import (
    CameraPose,
    FeatureTarget,
    MediaAttachment,
    MomentHint,
    ObservationPlan,
    ObservationTarget,
    Quest,
    QuestStop,
    ValidationResponse,
)


@pytest.fixture()
def client():
    return TestClient(app)


# ── Minimal valid quest fixture ─────────────────────────────────────────────

@pytest.fixture()
def valid_quest_payload():
    return {
        "id": "quest-test-001",
        "name": "Test Quest",
        "created": "2026-06-03T10:00:00Z",
        "difficulty": "easy",
        "estimated_duration_minutes": 30,
        "stops": [
            {
                "id": "stop-001",
                "name": "Trailhead",
                "lat": 41.2392,
                "lon": -73.5673,
                "alt": 150.0,
                "moment": {"dayOfYear": 145, "window": 7},
                "observations": [
                    {
                        "id": "obs-plan-001",
                        "name": "Look for Trillium",
                        "date": "2026-05-25",
                        "targets": [
                            {
                                "id": "target-001",
                                "target_type": "taxon",
                                "taxon_name": "Trillium grandiflorum",
                                "common_name": "white trillium",
                                "target_features": [
                                    {
                                        "group": "flower",
                                        "feature": "petal_count",
                                        "value": 3,
                                        "hint": "Count the petals",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


# ── Model unit tests ────────────────────────────────────────────────────────

class TestModels:
    def test_feature_target_defaults(self):
        ft = FeatureTarget(group="leaf", feature="shape")
        assert ft.group == "leaf"
        assert ft.feature == "shape"
        assert ft.value is None
        assert ft.hint is None

    def test_moment_hint_alias(self):
        mh = MomentHint(dayOfYear=200, window=10)
        assert mh.day_of_year == 200
        assert mh.window == 10

    def test_moment_hint_serialization(self):
        mh = MomentHint(dayOfYear=145, window=7)
        data = mh.model_dump(by_alias=True, mode='json')
        assert 'dayOfYear' in data
        assert data['dayOfYear'] == 145
        assert 'day_of_year' not in data

    def test_moment_hint_bounds(self):
        with pytest.raises(Exception):
            MomentHint(dayOfYear=0)
        with pytest.raises(Exception):
            MomentHint(dayOfYear=400)

    def test_quest_stop_geo_bounds(self):
        with pytest.raises(Exception):
            QuestStop(id="x", lat=91, lon=0)
        with pytest.raises(Exception):
            QuestStop(id="x", lat=0, lon=181)

    def test_quest_empty_stops_allowed_at_model_level(self):
        q = Quest(id="q1", name="Empty")
        assert q.stops == []

    def test_media_attachment_new_fields(self):
        media = MediaAttachment(
            id="media-001",
            media_type="audio",
            url_or_local_path="path/to/audio.mp3",
            notes="Birdsong recording",
        )
        assert media.id == "media-001"
        assert media.media_type == "audio"
        assert media.url_or_local_path == "path/to/audio.mp3"
        assert media.notes == "Birdsong recording"

    def test_media_attachment_defaults(self):
        media = MediaAttachment(id="media-002")
        assert media.media_type == "image"
        assert media.url_or_local_path is None
        assert media.notes is None

    def test_media_type_literal_validation(self):
        with pytest.raises(Exception):
            MediaAttachment(id="m1", media_type="gif")

    def test_target_type_literal_validation(self):
        target = ObservationTarget(id="t1", target_type="taxon")
        assert target.target_type == "taxon"

        with pytest.raises(Exception):
            ObservationTarget(id="t2", target_type="unknown")

    def test_difficulty_literal_validation(self):
        q_easy = Quest(id="q1", name="Easy", difficulty="easy")
        assert q_easy.difficulty == "easy"

        q_none = Quest(id="q2", name="No Diff")
        assert q_none.difficulty is None

        with pytest.raises(Exception):
            Quest(id="q3", name="Bad", difficulty="hard")


# ── Endpoint: valid payload ────────────────────────────────────────────────

class TestValidateEndpoint:
    def test_valid_quest(self, client, valid_quest_payload):
        resp = client.post("/api/contracts/quest/validate", json=valid_quest_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "valid"
        assert body["quest"]["id"] == "quest-test-001"
        assert body["quest"]["stops"][0]["id"] == "stop-001"
        assert body["errors"] == []

    def test_valid_quest_minimal(self, client):
        payload = {
            "id": "q-min",
            "name": "Minimal",
            "stops": [{"id": "s1", "lat": 0, "lon": 0}],
        }
        resp = client.post("/api/contracts/quest/validate", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "valid"

    def test_no_stops_returns_invalid(self, client):
        payload = {"id": "q-empty", "name": "Empty", "stops": []}
        resp = client.post("/api/contracts/quest/validate", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "invalid"
        assert "at least one stop" in body["errors"][0].lower()
        assert body["quest"] is None

    def test_missing_required_field_422(self, client):
        payload = {"name": "No Id", "stops": [{"id": "s1", "lat": 0, "lon": 0}]}
        resp = client.post("/api/contracts/quest/validate", json=payload)
        assert resp.status_code == 422

    def test_invalid_lat_422(self, client):
        payload = {
            "id": "q1",
            "name": "Bad Lat",
            "stops": [{"id": "s1", "lat": 999, "lon": 0}],
        }
        resp = client.post("/api/contracts/quest/validate", json=payload)
        assert resp.status_code == 422

    def test_extra_fields_preserved(self, client, valid_quest_payload):
        valid_quest_payload["stops"][0]["custom_stop_field"] = "hello"
        resp = client.post("/api/contracts/quest/validate", json=valid_quest_payload)
        assert resp.status_code == 200
        assert resp.json()["quest"]["stops"][0]["custom_stop_field"] == "hello"
