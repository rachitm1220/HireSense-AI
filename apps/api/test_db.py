from sqlmodel import Session, select, create_engine
from domains.jobs.models import Job

engine = create_engine("postgresql://postgres:postgres@localhost:5432/hiresense")
with Session(engine) as session:
    job = session.exec(select(Job).where(Job.id == 4)).first()
    if job:
        print("URL:", job.url)
        print("TITLE:", job.title)
        print("COMPANY:", job.company)
        print("DESCRIPTION:", job.description[:500] if job.description else "None")
    else:
        print("Job 4 not found")
