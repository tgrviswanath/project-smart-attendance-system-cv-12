# GCP Deployment Guide — Project CV-12 Smart Attendance System

---

## GCP Services for Smart Attendance

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Cloud Vision API**                 | Detect faces and return face landmarks for matching                          | Face detection preprocessing step                 |
| **Vertex AI Face Recognition**       | Face enrollment and identification via Vertex AI Vision                      | Replace your face_recognition + FAISS pipeline     |
| **Firestore**                        | Store attendance logs with timestamps, employee metadata                     | Replace your in-memory attendance log              |

> **Cloud Vision API + Firestore** with custom face embedding matching replaces your face_recognition + FAISS pipeline. For production, use **Vertex AI** for managed face recognition.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Cloud Run**              | Run backend + cv-service containers — serverless, scales to zero    | Best match for your current microservice architecture |
| **Artifact Registry**      | Store your Docker images                                            | Used with Cloud Run or GKE                            |

### 3. Supporting Services

| Service                        | Purpose                                                                   |
|--------------------------------|---------------------------------------------------------------------------|
| **Firestore**                  | Store attendance logs, employee registry, and session records             |
| **Cloud Storage**              | Store employee face photos and attendance reports                         |
| **Secret Manager**             | Store API keys and connection strings instead of .env files               |
| **Cloud Monitoring + Logging** | Track recognition latency, attendance counts, request volume              |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Firebase Hosting — React Frontend                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Cloud Run — Backend (FastAPI :8000)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal HTTPS
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Cloud Run         │    │ Cloud Vision API + Firestore       │
│ CV Service :8001  │    │ Face detection + attendance log    │
│ face_recognition  │    │ No dlib/cmake install needed       │
│ + FAISS           │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
gcloud auth login
gcloud projects create attendance-cv-project --name="Smart Attendance"
gcloud config set project attendance-cv-project
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com vision.googleapis.com \
  firestore.googleapis.com storage.googleapis.com cloudbuild.googleapis.com
```

---

## Step 1 — Create Artifact Registry and Push Images

```bash
GCP_REGION=europe-west2
gcloud artifacts repositories create attendance-repo \
  --repository-format=docker --location=$GCP_REGION
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
AR=$GCP_REGION-docker.pkg.dev/attendance-cv-project/attendance-repo
docker build -f docker/Dockerfile.cv-service -t $AR/cv-service:latest ./cv-service
docker push $AR/cv-service:latest
docker build -f docker/Dockerfile.backend -t $AR/backend:latest ./backend
docker push $AR/backend:latest
```

---

## Step 2 — Create Firestore for Attendance Logs

```bash
gcloud firestore databases create --location=europe-west2
```

---

## Step 3 — Deploy to Cloud Run

```bash
gcloud run deploy cv-service \
  --image $AR/cv-service:latest --region $GCP_REGION \
  --port 8001 --no-allow-unauthenticated \
  --min-instances 1 --max-instances 3 --memory 2Gi --cpu 1

CV_URL=$(gcloud run services describe cv-service --region $GCP_REGION --format "value(status.url)")

gcloud run deploy backend \
  --image $AR/backend:latest --region $GCP_REGION \
  --port 8000 --allow-unauthenticated \
  --min-instances 1 --max-instances 5 --memory 1Gi --cpu 1 \
  --set-env-vars CV_SERVICE_URL=$CV_URL
```

---

## Option B — Use Cloud Vision API + Firestore

```python
from google.cloud import vision, firestore
from datetime import datetime
import numpy as np

vision_client = vision.ImageAnnotatorClient()
db = firestore.Client()

def register_employee(employee_id: str, name: str, image_bytes: bytes) -> dict:
    image = vision.Image(content=image_bytes)
    response = vision_client.face_detection(image=image)
    if not response.face_annotations:
        return {"error": "No face detected"}
    # Store face landmarks as embedding proxy
    face = response.face_annotations[0]
    landmarks = {l.type_.name: {"x": l.position.x, "y": l.position.y} for l in face.landmarks}
    db.collection("employees").document(employee_id).set({"name": name, "landmarks": landmarks, "employee_id": employee_id})
    return {"employee_id": employee_id, "name": name}

def mark_attendance(employee_id: str, name: str) -> dict:
    db.collection("attendance").add({"employee_id": employee_id, "name": name, "timestamp": datetime.utcnow().isoformat()})
    return {"marked": True, "employee_id": employee_id, "timestamp": datetime.utcnow().isoformat()}
```

---

## Estimated Monthly Cost

| Service                    | Tier                  | Est. Cost          |
|----------------------------|-----------------------|--------------------|
| Cloud Run (backend)        | 1 vCPU / 1 GB         | ~$10–15/month      |
| Cloud Run (cv-service)     | 1 vCPU / 2 GB         | ~$12–18/month      |
| Artifact Registry          | Storage               | ~$1–2/month        |
| Firebase Hosting           | Free tier             | $0                 |
| Cloud Vision API           | 1k units free/month   | $0 (free tier)     |
| Firestore                  | Pay per operation     | ~$1–3/month        |
| **Total (Option A)**       |                       | **~$24–38/month**  |
| **Total (Option B)**       |                       | **~$12–20/month**  |

For exact estimates → https://cloud.google.com/products/calculator

---

## Teardown

```bash
gcloud run services delete backend --region $GCP_REGION --quiet
gcloud run services delete cv-service --region $GCP_REGION --quiet
gcloud artifacts repositories delete attendance-repo --location=$GCP_REGION --quiet
gcloud projects delete attendance-cv-project
```
