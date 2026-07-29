from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class ResumeDocument(SQLModel, table=True):
    __tablename__ = "resumedocument"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str = Field(default="Untitled Resume")
    latex_content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
