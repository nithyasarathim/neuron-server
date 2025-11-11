from fastapi import APIRouter, Form, Query, HTTPException
import uuid
import os
from models.meta import load_meta, save_meta
from services.text_processing import preprocess_text
from services.embedding import encode_text, compute_similarity, score_label
from config import JDS_DIR, JD_META, RESUME_META

router = APIRouter()

@router.get("/job/{job_id}")
async def get_job(job_id: str):
    jd_meta = load_meta(JD_META)
    if job_id not in jd_meta:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    
    job_data = jd_meta[job_id]
    return {
        "job_id": job_data["id"],
        "company": job_data["company"],
        "job_title": job_data["job_title"],
        "description": job_data.get("description"),
        "location": job_data.get("location"),
        "salary": job_data.get("salary"),
        "skills_required": job_data.get("skills_required"),
        "experience": job_data.get("experience"),
        "job_type": job_data.get("job_type"),
        "filename": job_data.get("filename"),
        "key": job_data.get("key")
    }

@router.get("/jobs")
async def get_all_jobs(key: str = Query(..., description="API key to filter jobs")):
    jd_meta = load_meta(JD_META)
    jobs_list = [
        {
            "job_id": job_data["id"],
            "company": job_data["company"],
            "job_title": job_data["job_title"],
            "description": job_data.get("description"),
            "location": job_data.get("location"),
            "salary": job_data.get("salary"),
            "skills_required": job_data.get("skills_required"),
            "experience": job_data.get("experience"),
            "job_type": job_data.get("job_type"),
            "filename": job_data.get("filename"),
            "key": job_data.get("key")
        }
        for job_data in jd_meta.values()
        if job_data.get("key") == key
    ]

    return {"jobs": jobs_list, "count": len(jobs_list)}

@router.post("/upload/jobs")
async def upload_job(
    company: str = Form(...),
    job_title: str = Form(...),
    description: str = Form(...),
    key: str = Form(..., description="API key for this job"),
    location: str = Form(None),
    salary: str = Form(None),
    skills_required: str = Form(None),
    experience: str = Form(None),
    job_type: str = Form(None),
):
    meta = load_meta(JD_META)
    job_id = str(uuid.uuid4())[:8]
    filename = f"{job_id}.txt"
    path = os.path.join(JDS_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(description)

    processed = preprocess_text(description)
    embedding = encode_text(processed)

    meta[job_id] = {
        "id": job_id,
        "company": company,
        "job_title": job_title,
        "description": description,
        "location": location,
        "salary": salary,
        "skills_required": skills_required,
        "experience": experience,
        "job_type": job_type,
        "filename": filename,
        "text": processed,
        "embedding": embedding,
        "key": key,  # Store the key here
    }

    save_meta(JD_META, meta)

    return {"job_id": job_id, "message": "Job uploaded successfully."}

@router.get("/match/candidates")
async def match_candidates(jobid: str, count: int = Query(5, gt=0)):
    jd_meta = load_meta(JD_META)
    res_meta = load_meta(RESUME_META)

    if jobid not in jd_meta:
        raise HTTPException(status_code=404, detail="Job ID not found.")

    jd_emb = jd_meta[jobid]["embedding"]
    pool_ids = list(res_meta.keys())
    pool_embs = [res_meta[i]["embedding"] for i in pool_ids]
    matches = compute_similarity(jd_emb, pool_embs, pool_ids)[:count]

    job_data = jd_meta[jobid]

    return {
        "job": {
            "job_id": job_data["id"],
            "job_title": job_data["job_title"],
            "company": job_data["company"],
            "description": job_data["description"],
            "location": job_data.get("location"),
            "salary": job_data.get("salary"),
            "skills_required": job_data.get("skills_required"),
            "experience": job_data.get("experience"),
            "job_type": job_data.get("job_type"),
        },
        "candidates": [
            {
                "user_id": res_meta[rid]["user_id"],
                "username": res_meta[rid]["username"],
                "resume": res_meta[rid]["filename"],
                "accuracy": round(score * 100, 2),
                "match": score_label(round(score * 100, 2)),
            }
            for rid, score in matches
        ],
    }

@router.get("/match/jobs")
async def match_jobs(resumeId: str, count: int = Query(5, gt=0)):
    res_meta = load_meta(RESUME_META)
    jd_meta = load_meta(JD_META)

    if resumeId not in res_meta:
        raise HTTPException(status_code=404, detail="Resume ID not found.")

    res_emb = res_meta[resumeId]["embedding"]
    pool_ids = list(jd_meta.keys())
    pool_embs = [jd_meta[i]["embedding"] for i in pool_ids]
    matches = compute_similarity(res_emb, pool_embs, pool_ids)[:count]

    resume_user = res_meta[resumeId]["username"]

    return {
        "resume_id": resumeId,
        "username": resume_user,
        "matches": [
            {
                "job_id": jid,
                "company": jd_meta[jid]["company"],
                "job_title": jd_meta[jid]["job_title"],
                "description": jd_meta[jid].get("description"),
                "location": jd_meta[jid].get("location"),
                "salary": jd_meta[jid].get("salary"),
                "skills_required": jd_meta[jid].get("skills_required"),
                "experience": jd_meta[jid].get("experience"),
                "job_type": jd_meta[jid].get("job_type"),
                "accuracy": round(score * 100, 2),
                "match": score_label(round(score * 100, 2)),
            }
            for jid, score in matches
        ],
    }
