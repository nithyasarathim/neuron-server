from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import uuid
from io import BytesIO
import os
from models.meta import load_meta, save_meta
from services.text_processing import extract_text_from_pdf_bytes, preprocess_text
from services.embedding import encode_text
from config import RESUME_META

RESUMES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "resumes")
RESUMES_DIR = os.path.abspath(RESUMES_DIR)

router = APIRouter()

@router.post("/upload/resume")
async def upload_resume(
    user_id: str = Form(...),
    username: str = Form(...),
    resume: UploadFile = File(...)
):
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF resumes allowed.")

    meta = load_meta(RESUME_META)

    # Remove old resume if exists
    existing_id = next(
        (rid for rid, entry in meta.items() if entry["username"].lower() == username.lower()), 
        None
    )
    if existing_id:
        old_path = os.path.join(RESUMES_DIR, meta[existing_id]["filename"])
        if os.path.exists(old_path):
            os.remove(old_path)
        del meta[existing_id]

    resume_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(resume.filename)[1] or ".pdf"
    filename = f"{resume_id}{ext}"
    path = os.path.join(RESUMES_DIR, filename)
    
    content = await resume.read()
    with open(path, "wb") as f:
        f.write(content)

    text = extract_text_from_pdf_bytes(BytesIO(content))
    processed = preprocess_text(text)
    embedding = encode_text(processed)

    meta[resume_id] = {
        "id": resume_id,
        "user_id": user_id,
        "username": username,
        "filename": filename,
        "text": processed,
        "embedding": embedding
    }
    save_meta(RESUME_META, meta)
    return {"resume_id": resume_id}

@router.get("/resume/{resume_id}")
async def get_resume(resume_id: str):
    meta = load_meta(RESUME_META)

    if resume_id not in meta:
        raise HTTPException(status_code=404, detail="Resume not found.")

    file_path = os.path.join(RESUMES_DIR, meta[resume_id]["filename"])
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Resume file missing on server.")

    return FileResponse(
        file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={meta[resume_id]['filename']}"}
    )
