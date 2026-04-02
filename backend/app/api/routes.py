from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.core.service import (register_person, recognize_faces, get_registry,
                               get_attendance, get_stats, clear_all)
import httpx

router = APIRouter(prefix="/api/v1", tags=["attendance"])


def _handle(e):
    if isinstance(e, httpx.ConnectError):
        raise HTTPException(status_code=503, detail="CV service unavailable")
    if isinstance(e, httpx.HTTPStatusError):
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register(name: str = Form(...), file: UploadFile = File(...)):
    try:
        content = await file.read()
        return await register_person(name, file.filename, content,
                                     file.content_type or "image/jpeg")
    except Exception as e:
        _handle(e)


@router.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return await recognize_faces(file.filename, content,
                                     file.content_type or "image/jpeg")
    except Exception as e:
        _handle(e)


@router.get("/registry")
async def registry():
    try:
        return await get_registry()
    except Exception as e:
        _handle(e)


@router.get("/attendance")
async def attendance():
    try:
        return await get_attendance()
    except Exception as e:
        _handle(e)


@router.get("/stats")
async def stats():
    try:
        return await get_stats()
    except Exception as e:
        _handle(e)


@router.delete("/all")
async def clear():
    try:
        return await clear_all()
    except Exception as e:
        _handle(e)
