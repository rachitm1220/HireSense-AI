from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Dict, Any, List
from datetime import datetime

class MockInterview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    job_id: Optional[int] = Field(default=None, foreign_key="job.id", index=True)
    resume_id: Optional[int] = Field(default=None, foreign_key="resumedocument.id", index=True)
    custom_jd: Optional[str] = None
    
    interview_type: str = Field(default="HR") # HR, DSA, SYSTEM_DESIGN, CORE_FUNDAMENTALS
    difficulty: str = Field(default="Strict Hiring Manager") # Friendly Recruiter, Strict Hiring Manager
    status: str = Field(default="PENDING") # PENDING, IN_PROGRESS, COMPLETED
    
    messages: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    scorecard: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
