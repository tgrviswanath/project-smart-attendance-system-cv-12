# AWS Deployment Guide — Project CV-12 Smart Attendance System

---

## AWS Services for Smart Attendance

### 1. Ready-to-Use AI (No Model Needed)

| Service                    | What it does                                                                 | When to use                                        |
|----------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Amazon Rekognition**     | Face collection, indexing, and search — replace face_recognition + FAISS     | Replace your entire face embedding pipeline        |
| **Amazon Rekognition**     | IndexFaces, SearchFacesByImage — persistent face registry in the cloud       | When you need durable face registry storage        |
| **Amazon DynamoDB**        | Store attendance logs with timestamps, employee metadata                     | Replace your in-memory attendance log              |

> **Amazon Rekognition Face Collections** is the direct replacement for your face_recognition + FAISS pipeline. It handles face indexing, search, and matching — no dlib/cmake install needed.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **AWS App Runner**         | Run backend container — simplest, no VPC or cluster needed          | Quickest path to production                           |
| **Amazon ECS Fargate**     | Run backend + cv-service containers in a private VPC                | Best match for your current microservice architecture |
| **Amazon ECR**             | Store your Docker images                                            | Used with App Runner, ECS, or EKS                     |

### 3. Supporting Services

| Service                  | Purpose                                                                   |
|--------------------------|---------------------------------------------------------------------------|
| **Amazon DynamoDB**      | Store attendance logs, employee registry, and session records             |
| **Amazon S3**            | Store employee face photos and attendance reports                         |
| **AWS Secrets Manager**  | Store API keys and connection strings instead of .env files               |
| **Amazon CloudWatch**    | Track recognition latency, attendance counts, request volume              |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  S3 + CloudFront — React Frontend                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  AWS App Runner / ECS Fargate — Backend (FastAPI :8000)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ ECS Fargate       │    │ Amazon Rekognition Face Collection │
│ CV Service :8001  │    │ + DynamoDB attendance log          │
│ face_recognition  │    │ No dlib/cmake install needed       │
│ + FAISS           │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
aws configure
AWS_REGION=eu-west-2
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
```

---

## Step 1 — Create ECR and Push Images

```bash
aws ecr create-repository --repository-name attendance/cv-service --region $AWS_REGION
aws ecr create-repository --repository-name attendance/backend --region $AWS_REGION
ECR=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR
docker build -f docker/Dockerfile.cv-service -t $ECR/attendance/cv-service:latest ./cv-service
docker push $ECR/attendance/cv-service:latest
docker build -f docker/Dockerfile.backend -t $ECR/attendance/backend:latest ./backend
docker push $ECR/attendance/backend:latest
```

---

## Step 2 — Create Rekognition Face Collection and DynamoDB

```bash
# Create face collection
aws rekognition create-collection --collection-id attendance-faces --region $AWS_REGION

# Create DynamoDB table for attendance
aws dynamodb create-table \
  --table-name attendance-log \
  --attribute-definitions AttributeName=employee_id,AttributeType=S AttributeName=timestamp,AttributeType=S \
  --key-schema AttributeName=employee_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION
```

---

## Step 3 — Deploy with App Runner

```bash
aws apprunner create-service \
  --service-name attendance-backend \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR'/attendance/backend:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "CV_SERVICE_URL": "http://cv-service:8001"
        }
      }
    }
  }' \
  --instance-configuration '{"Cpu": "1 vCPU", "Memory": "2 GB"}' \
  --region $AWS_REGION
```

---

## Option B — Use Amazon Rekognition Face Collections

```python
import boto3
from datetime import datetime

rekognition = boto3.client("rekognition", region_name="eu-west-2")
dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
table = dynamodb.Table("attendance-log")

COLLECTION_ID = "attendance-faces"

def register_employee(employee_id: str, name: str, image_bytes: bytes) -> dict:
    response = rekognition.index_faces(
        CollectionId=COLLECTION_ID,
        Image={"Bytes": image_bytes},
        ExternalImageId=f"{employee_id}#{name}",
        DetectionAttributes=["DEFAULT"]
    )
    return {"face_id": response["FaceRecords"][0]["Face"]["FaceId"], "employee_id": employee_id}

def recognize_and_mark(image_bytes: bytes) -> dict:
    response = rekognition.search_faces_by_image(
        CollectionId=COLLECTION_ID,
        Image={"Bytes": image_bytes},
        MaxFaces=5,
        FaceMatchThreshold=80
    )
    results = []
    for match in response["FaceMatches"]:
        ext_id = match["Face"]["ExternalImageId"]
        employee_id, name = ext_id.split("#", 1)
        table.put_item(Item={"employee_id": employee_id, "timestamp": datetime.utcnow().isoformat(), "name": name})
        results.append({"employee_id": employee_id, "name": name, "confidence": round(match["Similarity"], 2)})
    return {"recognized": results, "count": len(results)}
```

---

## Estimated Monthly Cost

| Service                    | Tier              | Est. Cost          |
|----------------------------|-------------------|--------------------|
| App Runner (backend)       | 1 vCPU / 2 GB     | ~$20–25/month      |
| App Runner (cv-service)    | 1 vCPU / 2 GB     | ~$20–25/month      |
| ECR + S3 + CloudFront      | Standard          | ~$3–7/month        |
| Rekognition Face Search    | Pay per image     | ~$1/1000 images    |
| DynamoDB                   | On-demand         | ~$1–3/month        |
| **Total (Option A)**       |                   | **~$43–57/month**  |
| **Total (Option B)**       |                   | **~$24–35/month**  |

For exact estimates → https://calculator.aws

---

## Teardown

```bash
aws rekognition delete-collection --collection-id attendance-faces --region $AWS_REGION
aws dynamodb delete-table --table-name attendance-log --region $AWS_REGION
aws ecr delete-repository --repository-name attendance/backend --force
aws ecr delete-repository --repository-name attendance/cv-service --force
```
