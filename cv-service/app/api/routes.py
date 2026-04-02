from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.core.store import register, recognize, get_registry, get_attendance, get_stats, clear_all

router = APIRouter(prefix="/api/v1/cv", tags=["attendance"])
ALLOWED = {"jpg", "jpeg", "png", "bmp", "webp"}


def _validate(filename: str):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"Unsupported format: .{ext}")


@router.post("/register")
async def register_person(name: str = Form(...), file: UploadFile = File(...)):
    if not name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    _validate(file.filename)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    result = register(name.strip(), content)
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["message"])
    return result


@router.post("/recognize")
async def recognize_faces(file: UploadFile = File(...)):
    _validate(file.filename)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    return recognize(content)


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
