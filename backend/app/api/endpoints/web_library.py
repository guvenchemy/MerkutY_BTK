from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import datetime
from app.services.text_analysis_service import TextAnalysisService
from app.services.grammar_service import GrammarService
from app.core.database import get_db

class WebAnalysisRequest(BaseModel):
    web_url: str
    include_examples: bool = True
    include_adaptation: bool = False
    user_id: Optional[int] = None
    username: Optional[str] = None

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

router = APIRouter()

@router.post("/save-web-content")
async def save_web_content(request: WebAnalysisRequest, db: Session = Depends(get_db)):
    try:
        url = request.web_url.strip()
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Resolve user id from username if provided
        added_by_user_id = request.user_id
        if not added_by_user_id and request.username:
            from app.models.user_vocabulary import User
            user = db.query(User).filter(User.username == request.username).first()
            if user:
                added_by_user_id = user.id

        # Check existing personal copy first
        from app.models.content_models import UrlContent
        existing = None
        if added_by_user_id:
            existing = db.query(UrlContent).filter(
                UrlContent.url == url, UrlContent.added_by_user_id == added_by_user_id
            ).first()
        if existing:
            return AnalysisResponse(success=True, data={
                "id": existing.id,
                "url": existing.url,
                "title": existing.title,
                "content": existing.content,
                "word_count": existing.word_count,
                "cefr_level": existing.cefr_level,
                "created_at": existing.created_at.isoformat() if existing.created_at else None
            })

        # Fallback to discover copy
        discover = db.query(UrlContent).filter(UrlContent.url == url).first()
        if discover:
            # create personal copy
            new_content = UrlContent(
                url=discover.url,
                title=discover.title,
                content=discover.content,
                source_type=discover.source_type,
                word_count=discover.word_count or (len(discover.content.split()) if discover.content else 0),
                added_by_user_id=added_by_user_id,
                cefr_level=discover.cefr_level,
                level_confidence=discover.level_confidence,
                level_analysis=discover.level_analysis,
                level_analyzed_at=discover.level_analyzed_at,
            )
            db.add(new_content)
            db.commit()
            db.refresh(new_content)
            return AnalysisResponse(success=True, data={
                "id": new_content.id,
                "url": new_content.url,
                "title": new_content.title,
                "content": new_content.content,
                "word_count": new_content.word_count,
                "cefr_level": new_content.cefr_level,
                "created_at": new_content.created_at.isoformat() if new_content.created_at else None
            })

        # Fetch from internet
        text_service = TextAnalysisService()
        result = text_service.extract_web_content(url)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to extract content"))
        data = result["data"]
        content_text = data.get("content", "")
        word_count = len(content_text.split()) if content_text else 0

        # Compute CEFR
        from app.services.ai_text_adaptation_service import AITextAdaptationService
        ai = AITextAdaptationService()
        cefr = ai.detect_cefr_level(content_text, allow_fallback=False) if content_text else {"cefr_level": None}

        # Save
        new_content = UrlContent(
            url=url,
            title=data.get("title", ""),
            content=content_text,
            source_type=data.get("source_type", "unknown"),
            word_count=word_count,
            added_by_user_id=added_by_user_id,
            cefr_level=cefr.get("cefr_level") if cefr.get("success") else None,
            level_confidence=cefr.get("confidence") if cefr.get("success") else None,
            level_analysis=cefr.get("analysis") if cefr.get("success") else None,
            level_analyzed_at=datetime.datetime.utcnow()
        )
        db.add(new_content)
        db.commit()
        db.refresh(new_content)

        return AnalysisResponse(success=True, data={
            "id": new_content.id,
            "url": new_content.url,
            "title": new_content.title,
            "content": new_content.content,
            "word_count": new_content.word_count,
            "cefr_level": new_content.cefr_level,
            "created_at": new_content.created_at.isoformat() if new_content.created_at else None
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
