# Azure Deployment Guide — Project CV-12 Smart Attendance System

---

## Azure Services for Smart Attendance

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Azure AI Face API — Person Group** | Face enrollment, indexing, and identification — replace face_recognition + FAISS | Replace your entire face embedding pipeline    |
| **Azure AI Face API — Identify**     | Match faces against enrolled person group — persistent face registry         | When you need durable face registry storage        |
| **Azure Cosmos DB**                  | Store attendance logs with timestamps, employee metadata                     | Replace your in-memory attendance log              |

> **Azure AI Face API Person Groups** is the direct replacement for your face_recognition + FAISS pipeline. It handles face enrollment, training, and identification — no dlib/cmake install needed.

### 2. Host Your Own Model (Keep Current Stack)

| Service                        | What it does                                                        | When to use                                           |
|--------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Azure Container Apps**       | Run your 3 Docker containers (frontend, backend, cv-service)        | Best match for your current microservice architecture |
| **Azure Container Registry**   | Store your Docker images                                            | Used with Container Apps or AKS                       |

### 3. Supporting Services

| Service                       | Purpose                                                                  |
|-------------------------------|--------------------------------------------------------------------------|
| **Azure Cosmos DB**           | Store attendance logs, employee registry, and session records            |
| **Azure Blob Storage**        | Store employee face photos and attendance reports                        |
| **Azure Key Vault**           | Store API keys and connection strings instead of .env files              |
| **Azure Monitor + App Insights** | Track recognition latency, attendance counts, request volume         |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Static Web Apps — React Frontend                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Azure Container Apps — Backend (FastAPI :8000)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Container Apps    │    │ Azure AI Face API Person Group     │
│ CV Service :8001  │    │ + Cosmos DB attendance log         │
│ face_recognition  │    │ No dlib/cmake install needed       │
│ + FAISS           │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
az login
az group create --name rg-smart-attendance --location uksouth
az extension add --name containerapp --upgrade
```

---

## Step 1 — Create Container Registry and Push Images

```bash
az acr create --resource-group rg-smart-attendance --name attendanceacr --sku Basic --admin-enabled true
az acr login --name attendanceacr
ACR=attendanceacr.azurecr.io
docker build -f docker/Dockerfile.cv-service -t $ACR/cv-service:latest ./cv-service
docker push $ACR/cv-service:latest
docker build -f docker/Dockerfile.backend -t $ACR/backend:latest ./backend
docker push $ACR/backend:latest
```

---

## Step 2 — Create Cosmos DB for Attendance Logs

```bash
az cosmosdb create --name attendance-db --resource-group rg-smart-attendance --kind GlobalDocumentDB --locations regionName=uksouth
az cosmosdb sql database create --account-name attendance-db --resource-group rg-smart-attendance --name attendance
az cosmosdb sql container create --account-name attendance-db --resource-group rg-smart-attendance \
  --database-name attendance --name logs --partition-key-path /employee_id
```

---

## Step 3 — Deploy Container Apps

```bash
az containerapp env create --name attendance-env --resource-group rg-smart-attendance --location uksouth

az containerapp create \
  --name cv-service --resource-group rg-smart-attendance \
  --environment attendance-env --image $ACR/cv-service:latest \
  --registry-server $ACR --target-port 8001 --ingress internal \
  --min-replicas 1 --max-replicas 3 --cpu 1 --memory 2.0Gi

az containerapp create \
  --name backend --resource-group rg-smart-attendance \
  --environment attendance-env --image $ACR/backend:latest \
  --registry-server $ACR --target-port 8000 --ingress external \
  --min-replicas 1 --max-replicas 5 --cpu 0.5 --memory 1.0Gi \
  --env-vars CV_SERVICE_URL=http://cv-service:8001
```

---

## Option B — Use Azure AI Face API Person Groups

```python
from azure.ai.vision.face import FaceClient, FaceAdministrationClient
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient
from datetime import datetime

face_client = FaceClient(endpoint=os.getenv("AZURE_FACE_ENDPOINT"), credential=AzureKeyCredential(os.getenv("AZURE_FACE_KEY")))
admin_client = FaceAdministrationClient(endpoint=os.getenv("AZURE_FACE_ENDPOINT"), credential=AzureKeyCredential(os.getenv("AZURE_FACE_KEY")))
cosmos_container = CosmosClient(os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY")).get_database_client("attendance").get_container_client("logs")

GROUP_ID = "attendance-group"

def register_employee(employee_id: str, name: str, image_bytes: bytes) -> dict:
    person = admin_client.large_person_group.create_person(GROUP_ID, name=name, user_data=employee_id)
    admin_client.large_person_group.add_face(GROUP_ID, person.person_id, image_content=image_bytes)
    admin_client.large_person_group.train(GROUP_ID)
    return {"person_id": str(person.person_id), "employee_id": employee_id}

def recognize_and_mark(image_bytes: bytes) -> dict:
    detected = face_client.detect(image_content=image_bytes, detection_model="detection_03")
    if not detected:
        return {"recognized": [], "count": 0}
    face_ids = [str(f.face_id) for f in detected]
    identified = face_client.identify_from_large_person_group(face_ids=face_ids, large_person_group_id=GROUP_ID)
    results = []
    for result in identified:
        if result.candidates:
            top = result.candidates[0]
            person = admin_client.large_person_group.get_person(GROUP_ID, top.person_id)
            cosmos_container.upsert_item({"id": f"{person.user_data}-{datetime.utcnow().isoformat()}", "employee_id": person.user_data, "name": person.name, "timestamp": datetime.utcnow().isoformat()})
            results.append({"employee_id": person.user_data, "name": person.name, "confidence": round(top.confidence * 100, 2)})
    return {"recognized": results, "count": len(results)}
```

---

## Estimated Monthly Cost

| Service                  | Tier      | Est. Cost         |
|--------------------------|-----------|-------------------|
| Container Apps (backend) | 0.5 vCPU  | ~$10–15/month     |
| Container Apps (cv-svc)  | 1 vCPU    | ~$15–20/month     |
| Container Registry       | Basic     | ~$5/month         |
| Static Web Apps          | Free      | $0                |
| Azure AI Face API        | F0 free   | $0 (30k calls)    |
| Cosmos DB                | Serverless| ~$1–3/month       |
| **Total (Option A)**     |           | **~$31–43/month** |
| **Total (Option B)**     |           | **~$16–23/month** |

For exact estimates → https://calculator.azure.com

---

## Teardown

```bash
az group delete --name rg-smart-attendance --yes --no-wait
```
