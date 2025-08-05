from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.transcript_library_service import TranscriptLibraryService
from app.models.word_cache import UrlContent
from app.models.user_vocabulary import User
from app.services.auth_service import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class LibraryRequest(BaseModel):
    video_url: str
    username: str

class LibraryResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    message: Optional[str] = None

# Add your existing endpoints here from the original file
# This is just the import fixes - you'll need to copy the rest
