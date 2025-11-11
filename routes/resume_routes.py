# routes/resume_routes.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import uuid
from io import BytesIO
import os
from models.meta import load_meta, save_meta
from config import RESUME_META

# === LAZY LOAD SERVICES ONLY WHEN NEEDED ===
_text_extractor = None
_preprocessor = None
_encoder = None

def get_text_extractor():
    global _text_extractor
    if _text_extractor is None:
        print("Loading text extractor (spaCy + pdfminer)...")
        from services.text_processing import extract_text_from_pdf_bytes
        _text_extractor = extract_text_from_pdf_bytes
    return _text_extractor

def get_preprocessor():
    global _preprocessor
    if _preprocessor is None:
        print("Loading text preprocessor (spaCy)...")
        from services.text_processing import preprocess_text
        _preprocessor = preprocess_text
    return _preprocessor

def get_encoder():
    global _encoder
    if _encoder is None:
        print("Loading embedding encoder...")
        from services.embedding import encode_text
        _encoder = encode_text
    return _encoder

# === DIRECTORY SETUP ===
RESUMES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "resumes")
RESUMES_DIR = os.path.abspath(RESUMES_DIR)
os.makedirs(RESUMES_DIR, exist_ok=True)  # Ensure dir exists

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

    # === LAZY LOAD ONLY NOW ===
    extract_text = get_text_extractor()
    preprocess = get_preprocessor()
    encode = get_encoder()

    text = extract_text(BytesIO(content))
    processed = preprocess(text)
    embedding = encode(processed)

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