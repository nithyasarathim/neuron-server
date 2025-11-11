from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.resume_routes import router as resume_router
from routes.job_routes import router as job_router

app = FastAPI(title="Resume Job Matcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router)
app.include_router(job_router)