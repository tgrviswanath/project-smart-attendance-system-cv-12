from fastapi.testclient import TestClient
from unittest.mock import patch
from PIL import Image
import numpy as np
import io
from app.main import app

client = TestClient(app)


def _sample_image() -> bytes:
    img = Image.new("RGB", (200, 200), color=(200, 180, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


def test_stats_empty():
    client.delete("/api/v1/cv/all")
    r = client.get("/api/v1/cv/stats")
    assert r.status_code == 200
    assert r.json()["registered_persons"] == 0


@patch("app.core.store.face_recognition.face_encodings",
       return_value=[np.random.rand(128).astype(np.float32)])
@patch("app.core.store.face_recognition.face_locations", return_value=[(10, 100, 90, 20)])
def test_register(mock_loc, mock_enc):
    client.delete("/api/v1/cv/all")
    r = client.post("/api/v1/cv/register",
        files={"file": ("alice.jpg", _sample_image(), "image/jpeg")},
        data={"name": "Alice"})
    assert r.status_code == 200
    assert r.json()["name"] == "Alice"
    assert r.json()["success"] is True


def test_register_empty_name():
    r = client.post("/api/v1/cv/register",
        files={"file": ("alice.jpg", _sample_image(), "image/jpeg")},
        data={"name": "  "})
    assert r.status_code == 400


def test_registry():
    r = client.get("/api/v1/cv/registry")
    assert r.status_code == 200
    assert "persons" in r.json()


def test_attendance():
    r = client.get("/api/v1/cv/attendance")
    assert r.status_code == 200
    assert "records" in r.json()


def test_clear():
    r = client.delete("/api/v1/cv/all")
    assert r.status_code == 200
