from sqlalchemy.orm import Session
from sqlalchemy import text
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
        Enhanced with discover library check to avoid duplicate processing.
        Returns transcript data with both original and adapted versions.
        """
        try:
            # Extract video ID
            video_id = self.youtube_service.get_video_id(video_url)
            if not video_id:
                return {"error": "Invalid YouTube URL"}
            
            # Get user
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return {"error": "User not found"}
            
            # 1) Check if transcript exists in user's own library
            own_transcript = db.query(ProcessedTranscript).filter(
                ProcessedTranscript.video_id == video_id,
                ProcessedTranscript.added_by_user_id == user.id
            ).first()
            
            if own_transcript:
                # Update view count
                own_transcript.view_count += 1
                db.commit()
                
                return {
                    "success": True,
                    "from_library": True,
                    "from_own_library": True,
                    "from_discover": False,
                    "video_id": video_id,
                    "original_text": own_transcript.original_text,
                    "adapted_text": own_transcript.adapted_text,
                    "video_title": own_transcript.video_title,
                    "channel_name": own_transcript.channel_name,
                    "duration": own_transcript.duration,
                    "view_count": own_transcript.view_count,
                    "added_by": own_transcript.added_by_username,
                    "cefr_level": own_transcript.cefr_level,
                    "message": "Kütüphanenden yüklendi"
                }
            
            # 2) Check if transcript exists in discover (other users' libraries)
            discover_transcript = db.query(ProcessedTranscript).filter(
                ProcessedTranscript.video_id == video_id,
                ProcessedTranscript.added_by_user_id != user.id
            ).first()
            
            if discover_transcript:
                # Create a personal copy for this user (dedup by composite unique)
                existing_for_user = db.query(ProcessedTranscript).filter(
                    ProcessedTranscript.video_id == video_id,
                    ProcessedTranscript.added_by_user_id == user.id
                ).first()
                if not existing_for_user:
                    new_copy = ProcessedTranscript(
                        video_id=discover_transcript.video_id,
                        video_url=discover_transcript.video_url,
                        video_title=discover_transcript.video_title,
                        channel_name=discover_transcript.channel_name,
                        duration=discover_transcript.duration,
                        original_text=discover_transcript.original_text,
                        adapted_text=discover_transcript.adapted_text,
                        language=discover_transcript.language,
                        word_count=discover_transcript.word_count,
                        adapted_word_count=discover_transcript.adapted_word_count,
                        added_by_user_id=user.id,
                        added_by_username=username,
                        view_count=1,
                        cefr_level=discover_transcript.cefr_level,
                        level_confidence=discover_transcript.level_confidence,
                        level_analysis=discover_transcript.level_analysis,
                        level_analyzed_at=discover_transcript.level_analyzed_at
                    )
                    db.add(new_copy)
                    db.commit()
                    discover_transcript = new_copy
                
                return {
                    "success": True,
                    "from_library": True,
                    "from_own_library": True,
                    "from_discover": True,
                    "video_id": video_id,
                    "original_text": discover_transcript.original_text,
                    "adapted_text": discover_transcript.adapted_text,
                    "video_title": discover_transcript.video_title,
                    "channel_name": discover_transcript.channel_name,
                    "duration": discover_transcript.duration,
                    "view_count": discover_transcript.view_count,
                    "added_by": discover_transcript.added_by_username,
                    "cefr_level": discover_transcript.cefr_level,
                    "message": "Keşiften kişisel kopya oluşturuldu"
                }
            
            # 3) Fetch new transcript
            transcript_result = self.youtube_service.get_transcript(video_id)
            if not transcript_result.get("success"):
                return {"error": f"Failed to get transcript: {transcript_result.get('error', 'Unknown error')}"}
            
            original_text = transcript_result["transcript"]
            
            # Get video info
            video_info = self.youtube_service.get_video_info(video_id)
            
            # CEFR Level Detection with AI (no fallback)
            cefr_result = self.ai_service.detect_cefr_level(original_text, allow_fallback=False)
            
            # AI Text Adaptation (current level approach)
            adapted_result = self.ai_service.adapt_text_with_ai(original_text, username, db, target_unknown_percentage=5.0)
            adapted_text = adapted_result.get("adapted_text", original_text)
            
            # Save to library with AI adaptation
            new_transcript = ProcessedTranscript(
                video_id=video_id,
                video_url=video_url,
                video_title=video_info.get("title", "Unknown"),
                channel_name=video_info.get("uploader", "Unknown"),
                duration=video_info.get("duration", 0),
                original_text=original_text,
                adapted_text=adapted_text,  # Save AI adaptation
                language=transcript_result.get("language", "en"),
                word_count=len(original_text.split()),
                adapted_word_count=len(adapted_text.split()),
                added_by_user_id=user.id,
                added_by_username=username,
                view_count=1,
                # CEFR Level fields
                cefr_level=cefr_result.get("cefr_level") if cefr_result.get("success") else None,
                level_confidence=cefr_result.get("confidence") if cefr_result.get("success") else None,
                level_analysis=cefr_result.get("analysis") if cefr_result.get("success") else None,
                level_analyzed_at=db.execute(text("SELECT NOW()")).scalar()
            )
            
            db.add(new_transcript)
            db.commit()
            
            return {
                "success": True,
                "from_library": False,
                "video_id": video_id,
                "original_text": original_text,
                "adapted_text": adapted_text,  # AI adaptation included
                "video_title": new_transcript.video_title,
                "channel_name": new_transcript.channel_name,
                "duration": new_transcript.duration,
                "view_count": new_transcript.view_count,
                "added_by": username,
                "cefr_level": new_transcript.cefr_level
            }
            
        except Exception as e:
            logger.error(f"Error in get_or_create_transcript: {e}")
            return {"error": f"Transcript processing failed: {str(e)}"}
    
    def get_library_transcripts(self, db: Session, limit: int = 50, offset: int = 0, username: str = None) -> List[Dict[str, Any]]:
        """Get transcripts from library with pagination. If username provided, only return user's transcripts."""
        try:
            query = db.query(ProcessedTranscript).filter(
                ProcessedTranscript.is_active == True
            )
            
            # If username provided, filter by user
            if username:
                user = db.query(User).filter(User.username == username).first()
                if user:
                    query = query.filter(ProcessedTranscript.added_by_user_id == user.id)
            
            transcripts = query.order_by(
                ProcessedTranscript.view_count.desc()
            ).offset(offset).limit(limit * 2).all()  # overfetch then dedupe
            
            # Dedupe by video_id for discover lists (when username is None)
            results: List[Dict[str, Any]] = []
            seen_ids = set()
            for t in transcripts:
                key = t.video_id if not username else t.id  # discover → per video; personal → per row
                if key in seen_ids:
                    continue
                seen_ids.add(key)
                results.append({
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
                    "cefr_level": t.cefr_level,
                    "level_confidence": t.level_confidence,
                    "level_analysis": t.level_analysis,
                    "level_analyzed_at": t.level_analyzed_at.isoformat() if t.level_analyzed_at else None
                })
            
            return results[:limit]
            
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
            transcripts = db.query(ProcessedTranscript).filter(
                ProcessedTranscript.is_active == True,
                (
                    ProcessedTranscript.video_title.ilike(f"%{query}%") |
                    ProcessedTranscript.channel_name.ilike(f"%{query}%") |
                    ProcessedTranscript.original_text.ilike(f"%{query}%")
                )
            ).order_by(
                ProcessedTranscript.view_count.desc()
            ).limit(limit * 2).all()
            
            results = []
            seen = set()
            for t in transcripts:
                if t.video_id in seen:
                    continue
                seen.add(t.video_id)
                results.append({
                    "id": t.id,
                    "video_id": t.video_id,
                    "video_title": t.video_title,
                    "channel_name": t.channel_name,
                    "duration": t.duration,
                    "word_count": t.word_count,
                    "view_count": t.view_count,
                    "added_by": t.added_by_username
                })
            
            return results[:limit]
            
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