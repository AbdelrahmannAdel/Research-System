# Reads the .env file and exposes DATABASE_URL and SECRET_KEY to the rest of the backend via the settings object

from pydantic_settings import BaseSettings

# Settings class inherits from BaseSettings which automatically
# reads environment variables and .env files
# Each attribute defined here must exist in the .env file
class Settings(BaseSettings):
    DATABASE_URL: str  # PostgreSQL connection string
    SECRET_KEY: str    # secret used to sign and verify JWT tokens

    class Config:
        # Tell BaseSettings to look for variables in the .env file
        env_file = ".env"

# Create a single shared instance of Settings
# All other files import this one object rather than reading .env themselves
settings = Settings()