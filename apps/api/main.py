from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.database import create_db_and_tables

# IMPORTANT: Import models here so SQLModel knows about them before create_all() runs!
import domains.users.models 
import domains.jobs.models
import domains.interviews.models

from domains.auth.router import router as auth_router
from domains.users.router import router as users_router
from domains.jobs.router import router as jobs_router
from domains.resumes.router import router as resumes_router
from domains.interviews.router import router as interviews_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This automatically syncs all SQLModel classes to Postgres tables!
    create_db_and_tables()
    yield

app = FastAPI(title="HireSense AI API", lifespan=lifespan)

# Allow CORS for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(jobs_router)
app.include_router(resumes_router)
app.include_router(interviews_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "HireSense AI API is running on the new architecture!"}
