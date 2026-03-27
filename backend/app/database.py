# Sets up the PostgreSQL connection, session factory, and base model class.
# Three exports are used throughout the backend:
# engine: the database connection
# Base: parent class for all table models
# get_db(): FastAPI dependency that provides a database session per request

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Connect to PostgreSQL using the URL from the .env file
engine = create_engine(settings.DATABASE_URL)

# Session factory, autocommit and autoflush are off so we control exactly when changes are saved to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class, all models inherit from this so SQLAlchemy knows they are tables
Base = declarative_base()

def get_db():
    db = SessionLocal() # Creates a session, yields it to the endpoint, then closes it when done.
    try:
        yield db
    finally:
        db.close()