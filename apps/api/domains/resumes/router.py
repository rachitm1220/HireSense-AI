from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel import Session, select
from pydantic import BaseModel
import requests as http_requests
import io

from core.database import get_session
from domains.auth.dependencies import get_current_user
from domains.users.models import User, UserContext
from domains.jobs.models import Job, UserJob
from domains.resumes.models import ResumeDocument
from domains.resumes.services import tailor_resume_latex, generate_resume_from_pdf_text, analyze_resume_with_ai_enhanced
from fastapi import UploadFile, File, Form
import pypdf

router = APIRouter(prefix="/resumes", tags=["resumes"])

class SaveLibraryRequest(BaseModel):
    name: str
    latex_content: str

class TailorRequest(BaseModel):
    job_id: int
    custom_instructions: str | None = None

class CompileRequest(BaseModel):
    latex_code: str

@router.post("/tailor")
def generate_tailored_resume(
    request: TailorRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    # 1. Fetch User Context
    user_context = db.exec(select(UserContext).where(UserContext.user_id == user.id)).first()
    if not user_context:
        raise HTTPException(status_code=404, detail="Please complete your AI Profile Context first.")
        
    # 2. Fetch Job Description
    job = db.exec(select(Job).where(Job.id == request.job_id)).first()
    if not job or not job.description:
        raise HTTPException(status_code=404, detail="Job description not found.")
        
    # 3. Serialize user context
    context_dict = {
        "contact": user_context.contact,
        "education": user_context.education,
        "experience": user_context.experience,
        "projects": user_context.projects,
        "skills": user_context.skills,
        "certifications": user_context.certifications,
        "achievements": user_context.achievements,
    }
    
    # 4. Generate the Tailored LaTeX string
    try:
        latex_code = tailor_resume_latex(context_dict, job.description, request.custom_instructions)
        
        # 5. Save the resume in UserJob
        user_job = db.exec(select(UserJob).where(UserJob.user_id == user.id, UserJob.job_id == job.id)).first()
        if not user_job:
            user_job = UserJob(user_id=user.id, job_id=job.id)
            db.add(user_job)
            
        user_job.tailored_resume_latex = latex_code
        db.commit()
        
        return {"latex_code": latex_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to tailor resume: {str(e)}")

@router.post("/compile")
def compile_resume_pdf(
    request: CompileRequest,
    user: User = Depends(get_current_user),
):
    """
    Proxies the LaTeX code to the free ytotech.com compilation API
    and returns the compiled PDF bytes.
    No system TeX installation required.
    """
    try:
        response = http_requests.post(
            "https://latex.ytotech.com/builds/sync",
            json={'compiler': 'pdflatex', 'resources': [{'main': True, 'content': request.latex_code}]},
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="LaTeX compilation service timed out. Please try again.")
    except http_requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Could not reach LaTeX compilation service.")

    if response.status_code != 201 or "application/pdf" not in response.headers.get("content-type", ""):
        log_snippet = response.text[:500] if response.text else "No log available."
        raise HTTPException(
            status_code=500,
            detail=f"PDF compilation failed. Compiler log: {log_snippet}"
        )

    return Response(
        content=response.content,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="resume.pdf"'},
    )

@router.post("/library/upload")
async def upload_resume_to_library(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    pdf_bytes = await file.read()
    doc = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    raw_text = ""
    for page in doc.pages:
        raw_text += page.extract_text() + "\n"
        
    try:
        result = generate_resume_from_pdf_text(raw_text)
        
        resume_doc = ResumeDocument(
            user_id=user.id,
            name=result["name"],
            latex_content=result["latex"]
        )
        db.add(resume_doc)
        db.commit()
        db.refresh(resume_doc)
        
        return {"id": resume_doc.id, "name": resume_doc.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")

@router.post("/library")
def save_resume_to_library(
    request: SaveLibraryRequest,
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    resume_doc = ResumeDocument(
        user_id=user.id,
        name=request.name,
        latex_content=request.latex_content
    )
    db.add(resume_doc)
    db.commit()
    db.refresh(resume_doc)
    return {"id": resume_doc.id, "name": resume_doc.name}

@router.get("/library")
def get_user_resumes(user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    resumes = db.exec(select(ResumeDocument).where(ResumeDocument.user_id == user.id)).all()
    return [{"id": r.id, "name": r.name, "created_at": r.created_at, "latex_content": r.latex_content} for r in resumes]

@router.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(default="")
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    pdf_bytes = await file.read()
    doc = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    raw_text = ""
    for page in doc.pages:
        raw_text += page.extract_text() + "\n"
        
    if not raw_text or len(raw_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
    try:
        analysis = analyze_resume_with_ai_enhanced(raw_text, job_description)
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
