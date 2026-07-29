from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from core.database import get_session
from domains.auth.dependencies import get_current_user
from domains.users.models import User
from domains.jobs.models import Job, UserJob
from domains.interviews.models import MockInterview

from domains.interviews.services import generate_interview_reply, get_interview_hint, generate_scorecard

from domains.resumes.models import ResumeDocument

router = APIRouter(prefix="/interviews", tags=["interviews"])

class StartInterviewRequest(BaseModel):
    job_id: Optional[int] = None
    resume_id: Optional[int] = None
    custom_jd: Optional[str] = None
    interview_type: str # HR, DSA, SYSTEM_DESIGN, CORE_FUNDAMENTALS
    difficulty: str = "Strict Hiring Manager"

class ChatRequest(BaseModel):
    message: str
    code_snippet: Optional[str] = None
    raw_excalidraw: Optional[List[Any]] = None

@router.post("/start")
def start_interview(
    request: StartInterviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Initializes a new mock interview session for a specific job application."""
    if request.job_id:
        user_job = db.exec(select(UserJob).where(UserJob.user_id == user.id, UserJob.job_id == request.job_id)).first()
        if not user_job or not user_job.tailored_resume_latex:
            raise HTTPException(status_code=400, detail="You must tailor a resume for this job before starting an interview.")
        job = db.exec(select(Job).where(Job.id == request.job_id)).first()
        company = job.company
        jd = job.description
        resume_latex = user_job.tailored_resume_latex
    elif request.resume_id:
        resume_doc = db.exec(select(ResumeDocument).where(ResumeDocument.id == request.resume_id, ResumeDocument.user_id == user.id)).first()
        if not resume_doc:
            raise HTTPException(status_code=404, detail="Resume not found in library.")
        company = "Custom Company"
        jd = request.custom_jd or "General role based on the candidate's experience."
        resume_latex = resume_doc.latex_content
    else:
        raise HTTPException(status_code=400, detail="Must provide job_id or resume_id")
    
    # Generate the first opening message from the AI
    try:
        opening_msg = generate_interview_reply(
            request.interview_type, 
            request.difficulty,
            company,
            jd, 
            resume_latex, 
            []
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    interview = MockInterview(
        user_id=user.id,
        job_id=request.job_id,
        resume_id=request.resume_id,
        custom_jd=request.custom_jd,
        interview_type=request.interview_type,
        difficulty=request.difficulty,
        status="IN_PROGRESS",
        messages=[{"role": "assistant", "content": opening_msg}],
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return {"interview_id": interview.id, "status": "started"}

@router.get("/")
def get_all_interviews(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Gets all interviews for the current user."""
    statement = select(MockInterview).where(MockInterview.user_id == user.id).order_by(MockInterview.created_at.desc())
    interviews = db.exec(statement).all()
    
    interviews_list = []
    for interview in interviews:
        if interview.job_id:
            job = db.exec(select(Job).where(Job.id == interview.job_id)).first()
            job_title = job.title if job else "Unknown Job"
            company = job.company if job else "Unknown Company"
        else:
            job_title = "Custom Mock Interview"
            company = "Custom JD"
            
        interviews_list.append({
            "id": interview.id,
            "job_title": job_title,
            "company": company,
            "interview_type": interview.interview_type,
            "difficulty": interview.difficulty,
            "status": interview.status,
            "scorecard": interview.scorecard,
            "created_at": interview.created_at
        })
    return interviews_list

@router.get("/{interview_id}/session")
def get_interview_session(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Gets the current state of an interview session."""
    interview = db.exec(select(MockInterview).where(MockInterview.id == interview_id, MockInterview.user_id == user.id)).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return interview

@router.post("/{interview_id}/chat")
def interview_chat(
    interview_id: int,
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Sends a user message to the AI and gets a reply."""
    interview = db.exec(select(MockInterview).where(MockInterview.id == interview_id, MockInterview.user_id == user.id)).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
        
    if interview.job_id:
        job = db.exec(select(Job).where(Job.id == interview.job_id)).first()
        user_job = db.exec(select(UserJob).where(UserJob.job_id == interview.job_id, UserJob.user_id == user.id)).first()
        company = job.company if job else "Unknown Company"
        jd = job.description if job else ""
        resume_latex = user_job.tailored_resume_latex if user_job else ""
    else:
        resume_doc = db.exec(select(ResumeDocument).where(ResumeDocument.id == interview.resume_id)).first()
        company = "Custom Company"
        jd = interview.custom_jd or "General role based on the candidate's experience."
        resume_latex = resume_doc.latex_content if resume_doc else ""
    
    messages = list(interview.messages)
    
    # Append code snippet if present
    full_message = request.message
    if request.code_snippet:
        full_message += f"\n\n[CANDIDATE'S WORKSPACE]:\n```\n{request.code_snippet}\n```"
        
    user_msg = {"role": "user", "content": full_message}
    if request.raw_excalidraw:
        user_msg["raw_excalidraw"] = request.raw_excalidraw
        
    messages.append(user_msg)
    
    try:
        reply = generate_interview_reply(
            interview.interview_type, 
            interview.difficulty,
            company,
            jd, 
            resume_latex, 
            messages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    messages.append({"role": "assistant", "content": reply})
    
    # We must explicitly flag the JSONB column as modified in SQLAlchemy/SQLModel
    from sqlalchemy.orm.attributes import flag_modified
    interview.messages = messages
    flag_modified(interview, "messages")
    
    db.commit()
    
    return {"reply": reply}

@router.post("/{interview_id}/hint")
def get_hint(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Gets a brief hint for the user based on the current context."""
    interview = db.exec(select(MockInterview).where(MockInterview.id == interview_id, MockInterview.user_id == user.id)).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
        
    try:
        hint = get_interview_hint(list(interview.messages))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"hint": hint}

@router.post("/{interview_id}/end")
def end_interview(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Ends the interview and generates the scorecard."""
    interview = db.exec(select(MockInterview).where(MockInterview.id == interview_id, MockInterview.user_id == user.id)).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
        
    if interview.status == "COMPLETED":
        return {"scorecard": interview.scorecard}
        
    try:
        scorecard = generate_scorecard(interview.interview_type, list(interview.messages))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate scorecard: {str(e)}")
        
    interview.status = "COMPLETED"
    interview.scorecard = scorecard
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(interview, "scorecard")
    db.commit()
    
    return {"scorecard": scorecard}
