# Provides all security functions used for authenticatio
# password hashing, password verification, JWT creation, and JWT validation

from datetime import datetime, timedelta
from jose import JWTError, jwt
from bcrypt import hashpw, checkpw, gensalt
from app.core.config import settings

ALGORITHM = "HS256"                 # signing algorithm for JWT tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Hash a plain text password using bcrypt
def hash_password(password: str) -> str:
    return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")

# Check if a plain text password matches a stored bcrypt hash.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# Create a signed JWT token containing the provided data plus an expiry time
# The token is signed with SECRET_KEY
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

# Decode and validate a JWT token
# Returns user ID and email if valid, None if invalid or expired
def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None