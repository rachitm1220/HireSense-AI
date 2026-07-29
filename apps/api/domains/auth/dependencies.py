from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from core.database import get_session
from domains.users.models import User, UserSession

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_session)
) -> User:
    """Dependency to retrieve the currently logged-in user via their session token."""
    token = credentials.credentials
    
    # Check if session exists
    user_session = db.exec(select(UserSession).where(UserSession.id == token)).first()
    if not user_session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
        
    # Get user tied to the session
    user = db.exec(select(User).where(User.id == user_session.user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user
