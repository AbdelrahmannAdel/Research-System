from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter()