from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.transcript_library_service import TranscriptLibraryService

router = APIRouter()

class LibraryRequest(BaseModel):
    video_url: str
    username: str

class LibraryResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

class TranscriptAdaptationRequest(BaseModel):
    username: str
    target_unknown_percentage: Optional[float] = 10.0

def get_library_service():
    return TranscriptLibraryService()

@router.post("/library/transcript", response_model=LibraryResponse)
async def get_or_create_transcript(
    request: LibraryRequest,
    library_service: TranscriptLibraryService = Depends(get_library_service),
    db: Session = Depends(get_db)
):
    """
    Get transcript from library or create new one.
    Returns both original and adapted versions.
    """
    try:
        result = library_service.get_or_create_transcript(
            video_url=request.video_url,
            username=request.username,
            db=db
        )
        
        if "error" in result:
            return LibraryResponse(success=False, error=result["error"])
        
        return LibraryResponse(success=True, data=result)
        
    except Exception as e:
        return LibraryResponse(success=False, error=f"Library operation failed: {str(e)}")

@router.get("/library/transcripts")
async def get_library_transcripts(
    limit: int = 50,
    offset: int = 0,
    library_service: TranscriptLibraryService = Depends(get_library_service),
    db: Session = Depends(get_db)
):
    """
    Get all transcripts from library with pagination.
    """
    try:
        transcripts = library_service.get_library_transcripts(db, limit, offset)
        return {
            "success": True,
            "data": transcripts,
            "total": len(transcripts)
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get library: {str(e)}"}

@router.get("/library/transcript/{transcript_id}")
async def get_transcript_by_id(
    transcript_id: int,
    library_service: TranscriptLibraryService = Depends(get_library_service),
    db: Session = Depends(get_db)
):
    """
    Get specific transcript by ID with full content.
    """
    try:
        transcript = library_service.get_transcript_by_id(transcript_id, db)
        
        if not transcript:
            return {"success": False, "error": "Transcript not found"}
        
        return {"success": True, "data": transcript}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get transcript: {str(e)}"}

@router.post("/library/transcript/{transcript_id}/adapt")
async def adapt_transcript_for_user(
    transcript_id: int,
    request: TranscriptAdaptationRequest,
    library_service: TranscriptLibraryService = Depends(get_library_service),
    db: Session = Depends(get_db)
):
    """
    Create smart AI adaptation for specific user's level using their vocabulary and grammar knowledge.
    Implements i+1 methodology with 90% comprehensible + 10% challenging content.
    """
    try:
        # Get original transcript
        transcript = library_service.get_transcript_by_id(transcript_id, db)
        
        if not transcript:
            return {"success": False, "error": "Transcript not found"}
        
        # Create smart AI adaptation for this user
        from app.services.ai_text_adaptation_service import AITextAdaptationService
        ai_service = AITextAdaptationService()
        
        # Use the requested unknown percentage for optimal i+1 learning
        adaptation_result = ai_service.adapt_text_with_ai(
            text=transcript["original_text"], 
            username=request.username,
            db=db,  # Pass the existing db session
            target_unknown_percentage=request.target_unknown_percentage
        )
        
        if adaptation_result.get("error"):
            return {"success": False, "error": adaptation_result["error"]}
        
        adapted_text = adaptation_result.get("adapted_text", transcript["original_text"])
        
        return {
            "success": True,
            "data": {
                "original_text": transcript["original_text"],
                "adapted_text": adapted_text,
                "word_count": transcript["word_count"],
                "adapted_word_count": len(adapted_text.split()),
                "adaptation_info": adaptation_result.get("adaptation_info", {}),
                "user_level": adaptation_result.get("user_level", "A1"),
                "adaptation_method": adaptation_result.get("adaptation_method", "Smart AI i+1"),
                "comprehension_target": "90% known + 10% challenging words"
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to adapt transcript: {str(e)}"}

@router.post("/library/transcript/video/{video_id}/adapt")
async def adapt_transcript_by_video_id(
    video_id: str,
    request: TranscriptAdaptationRequest,
    library_service: TranscriptLibraryService = Depends(get_library_service),
    db: Session = Depends(get_db)
):
    """
    Create smart AI adaptation using video ID instead of transcript ID.
    More convenient for frontend usage.
    """
    try:
        # Find transcript by video ID
        from app.models import ProcessedTranscript
        transcript_record = db.query(ProcessedTranscript).filter(
            ProcessedTranscript.video_id == video_id,
            ProcessedTranscript.is_active == True
        ).first()
        
        if not transcript_record:
            return {"success": False, "error": f"Transcript not found for video ID: {video_id}"}
        
        # Get transcript data
        transcript = {
            "original_text": transcript_record.original_text,
            "word_count": transcript_record.word_count
        }
        
        # Create smart AI adaptation for this user
        from app.services.ai_text_adaptation_service import AITextAdaptationService
        ai_service = AITextAdaptationService()
        
        # Use the requested unknown percentage for optimal i+1 learning
        adaptation_result = ai_service.adapt_text_with_ai(
            text=transcript["original_text"], 
            username=request.username,
            db=db,
            target_unknown_percentage=request.target_unknown_percentage
        )
        
        if adaptation_result.get("error"):
            return {"success": False, "error": adaptation_result["error"]}
        
        adapted_text = adaptation_result.get("adapted_text", transcript["original_text"])
        
        return {
            "success": True,
            "data": {
                "original_text": transcript["original_text"],
                "adapted_text": adapted_text,
                "word_count": transcript["word_count"],
                "adapted_word_count": len(adapted_text.split()),
                "adaptation_info": adaptation_result.get("adaptation_info", {}),
                "user_level": adaptation_result.get("user_level", "A1"),
                "adaptation_method": adaptation_result.get("adaptation_method", "Smart AI i+1"),
                "comprehension_target": "90% known + 10% challenging words"
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to adapt transcript: {str(e)}"}

@router.get("/library/search")
async def search_transcripts(
    q: str,
    min_words: int = 0,
    max_words: int = 0,
    limit: int = 20,
    library_service: TranscriptLibraryService = Depends(get_library_service),
    db: Session = Depends(get_db)
):
    """
    Search transcripts by title, channel, or content with filters.
    """
    try:
        results = library_service.search_transcripts(q, db, limit)
        
        # Apply filters
        filtered_results = []
        for transcript in results:
            # Word count filter
            if min_words > 0 and transcript.get('word_count', 0) < min_words:
                continue
            if max_words > 0 and transcript.get('word_count', 0) > max_words:
                continue
                
            filtered_results.append(transcript)
        
        return {
            "success": True,
            "data": filtered_results,
            "query": q,
            "total": len(filtered_results),
            "filters": {
                "min_words": min_words,
                "max_words": max_words
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Search failed: {str(e)}"}

@router.get("/library/user/{username}")
async def get_user_transcripts(
    username: str,
    library_service: TranscriptLibraryService = Depends(get_library_service),
    db: Session = Depends(get_db)
):
    """
    Get transcripts added by specific user.
    """
    try:
        transcripts = library_service.get_user_transcripts(username, db)
        return {
            "success": True,
            "data": transcripts,
            "username": username,
            "total": len(transcripts)
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get user transcripts: {str(e)}"}

@router.get("/library/stats")
async def get_library_stats(
    library_service: TranscriptLibraryService = Depends(get_library_service),
    db: Session = Depends(get_db)
):
    """
    Get library statistics.
    """
    try:
        from app.models.user_vocabulary import ProcessedTranscript
        
        total_transcripts = db.query(ProcessedTranscript).filter(
            ProcessedTranscript.is_active == True
        ).count()
        
        from sqlalchemy import func
        
        total_views = db.query(ProcessedTranscript).filter(
            ProcessedTranscript.is_active == True
        ).with_entities(
            func.sum(ProcessedTranscript.view_count)
        ).scalar() or 0
        
        total_words = db.query(ProcessedTranscript).filter(
            ProcessedTranscript.is_active == True
        ).with_entities(
            func.sum(ProcessedTranscript.word_count)
        ).scalar() or 0
        
        return {
            "success": True,
            "data": {
                "total_transcripts": total_transcripts,
                "total_views": total_views,
                "total_words": total_words,
                "average_views": total_views / total_transcripts if total_transcripts > 0 else 0
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get stats: {str(e)}"} 