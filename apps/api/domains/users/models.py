from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: Optional[str] = None
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserContext(SQLModel, table=True):
    user_id: int = Field(primary_key=True, foreign_key="user.id")
    contact: dict[str, str] = Field(default={}, sa_column=Column(JSONB))
    skills: list[str] = Field(default=[], sa_column=Column(JSONB))
    experience: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    projects: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    education: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    certifications: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    achievements: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
