import sys
from sqlalchemy import text
from core.database import engine
from sqlmodel import SQLModel

# Import models to register
from domains.users.models import *
from domains.jobs.models import *
from domains.interviews.models import *
from domains.resumes.models import *

def run():
    print("Creating new tables...")
    SQLModel.metadata.create_all(engine)
    
    with engine.connect() as conn:
        print("Applying ALTER TABLE statements for mockinterview...")
        try:
            conn.execute(text("ALTER TABLE mockinterview ALTER COLUMN job_id DROP NOT NULL"))
            print("- Made job_id optional")
        except Exception as e:
            print(f"- job_id error: {e}")
            
        try:
            conn.execute(text("ALTER TABLE mockinterview ADD COLUMN resume_id INTEGER REFERENCES resumedocument(id)"))
            print("- Added resume_id column")
        except Exception as e:
            print(f"- resume_id error: {e}")
            
        try:
            conn.execute(text("ALTER TABLE mockinterview ADD COLUMN custom_jd TEXT"))
            print("- Added custom_jd column")
        except Exception as e:
            print(f"- custom_jd error: {e}")
            
        conn.commit()
    print("Migration V2 complete.")

if __name__ == "__main__":
    run()
