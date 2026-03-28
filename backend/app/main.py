# Entry point of the entire backend application.
# This file ties everything together, it creates the FastAPI app,
# sets up CORS, creates database tables, and registers all API routers.
# Run with: uvicorn app.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.api import auth, papers
from app.models import paper

# Create all database tables on startup if they don't already exist.
# SQLAlchemy looks at all models that inherit from Base (User, SavedPaper)
# and creates their corresponding tables in PostgreSQL automatically.
Base.metadata.create_all(bind=engine)

# Create the main FastAPI application instance
app = FastAPI(title="Research Paper AI System")

# Configure CORS
# Our frontend runs on localhost:5173 and backend on localhost:8000, different origins.
# This middleware tells the backend to accept requests from the frontend's address.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # only allow our frontend
    allow_credentials=True,                   # allow cookies and auth headers
    allow_methods=["*"],                      # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],                      # allow all headers
)

# Register the auth router, makes /auth/register and /auth/login available
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Register the paper router, makes all /papers endpoints available
app.include_router(papers.router, prefix="/papers", tags=["Papers"])

# Root endpoint, used to verify the backend is running
@app.get("/")
def root():
    return {"message": "Backend is running"}