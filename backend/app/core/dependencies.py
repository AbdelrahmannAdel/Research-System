# Provides reusable FastAPI dependencies for protected endpoints.
# Any endpoint that requires a logged-in user imports and uses get_current_user.

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.security import verify_token

# HTTPBearer tells FastAPI to expect an Authorization, Bearer <token> header.
# auto_error=True means FastAPI automatically returns 401 if the header is missing.
bearer_scheme = HTTPBearer(auto_error=True)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    # Extract the raw token string from the Authorization header
    token = credentials.credentials

    # Verify and decode the token using our security module
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Extract user ID from the token payload
    user_id = int(payload.get("sub"))

    # Look up the user in the database to confirm they still exist
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user