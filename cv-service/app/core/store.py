"""
Face embedding store using face_recognition + FAISS.
- Register: encode face → store 128-dim embedding in FAISS
- Recognize: encode query face → nearest neighbor search → return person name
- Attendance: track who was seen and when (in-memory)
"""
import face_recognition
import faiss
import numpy as np
from PIL import Image
import io
import base64
import cv2
from datetime import datetime
from app.core.config import settings

# Registry: {id: {name, embedding, thumbnail}}
_registry: dict[int, dict] = {}
_index: faiss.IndexFlatL2 | None = None
_id_map: list[int] = []   # maps FAISS index position → registry id

# Attendance log: [{person_id, name, timestamp}]
_attendance: list[dict] = []


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


def _get_index() -> faiss.IndexFlatL2:
    global _index
    if _index is None:
        _index = faiss.IndexFlatL2(128)   # 128-dim face embeddings
    return _index


def register(name: str, image_bytes: bytes) -> dict:
    img = _load_image(image_bytes)
    encodings = face_recognition.face_encodings(img)
    if not encodings:
        return {"success": False, "message": "No face detected in image"}

    embedding = np.array(encodings[0], dtype=np.float32).reshape(1, -1)
    person_id = len(_registry)
    thumbnail = _make_thumbnail(image_bytes)

    _registry[person_id] = {"name": name, "embedding": embedding, "thumbnail": thumbnail}
    _get_index().add(embedding)
    _id_map.append(person_id)

    return {"success": True, "person_id": person_id, "name": name,
            "total_registered": len(_registry)}


def recognize(image_bytes: bytes) -> dict:
    if not _registry:
        return {"recognized": [], "unknown_count": 0, "annotated_image": None}

    img = _load_image(image_bytes)
    face_locations = face_recognition.face_locations(img)
    face_encodings = face_recognition.face_encodings(img, face_locations)

    annotated = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    recognized = []
    unknown_count = 0

    for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
        query = np.array(encoding, dtype=np.float32).reshape(1, -1)
        distances, indices = _get_index().search(query, 1)
        dist = float(distances[0][0])
        idx = int(indices[0][0])

        # L2 distance threshold (128-dim, tolerance ~0.5 → L2 ~0.25)
        threshold = settings.RECOGNITION_TOLERANCE ** 2 * 128

        if dist < threshold and idx < len(_id_map):
            person_id = _id_map[idx]
            person = _registry[person_id]
            name = person["name"]
            color = (0, 255, 0)

            # Log attendance
            _attendance.append({
                "person_id": person_id,
                "name": name,
                "timestamp": datetime.now().isoformat(),
            })
            recognized.append({"name": name, "person_id": person_id,
                                "distance": round(dist, 4)})
        else:
            name = "Unknown"
            color = (0, 0, 255)
            unknown_count += 1

        cv2.rectangle(annotated, (left, top), (right, bottom), color, 2)
        cv2.putText(annotated, name, (left, top - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    annotated_b64 = base64.b64encode(buf).decode("utf-8")

    return {
        "recognized": recognized,
        "unknown_count": unknown_count,
        "face_count": len(face_locations),
        "annotated_image": annotated_b64,
    }


def get_registry() -> list[dict]:
    return [{"person_id": pid, "name": p["name"], "thumbnail": p["thumbnail"]}
            for pid, p in _registry.items()]


def get_attendance() -> list[dict]:
    return list(reversed(_attendance))


def get_stats() -> dict:
    return {
        "registered_persons": len(_registry),
        "attendance_records": len(_attendance),
        "tolerance": settings.RECOGNITION_TOLERANCE,
    }


def clear_all() -> dict:
    global _index, _id_map
    _registry.clear()
    _attendance.clear()
    _index = None
    _id_map = []
    return {"message": "All data cleared"}
