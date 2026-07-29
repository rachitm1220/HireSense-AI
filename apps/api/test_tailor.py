import asyncio
from sqlmodel import create_engine, Session, select
from domains.users.models import UserContext
from domains.jobs.models import Job
from domains.resumes.services import tailor_resume_latex

engine = create_engine("postgresql://postgres:postgres@localhost:5432/hiresense")

def test():
    with Session(engine) as db:
        user_context = db.exec(select(UserContext)).first()
        job = db.exec(select(Job)).first()
        
        context_dict = {
            "contact": user_context.contact,
            "education": user_context.education,
            "experience": user_context.experience,
            "projects": user_context.projects,
            "skills": user_context.skills,
            "certifications": user_context.certifications,
            "achievements": user_context.achievements,
        }
        
        try:
            print("Calling LLM...")
            latex = tailor_resume_latex(context_dict, job.description)
            print("SUCCESS")
        except Exception as e:
            import traceback
            traceback.print_exc()

test()
