from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
import pypdf
import io

from core.database import get_session
from domains.auth.dependencies import get_current_user
from domains.users.models import User, UserContext
from domains.users.services import merge_context_via_llm

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/context")
def get_user_context(user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    context = db.exec(select(UserContext).where(UserContext.user_id == user.id)).first()
    if not context:
        context = UserContext(user_id=user.id)
        db.add(context)
        db.commit()
        db.refresh(context)
    return context

class ContextUpdateRequest(BaseModel):
    contact: dict[str, str] = {}
    skills: list[str] = []
    experience: list[dict] = []
    projects: list[dict] = []
    education: list[dict] = []
    certifications: list[dict] = []
    achievements: list[dict] = []

@router.put("/me/context")
def update_user_context_manual(
    request: ContextUpdateRequest, 
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    context = db.exec(select(UserContext).where(UserContext.user_id == user.id)).first()
    if not context:
        context = UserContext(user_id=user.id)
        
    for key, value in request.model_dump().items():
        setattr(context, key, value)
        
    db.add(context)
    db.commit()
    db.refresh(context)
    return context

class ChatUpdateRequest(BaseModel):
    message: str

@router.post("/me/context/chat")
def update_context_chat(
    request: ChatUpdateRequest, 
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    context = db.exec(select(UserContext).where(UserContext.user_id == user.id)).first()
    if not context:
        context = UserContext(user_id=user.id)
    
    # Merge using Llama-3
    current_dict = context.model_dump(exclude={"user_id"})
    merged_dict = merge_context_via_llm(current_dict, request.message)
    
    for key, value in merged_dict.items():
        setattr(context, key, value)
        
    db.add(context)
    db.commit()
    db.refresh(context)
    return context

@router.post("/me/context/upload")
async def update_context_upload(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    # Read PDF purely in memory (never saved to disk!)
    pdf_bytes = await file.read()
    import pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    
    raw_text = ""
    links_context = []
    
    for page in doc:
        raw_text += page.get_text() + "\n"
        
        # Extract hidden hyperlinks and the exact text they are attached to
        links = page.get_links()
        for link in links:
            if link.get("kind") == pymupdf.LINK_URI:
                try:
                    rect = link.get("from")
                    text = page.get_textbox(rect).strip()
                    # clean up line breaks
                    text = " ".join(text.split())
                    uri = link.get("uri")
                    if text and uri:
                        links_context.append(f"- [{text}]({uri})")
                except Exception:
                    pass
                    
    if links_context:
        raw_text += "\n\n--- EXTRACTED HYPERLINKS ---\n"
        raw_text += "The following text snippets contained these exact hyperlinks:\n"
        raw_text += "\n".join(links_context)
        
    # Get current context
    context = db.exec(select(UserContext).where(UserContext.user_id == user.id)).first()
    if not context:
        context = UserContext(user_id=user.id)
        
    current_dict = context.model_dump(exclude={"user_id"})
    
    # Pass the raw text and current context to Llama-3 to merge intelligently
    merged_dict = merge_context_via_llm(current_dict, raw_text)
    
    # Save the merged JSON to Postgres
    for key, value in merged_dict.items():
        setattr(context, key, value)
        
    db.add(context)
    db.commit()
    db.refresh(context)
    return context
