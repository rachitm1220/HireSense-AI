from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Dict, Any
from datetime import datetime

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(unique=True, index=True)
    title: Optional[str] = Field(default=None)
    company: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None) # Markdown from Tinyfish
    status: str = Field(default="PENDING") # PENDING, COMPLETED, FAILED
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserJob(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    job_id: int = Field(foreign_key="job.id", primary_key=True)
    tailored_resume_latex: Optional[str] = Field(default=None)
    applied_status: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
