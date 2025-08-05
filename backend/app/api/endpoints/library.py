from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.services.transcript_library_service import TranscriptLibraryService
from app.models.content_models import UrlContent
from app.models.user_vocabulary import User
from app.models.transcript_library import TranscriptLibrary
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
        from app.models import TranscriptLibrary
        transcript_record = db.query(TranscriptLibrary).filter(
            TranscriptLibrary.video_id == video_id,
            TranscriptLibrary.is_active == True
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
        from app.models.user_vocabulary import User
        
        total_transcripts = db.query(TranscriptLibrary).filter(
            TranscriptLibrary.is_active == True
        ).count()
        
        total_views = db.query(TranscriptLibrary).filter(
            TranscriptLibrary.is_active == True
        ).with_entities(
            func.sum(TranscriptLibrary.view_count)
        ).scalar() or 0
        
        total_words = db.query(TranscriptLibrary).filter(
            TranscriptLibrary.is_active == True
        ).with_entities(
            func.sum(TranscriptLibrary.word_count)
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

@router.get("/library/web-content")
async def get_web_content(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get web content from library (Medium, Wikipedia etc.)
    """
    try:
        from app.models.content_models import UrlContent
        
        # Get web content with pagination
        contents = db.query(UrlContent).order_by(
            UrlContent.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        # Convert to format similar to transcripts
        content_list = []
        for content in contents:
            content_list.append({
                "id": content.id,
                "title": content.title or f"{content.source_type.title()} Content",
                "source_type": content.source_type,
                "url": content.url,
                "content": content.content,
                "created_at": content.created_at.isoformat() if content.created_at else None,
                "video_id": None,  # For compatibility with transcript interface
                "original_text": content.content,
                "adapted_text": None  # Web content doesn't have adapted version in UrlContent
            })
        
        return {
            "success": True,
            "data": content_list
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get web content: {str(e)}"}

@router.get("/library/all-content")
async def get_all_content(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get both transcripts and web content combined
    """
    try:
        # Get transcripts
        # Get transcripts directly from service
        transcript_service = TranscriptLibraryService()
        transcript_response = transcript_service.get_transcripts(
            user_id=current_user.id,
            limit=limit//2,
            offset=offset//2
        )
        transcripts = transcript_response.get("data", [])
        
        # Get web content
        web_response = await get_web_content(limit=limit//2, offset=offset//2, db=db)
        web_contents = web_response.get("data", [])
        
        # Combine and sort by created_at
        all_content = []
        
        # Add transcripts with type marker
        for transcript in transcripts:
            transcript["content_type"] = "youtube"
            all_content.append(transcript)
        
        # Add web content with type marker
        for content in web_contents:
            content["content_type"] = "web"
            all_content.append(content)
        
        # Sort by created_at descending
        all_content.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {
            "success": True,
            "data": all_content[:limit]
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get all content: {str(e)}"} 

@router.get("/web-content/{content_id}")
async def get_web_content_detail(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific web content item"""
    try:
        # Geçici olarak user filter'ı olmadan
        web_content = db.query(UrlContent).filter(UrlContent.id == content_id).first()
        
        if not web_content:
            raise HTTPException(status_code=404, detail="Web content not found")
        
        return {
            "success": True,
            "data": {
                "id": web_content.id,
                "title": web_content.title,
                "url": web_content.url,
                "content": web_content.content,
                "adapted_text": web_content.content,  # Henüz adapted content yok
                "word_count": len(web_content.content.split()) if web_content.content else 0,
                "adapted_word_count": len(web_content.content.split()) if web_content.content else 0,
                "created_at": web_content.created_at.isoformat(),
                "content_type": "web"
            }
        }
    except Exception as e:
        logger.error(f"Error getting web content detail: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/web-content")
async def get_web_content(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get user's saved web content from library
    """
    try:
        # Geçici olarak tüm content'i getir (user filter'ı olmadan)
        web_contents = db.query(UrlContent).order_by(UrlContent.created_at.desc()).offset(offset).limit(limit).all()
        
        formatted_contents = []
        for content in web_contents:
            formatted_contents.append({
                "id": content.id,
                "title": content.title,
                "url": content.url,
                "word_count": len(content.content.split()) if content.content else 0,
                "created_at": content.created_at.isoformat(),
                "content_type": "web"
            })
        
        return {
            "success": True,
            "data": formatted_contents
        }
        
    except Exception as e:
        logger.error(f"Error getting web content list: {str(e)}")
        return {"success": False, "error": f"Failed to get web content: {str(e)}"}

@router.post("/web-content-from-url")
async def get_or_create_web_content(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Web content'i URL'den al - varsa veritabanından, yoksa internetten çek ve kaydet
    """
    try:
        url = request.get("url", "").strip()
        if not url:
            return {"success": False, "error": "URL is required"}
            
        # URL'yi normalize et
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        print(f"🔍 Checking web content for URL: {url}")
        
        # Önce veritabanında var mı kontrol et
        from app.models.content_models import UrlContent
        existing_content = db.query(UrlContent).filter(UrlContent.url == url).first()
        
        if existing_content:
            print(f"✅ Found existing content in database (ID: {existing_content.id})")
            return {
                "success": True,
                "data": {
                    "id": existing_content.id,
                    "url": existing_content.url,
                    "title": existing_content.title,
                    "content": existing_content.content,
                    "source_type": existing_content.source_type,
                    "created_at": existing_content.created_at.isoformat() if existing_content.created_at else None,
                    "from_cache": True
                },
                "message": "Content loaded from database cache"
            }
        
        # Veritabanında yoksa internetten çek
        print(f"🌐 Content not found in cache, fetching from internet...")
        
        # Web scraping ile içeriği çek
        from app.services.text_analysis_service import TextAnalysisService
        text_service = TextAnalysisService()
        
        content_result = text_service.extract_web_content(url)
        
        if not content_result.get("success"):
            return {"success": False, "error": content_result.get("error", "Failed to extract content")}
        
        content_data = content_result["data"]
        
        # Veritabanına kaydet
        new_content = UrlContent(
            url=url,
            title=content_data.get("title", ""),
            content=content_data.get("content", ""),
            source_type=content_data.get("source_type", "unknown")
        )
        
        db.add(new_content)
        db.commit()
        db.refresh(new_content)
        
        print(f"💾 Saved new content to database (ID: {new_content.id})")
        
        return {
            "success": True,
            "data": {
                "id": new_content.id,
                "url": new_content.url,
                "title": new_content.title,
                "content": new_content.content,
                "source_type": new_content.source_type,
                "created_at": new_content.created_at.isoformat() if new_content.created_at else None,
                "from_cache": False
            },
            "message": "Content fetched from internet and cached"
        }
        
    except Exception as e:
        print(f"❌ Web content error: {str(e)}")
        return {"success": False, "error": f"Failed to get web content: {str(e)}"} 