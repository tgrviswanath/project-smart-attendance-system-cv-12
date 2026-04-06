import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.core.store import register, recognize, get_registry, get_attendance, get_stats, clear_all
from app.core.validate import validate_image

router = APIRouter(prefix="/api/v1/cv", tags=["attendance"])


@router.post("/register")
async def register_person(name: str = Form(...), file: UploadFile = File(...)):
    if not name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    validate_image(file, content)
    try:
        result = await asyncio.get_running_loop().run_in_executor(None, register, name.strip(), content)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration error: {e}")
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["message"])
    return result


@router.post("/recognize")
async def recognize_faces(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    validate_image(file, content)
    try:
        return await asyncio.get_running_loop().run_in_executor(None, recognize, content)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recognition error: {e}")


@router.get("/registry")
def registry():
    return {"persons": get_registry()}


@router.get("/attendance")
def attendance():
    return {"records": get_attendance()}


@router.get("/stats")
def stats():
    return get_stats()


@router.delete("/all")
def clear():
    return clear_all()
