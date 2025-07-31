from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.youtube_service import get_transcript, get_video_id

router = APIRouter()

class TranscriptRequest(BaseModel):
    url: str

class TranscriptResponse(BaseModel):
    transcript: str

@router.post("/transcript", response_model=TranscriptResponse)
async def fetch_transcript(request: TranscriptRequest):
    video_id = get_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    transcript = get_transcript(video_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found for this video.")
        
    return TranscriptResponse(transcript=transcript) 