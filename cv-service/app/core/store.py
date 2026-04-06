"""
Persistent face embedding store using face_recognition + FAISS.
- FAISS index saved to disk (data/faces.faiss)
- Registry metadata saved to JSON (data/registry.json)
- Attendance log saved to JSON (data/attendance.json)
- Survives service restarts
"""
import face_recognition
import faiss
import numpy as np
from PIL import Image
import io
import base64
import cv2
import json
import os
from datetime import datetime
from app.core.config import settings

INDEX_PATH      = "data/faces.faiss"
REGISTRY_PATH   = "data/registry.json"
ATTENDANCE_PATH = "data/attendance.json"

_index: faiss.IndexFlatL2 | None = None
_registry: dict[int, dict] = {}
_id_map: list[int] = []
_attendance: list[dict] = []


def _ensure_dir():
    os.makedirs("data", exist_ok=True)


def _load():
    global _index, _registry, _id_map, _attendance
    _ensure_dir()
    if os.path.exists(INDEX_PATH) and os.path.exists(REGISTRY_PATH):
        _index = faiss.read_index(INDEX_PATH)
        with open(REGISTRY_PATH, "r") as f:
            data = json.load(f)
            _registry = {int(k): v for k, v in data["registry"].items()}
            _id_map = data["id_map"]
    else:
        _index = faiss.IndexFlatL2(128)
        _registry = {}
        _id_map = []
    if os.path.exists(ATTENDANCE_PATH):
        with open(ATTENDANCE_PATH, "r") as f:
            _attendance = json.load(f)
    else:
        _attendance = []


def _get_index() -> faiss.IndexFlatL2:
    global _index
    if _index is None:
        _load()
    return _index


def _save_index():
    _ensure_dir()
    faiss.write_index(_get_index(), INDEX_PATH)
    with open(REGISTRY_PATH, "w") as f:
        json.dump({"registry": _registry, "id_map": _id_map}, f)


def _save_attendance():
    _ensure_dir()
    with open(ATTENDANCE_PATH, "w") as f:
        json.dump(_attendance, f)


def _load_image(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    if max(w, h) > settings.MAX_IMAGE_SIZE:
        scale = settings.MAX_IMAGE_SIZE / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    return np.array(img)


def _make_thumbnail(image_bytes: bytes, size: int = 80) -> str:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((size, size))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def register(name: str, image_bytes: bytes) -> dict:
    img = _load_image(image_bytes)
    encodings = face_recognition.face_encodings(img)
    if not encodings:
        return {"success": False, "message": "No face detected in image"}
    embedding = np.array(encodings[0], dtype=np.float32).reshape(1, -1)
    person_id = len(_registry)
    thumbnail = _make_thumbnail(image_bytes)
    _registry[person_id] = {"name": name, "thumbnail": thumbnail}
    _get_index().add(embedding)
    _id_map.append(person_id)
    _save_index()
    return {"success": True, "person_id": person_id, "name": name,
            "total_registered": len(_registry)}


def recognize(image_bytes: bytes) -> dict:
    if not _registry:
        return {"recognized": [], "unknown_count": 0, "face_count": 0, "annotated_image": None}
    img = _load_image(image_bytes)
    face_locations = face_recognition.face_locations(img)
    face_encodings = face_recognition.face_encodings(img, face_locations)
    annotated = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    recognized = []
    unknown_count = 0
    threshold = settings.RECOGNITION_TOLERANCE ** 2 * 128
    for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
        query = np.array(encoding, dtype=np.float32).reshape(1, -1)
        distances, indices = _get_index().search(query, 1)
        dist = float(distances[0][0])
        idx = int(indices[0][0])
        if dist < threshold and idx < len(_id_map):
            person_id = _id_map[idx]
            person = _registry[person_id]
            name = person["name"]
            color = (0, 255, 0)
            _attendance.append({"person_id": person_id, "name": name,
                                 "timestamp": datetime.now().isoformat()})
            _save_attendance()
            recognized.append({"name": name, "person_id": person_id, "distance": round(dist, 4)})
        else:
            name = "Unknown"
            color = (0, 0, 255)
            unknown_count += 1
        cv2.rectangle(annotated, (left, top), (right, bottom), color, 2)
        cv2.putText(annotated, name, (left, top - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return {"recognized": recognized, "unknown_count": unknown_count,
            "face_count": len(face_locations),
            "annotated_image": base64.b64encode(buf).decode("utf-8")}


def get_registry() -> list[dict]:
    return [{"person_id": pid, "name": p["name"], "thumbnail": p["thumbnail"]}
            for pid, p in _registry.items()]


def get_attendance() -> list[dict]:
    return list(reversed(_attendance))


def get_stats() -> dict:
    return {"registered_persons": len(_registry),
            "attendance_records": len(_attendance),
            "tolerance": settings.RECOGNITION_TOLERANCE}


def clear_all() -> dict:
    global _index, _id_map
    _registry.clear()
    _attendance.clear()
    _index = None
    _id_map = []
    _ensure_dir()
    for path in (INDEX_PATH, REGISTRY_PATH, ATTENDANCE_PATH):
        if os.path.exists(path):
            os.remove(path)
    return {"message": "All data cleared"}
