# Project 12 - Smart Attendance System (CV)

Face recognition attendance system using face_recognition library + FAISS embeddings.

## Architecture

```
Frontend :3000  →  Backend :8000  →  CV Service :8001
  React/MUI        FastAPI/httpx      FastAPI/face_recognition/FAISS
```

## How It Works

```
Register: Upload face photo + name → 128-dim embedding → stored in FAISS
Recognize: Upload group photo → detect faces → nearest neighbor search → mark attendance
```

## What's New vs Previous Projects

| | P11 (Plant Disease) | P12 (Attendance) |
|---|---|---|
| Model | ResNet18 (trained) | face_recognition (pretrained dlib) |
| Index | None | FAISS 128-dim embeddings |
| State | Stateless | Stateful (registry + attendance log) |
| New concept | Transfer learning | Face embeddings + vector search |

## Local Run

```bash
# Terminal 1 - CV Service
cd cv-service && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Backend
cd backend && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 3 - Frontend
cd frontend && npm install && npm start
```

## Docker
```bash
docker-compose up --build
```

## Note
face_recognition requires cmake + dlib. On Windows install cmake first:
https://cmake.org/download/
