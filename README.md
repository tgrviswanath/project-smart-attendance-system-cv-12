# Project CV-12 - Smart Attendance System

Microservice CV system that performs face recognition attendance using the face_recognition library + FAISS embeddings. Register faces once, then recognize them in group photos to mark attendance automatically.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND  (React - Port 3000)                              │
│  axios POST /api/v1/register  |  POST /api/v1/recognize     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP JSON
┌──────────────────────▼──────────────────────────────────────┐
│  BACKEND  (FastAPI - Port 8000)                             │
│  httpx → cv-service                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP JSON
┌──────────────────────▼──────────────────────────────────────┐
│  CV SERVICE  (FastAPI - Port 8001)                          │
│  Register: face photo → 128-dim embedding → FAISS index     │
│  Recognize: group photo → detect faces → nearest neighbor   │
│  Returns { recognized[], attendance_log[] }                 │
└─────────────────────────────────────────────────────────────┘
```

---

## How It Works

```
Register: Upload face photo + name → 128-dim embedding → stored in FAISS
Recognize: Upload group photo → detect faces → nearest neighbor search → mark attendance
```

---

## What's New vs Previous Projects

| | CV-11 (Plant Disease) | CV-12 (Attendance) |
|---|---|---|
| Model | ResNet18 (trained) | face_recognition (pretrained dlib) |
| Index | None | FAISS 128-dim embeddings |
| State | Stateless | Stateful (registry + attendance log) |
| New concept | Transfer learning | Face embeddings + vector search |

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Frontend | React, MUI |
| Backend | FastAPI, httpx |
| CV | face_recognition (dlib), FAISS, OpenCV |
| Index | FAISS IndexFlatL2 (128-dim) |
| Deployment | Docker, docker-compose |

---

## Prerequisites

- Python 3.12+
- Node.js — run `nvs use 20.14.0` before starting the frontend
- **cmake** required for dlib (face_recognition dependency):
  - Windows: https://cmake.org/download/
  - Ubuntu: `sudo apt-get install cmake`

---

## Local Run

### Step 1 — Start CV Service (Terminal 1)

```bash
cd cv-service
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Verify: http://localhost:8001/health → `{"status":"ok"}`

### Step 2 — Start Backend (Terminal 2)

```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Step 3 — Start Frontend (Terminal 3)

```bash
cd frontend
npm install && npm start
```

Opens at: http://localhost:3000

---

## Environment Files

### `backend/.env`

```
APP_NAME=Smart Attendance API
APP_VERSION=1.0.0
ALLOWED_ORIGINS=["http://localhost:3000"]
CV_SERVICE_URL=http://localhost:8001
```

### `frontend/.env`

```
REACT_APP_API_URL=http://localhost:8000
```

---

## Docker Run

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API docs | http://localhost:8000/docs |
| CV Service docs | http://localhost:8001/docs |

---

## Run Tests

```bash
cd cv-service && venv\Scripts\activate
pytest ../tests/cv-service/ -v

cd backend && venv\Scripts\activate
pytest ../tests/backend/ -v
```

---

## Project Structure

```
project-smart-attendance-system-cv-12/
├── frontend/                    ← React (Port 3000)
├── backend/                     ← FastAPI (Port 8000)
├── cv-service/                  ← FastAPI CV (Port 8001)
│   └── app/
│       ├── api/routes.py
│       ├── core/registry.py     ← FAISS face registry
│       ├── core/recognizer.py   ← face_recognition + nearest neighbor
│       ├── core/attendance.py   ← attendance log management
│       └── main.py
├── samples/
├── tests/
├── docker/
└── docker-compose.yml
```

---

## API Reference

```
POST /api/v1/register
Body:     { "image": "<base64>", "name": "John Smith", "employee_id": "E001" }
Response: { "registered": true, "employee_id": "E001", "registry_size": 5 }

POST /api/v1/recognize
Body:     { "image": "<base64>" }
Response: {
  "recognized": [{ "employee_id": "E001", "name": "John Smith", "confidence": 94.2 }],
  "attendance_log": [{ "employee_id": "E001", "name": "John Smith", "timestamp": "2024-01-15T09:00:00" }]
}

GET /api/v1/attendance
Response: { "log": [...], "total": 12 }

DELETE /api/v1/registry
Response: { "cleared": true }
```
