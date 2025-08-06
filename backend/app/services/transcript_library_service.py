from sqlalchemy.orm import Session
from app.models.user_vocabulary import ProcessedTranscript, User
from app.services.yt_dlp_service import YTDlpService
from app.services.ai_text_adaptation_service import AITextAdaptationService
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class TranscriptLibraryService:
    """Service for managing transcript library functionality."""
    
    def __init__(self):
        self.youtube_service = YTDlpService()
        self.ai_service = AITextAdaptationService()
    
    def get_or_create_transcript(self, video_url: str, username: str, db: Session) -> Dict[str, Any]:
        """
        Get transcript from library or create new one.
        Returns transcript data with both original and adapted versions.
        """
        try:
            # Extract video ID
            video_id = self.youtube_service.get_video_id(video_url)
            if not video_id:
                return {"error": "Invalid YouTube URL"}
            
            # Check if transcript exists in library
            existing_transcript = db.query(ProcessedTranscript).filter(
                ProcessedTranscript.video_id == video_id
            ).first()
            
            if existing_transcript:
                # Update view count
                existing_transcript.view_count += 1
                db.commit()
                
                return {
                    "success": True,
                    "from_library": True,
                    "video_id": video_id,
                    "original_text": existing_transcript.original_text,
                    "adapted_text": existing_transcript.adapted_text,
                    "video_title": existing_transcript.video_title,
                    "channel_name": existing_transcript.channel_name,
                    "duration": existing_transcript.duration,
                    "view_count": existing_transcript.view_count,
                    "added_by": existing_transcript.added_by_username
                }
            
            # Get user
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return {"error": "User not found"}
            
            # Fetch new transcript
            transcript_result = self.youtube_service.get_transcript(video_id)
            if not transcript_result.get("success"):
                return {"error": f"Failed to get transcript: {transcript_result.get('error', 'Unknown error')}"}
            
            original_text = transcript_result["transcript"]
            
            # Get video info
            video_info = self.youtube_service.get_video_info(video_id)
            
            # CEFR Level Detection with AI
            cefr_result = self.ai_service.detect_cefr_level(original_text)
            
            # Save to library (only original text)
            new_transcript = ProcessedTranscript(
                video_id=video_id,
                video_url=video_url,
                video_title=video_info.get("title", "Unknown"),
                channel_name=video_info.get("uploader", "Unknown"),
                duration=video_info.get("duration", 0),
                original_text=original_text,
                adapted_text=None,  # Don't save AI adaptation
                language=transcript_result.get("language", "en"),
                word_count=len(original_text.split()),
                adapted_word_count=0,  # Will be calculated on demand
                added_by_user_id=user.id,
                added_by_username=username,
                view_count=1,
                # CEFR Level fields
                cefr_level=cefr_result.get("cefr_level", "B1"),
                level_confidence=cefr_result.get("confidence", 50),
                level_analysis=cefr_result.get("analysis", "AI analysis completed"),
                level_analyzed_at=db.execute("SELECT NOW()").scalar()
            )
            
            db.add(new_transcript)
            db.commit()
            
            return {
                "success": True,
                "from_library": False,
                "video_id": video_id,
                "original_text": original_text,
                "adapted_text": None,  # No AI adaptation stored
                "video_title": new_transcript.video_title,
                "channel_name": new_transcript.channel_name,
                "duration": new_transcript.duration,
                "view_count": new_transcript.view_count,
                "added_by": username
            }
            
        except Exception as e:
            logger.error(f"Error in get_or_create_transcript: {e}")
            return {"error": f"Transcript processing failed: {str(e)}"}
    
    def get_library_transcripts(self, db: Session, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all transcripts from library with pagination."""
        try:
            transcripts = db.query(ProcessedTranscript).filter(
                ProcessedTranscript.is_active == True
            ).order_by(
                ProcessedTranscript.view_count.desc()
            ).offset(offset).limit(limit).all()
            
            return [
                {
                    "id": t.id,
                    "video_id": t.video_id,
                    "video_url": t.video_url,
                    "video_title": t.video_title,
                    "channel_name": t.channel_name,
                    "duration": t.duration,
                    "language": t.language,
                    "word_count": t.word_count,
                    "adapted_word_count": t.adapted_word_count,
                    "view_count": t.view_count,
                    "added_by": t.added_by_username,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    # CEFR Level fields (NEW)
                    "cefr_level": t.cefr_level,
                    "level_confidence": t.level_confidence,
                    "level_analysis": t.level_analysis,
                    "level_analyzed_at": t.level_analyzed_at.isoformat() if t.level_analyzed_at else None
                }
                for t in transcripts
            ]
            
        except Exception as e:
            logger.error(f"Error getting library transcripts: {e}")
            return []
    
    def get_transcript_by_id(self, transcript_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Get specific transcript by ID."""
        try:
            transcript = db.query(ProcessedTranscript).filter(
                ProcessedTranscript.id == transcript_id,
                ProcessedTranscript.is_active == True
            ).first()
            
            if not transcript:
                return None
            
            # Update view count
            transcript.view_count += 1
            db.commit()
            
            return {
                "id": transcript.id,
                "video_id": transcript.video_id,
                "video_url": transcript.video_url,
                "video_title": transcript.video_title,
                "channel_name": transcript.channel_name,
                "duration": transcript.duration,
                "original_text": transcript.original_text,
                "adapted_text": transcript.adapted_text,
                "language": transcript.language,
                "word_count": transcript.word_count,
                "adapted_word_count": transcript.adapted_word_count,
                "view_count": transcript.view_count,
                "added_by": transcript.added_by_username,
                "created_at": transcript.created_at.isoformat() if transcript.created_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting transcript by ID: {e}")
            return None
    
    def search_transcripts(self, query: str, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Search transcripts by title, channel, or content."""
        try:
            # Simple text search
            transcripts = db.query(ProcessedTranscript).filter(
                ProcessedTranscript.is_active == True,
                (
                    ProcessedTranscript.video_title.ilike(f"%{query}%") |
                    ProcessedTranscript.channel_name.ilike(f"%{query}%") |
                    ProcessedTranscript.original_text.ilike(f"%{query}%")
                )
            ).order_by(
                ProcessedTranscript.view_count.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": t.id,
                    "video_id": t.video_id,
                    "video_title": t.video_title,
                    "channel_name": t.channel_name,
                    "duration": t.duration,
                    "word_count": t.word_count,
                    "view_count": t.view_count,
                    "added_by": t.added_by_username
                }
                for t in transcripts
            ]
            
        except Exception as e:
            logger.error(f"Error searching transcripts: {e}")
            return []
    
    def get_user_transcripts(self, username: str, db: Session) -> List[Dict[str, Any]]:
        """Get transcripts added by specific user."""
        try:
            transcripts = db.query(ProcessedTranscript).filter(
                ProcessedTranscript.added_by_username == username,
                ProcessedTranscript.is_active == True
            ).order_by(
                ProcessedTranscript.created_at.desc()
            ).all()
            
            return [
                {
                    "id": t.id,
                    "video_id": t.video_id,
                    "video_title": t.video_title,
                    "channel_name": t.channel_name,
                    "duration": t.duration,
                    "word_count": t.word_count,
                    "view_count": t.view_count,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in transcripts
            ]
            
        except Exception as e:
            logger.error(f"Error getting user transcripts: {e}")
            return [] 