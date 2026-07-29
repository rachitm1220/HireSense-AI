from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from pydantic import BaseModel

from core.database import get_session
from domains.auth.dependencies import get_current_user
from domains.users.models import User
from domains.jobs.models import Job, UserJob
from domains.jobs.services import scrape_job_url

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobSubmitRequest(BaseModel):
    url: str

@router.post("/submit")
async def submit_job(
    request: JobSubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    # 1. Check if job already exists globally
    job = db.exec(select(Job).where(Job.url == request.url)).first()
    
    if not job:
        # Create new PENDING job
        job = Job(url=request.url, status="PENDING")
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Scrape immediately (Synchronously for MVP so user sees it right away)
        try:
            extracted_data = await scrape_job_url(request.url)
            job.title = extracted_data.get("title")
            job.company = extracted_data.get("company")
            job.location = extracted_data.get("location")
            job.description = extracted_data.get("description")
            job.status = "COMPLETED"
        except Exception as e:
            job.status = "FAILED"
            job.description = str(e)
            
        db.add(job)
        db.commit()
        db.refresh(job)
        
    # 2. Link this job to the user's personal board
    user_job = db.exec(select(UserJob).where(UserJob.user_id == user.id, UserJob.job_id == job.id)).first()
    if not user_job:
        user_job = UserJob(user_id=user.id, job_id=job.id)
        db.add(user_job)
        db.commit()
        
    return job

@router.get("/community")
def get_community_jobs(user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    """Get all jobs submitted by anyone, with tailored status for current user"""
    statement = select(Job, UserJob.tailored_resume_latex).outerjoin(
        UserJob, (Job.id == UserJob.job_id) & (UserJob.user_id == user.id)
    ).order_by(Job.created_at.desc())
    
    results = db.exec(statement).all()
    return [{**job.dict(), "has_tailored_resume": latex is not None, "tailored_resume_latex": latex} for job, latex in results]

@router.get("/me")
def get_my_jobs(user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    """Get only jobs submitted by this user, with tailored status"""
    statement = select(Job, UserJob.tailored_resume_latex).join(
        UserJob, (Job.id == UserJob.job_id) & (UserJob.user_id == user.id)
    ).order_by(Job.created_at.desc())
    
    results = db.exec(statement).all()
    return [{**job.dict(), "has_tailored_resume": latex is not None, "tailored_resume_latex": latex} for job, latex in results]

@router.get("/applications")
def get_applications(user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    """Get all jobs where a resume was tailored. Returns two lists: generated and applied."""
    statement = select(Job, UserJob).join(UserJob).where(UserJob.user_id == user.id, UserJob.tailored_resume_latex != None).order_by(Job.created_at.desc())
    results = db.exec(statement).all()
    
    generated = []
    applied = []
    
    for job, user_job in results:
        job_data = job.dict()
        if user_job.applied_status:
            applied.append(job_data)
        else:
            generated.append(job_data)
            
    return {"generated": generated, "applied": applied}

@router.post("/{job_id}/apply")
def mark_as_applied(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    """Mark a job as applied by the user"""
    user_job = db.exec(select(UserJob).where(UserJob.user_id == user.id, UserJob.job_id == job_id)).first()
    if not user_job:
        raise HTTPException(status_code=404, detail="Job not found or resume not tailored yet.")
        
    user_job.applied_status = True
    db.commit()
    return {"status": "success"}

@router.delete("/{job_id}/application")
def delete_application(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    """Clear the tailored resume if the user didn't apply"""
    user_job = db.exec(select(UserJob).where(UserJob.user_id == user.id, UserJob.job_id == job_id)).first()
    if not user_job:
        raise HTTPException(status_code=404, detail="Application not found.")
        
    # We just clear the resume and applied_status instead of deleting the UserJob completely, 
    # since UserJob also tracks their scraped jobs.
    user_job.tailored_resume_latex = None
    user_job.applied_status = False
    db.commit()
    return {"status": "success"}
