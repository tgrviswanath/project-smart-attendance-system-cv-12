from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

MOCK_REGISTER = {"success": True, "person_id": 0, "name": "Alice", "total_registered": 1}
MOCK_RECOGNIZE = {
    "recognized": [{"name": "Alice", "person_id": 0, "distance": 0.12}],
    "unknown_count": 0, "face_count": 1, "annotated_image": "base64",
}
MOCK_STATS = {"registered_persons": 1, "attendance_records": 1, "tolerance": 0.5}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


@patch("app.core.service.register_person", new_callable=AsyncMock, return_value=MOCK_REGISTER)
def test_register_endpoint(mock_reg):
    r = client.post("/api/v1/register",
        files={"file": ("alice.jpg", b"fake", "image/jpeg")},
        data={"name": "Alice"})
    assert r.status_code == 200
    assert r.json()["name"] == "Alice"


@patch("app.core.service.recognize_faces", new_callable=AsyncMock, return_value=MOCK_RECOGNIZE)
def test_recognize_endpoint(mock_rec):
    r = client.post("/api/v1/recognize",
        files={"file": ("group.jpg", b"fake", "image/jpeg")})
    assert r.status_code == 200
    assert len(r.json()["recognized"]) == 1


@patch("app.core.service.get_stats", new_callable=AsyncMock, return_value=MOCK_STATS)
def test_stats_endpoint(mock_stats):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    assert r.json()["registered_persons"] == 1
