from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session as DbSession, select
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

from core.database import get_session
from core.config import settings
from domains.users.models import User, UserSession

router = APIRouter(prefix="/auth", tags=["auth"])

class GoogleLoginRequest(BaseModel):
    token: str

@router.post("/google")
def google_auth(request: GoogleLoginRequest, db: DbSession = Depends(get_session)):
    try:
        # 1. Verify the Google Token
        idinfo = id_token.verify_oauth2_token(
            request.token, requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        email = idinfo["email"]
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    # 2. Get or create the user
    user = db.exec(select(User).where(User.email == email)).first()
    
    if not user:
        user = User(
            email=email, 
            name=idinfo.get("name"), 
            picture=idinfo.get("picture")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3. Create an opaque session token
    user_session = UserSession(user_id=user.id)
    db.add(user_session)
    db.commit()
    db.refresh(user_session)

    # 4. Return token to the frontend
    return {
        "token": user_session.id, 
        "user": {
            "email": user.email, 
            "name": user.name, 
            "picture": user.picture
        }
    }
