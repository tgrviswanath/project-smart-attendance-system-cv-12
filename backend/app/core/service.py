import httpx
from app.core.config import settings

CV_URL = settings.CV_SERVICE_URL


async def register_person(name: str, filename: str, content: bytes, content_type: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{CV_URL}/api/v1/cv/register",
                              files={"file": (filename, content, content_type)},
                              data={"name": name}, timeout=30.0)
        r.raise_for_status()
        return r.json()


async def recognize_faces(filename: str, content: bytes, content_type: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{CV_URL}/api/v1/cv/recognize",
                              files={"file": (filename, content, content_type)}, timeout=30.0)
        r.raise_for_status()
        return r.json()


async def get_registry() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{CV_URL}/api/v1/cv/registry", timeout=10.0)
        r.raise_for_status()
        return r.json()


async def get_attendance() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{CV_URL}/api/v1/cv/attendance", timeout=10.0)
        r.raise_for_status()
        return r.json()


async def get_stats() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{CV_URL}/api/v1/cv/stats", timeout=10.0)
        r.raise_for_status()
        return r.json()


async def clear_all() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{CV_URL}/api/v1/cv/all", timeout=10.0)
        r.raise_for_status()
        return r.json()
