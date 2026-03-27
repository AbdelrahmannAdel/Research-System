# Handles all authentication endpoints, registration and login
# All routes here are prefixed with /auth (set in main.py),
# so /register becomes /auth/register and /login becomes /auth/login

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token

# Create a router
# Registered in main.py with the /auth prefix
router = APIRouter()

# Request body model for registratio
# FastAPI automatically validates that all three fields are present and are strings
# If any field is missing the request is rejected before our code runs
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

# Request body model for login
class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # db is injected automatically by FastAPI using the get_db dependency
    # Check if a user with this email already exists in the database
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Hash the password before storing
    hashed = hash_password(request.password)

    # Create a new User object and save it to the database
    new_user = User(name=request.name, email=request.email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # refresh to get the auto-generated id and created_at from the DB

    return {"message": "Account created successfully"}

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Look up the user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Return the same message whether email or password is wrong
        # This prevents attackers from using the login form to discover registered emails
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify the entered password against the stored bcrypt hash
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create a JWT token containing the user's ID and email
    # "sub" (subject) is a standard JWT field, we use it to store the user ID
    token = create_access_token({"sub": str(user.id), "email": user.email})

    # Return the token and user's name so the frontend can greet the user
    return {"access_token": token, "token_type": "bearer", "name": user.name}