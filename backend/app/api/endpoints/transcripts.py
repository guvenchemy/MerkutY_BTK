from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.yt_dlp_service import YTDlpService

router = APIRouter()

class TranscriptRequest(BaseModel):
    url: str

class TranscriptResponse(BaseModel):
    transcript: str

@router.post("/transcript", response_model=TranscriptResponse)
async def fetch_transcript(request: TranscriptRequest):
    youtube_service = YTDlpService()
    video_id = youtube_service.get_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    transcript_result = youtube_service.get_transcript(video_id)
    if not transcript_result.get("success"):
        raise HTTPException(status_code=404, detail=f"Transcript not found: {transcript_result.get('error', 'Unknown error')}")
        
    return TranscriptResponse(transcript=transcript_result["transcript"]) 