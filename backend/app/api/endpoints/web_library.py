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

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

router = APIRouter()

@router.post("/save-web-content")
async def save_web_content(request: WebAnalysisRequest, db: Session = Depends(get_db)):
    """
    🌐 Save Web Content to Library
    Saves analyzed Medium/Wikipedia content to library for future use
    """
    try:
        # User ID'yi al veya oluştur
        user_id = request.user_id
        if not user_id:
            user_id = GrammarService.create_or_get_user_by_session(db, "temp_session")
        
        url = request.web_url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Check if already exists in library
        from app.models.content_models import UrlContent
        existing_content = db.query(UrlContent).filter(UrlContent.url == url).first()
        
        if existing_content:
            return AnalysisResponse(
                success=True,
                data={
                    "message": "Content already exists in library",
                    "content_id": existing_content.id,
                    "title": existing_content.title,
                    "from_library": True
                }
            )
        
        # Basit kaydetme - UrlContent kullan
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Source type belirle
        if 'medium.com' in domain:
            source_type = 'medium'
        elif 'wikipedia.org' in domain:
            source_type = 'wikipedia'
        else:
            source_type = 'web'
        
        new_content = UrlContent(
            title=f"{source_type.title()} Content",
            url=url,
            content="Web content analyzed and saved",
            source_type=source_type,
            created_at=datetime.datetime.now()
        )
        
        db.add(new_content)
        db.commit()
        db.refresh(new_content)
        
        return AnalysisResponse(
            success=True,
            data={
                "message": "Content successfully saved to library",
                "content_id": new_content.id,
                "from_library": False
            }
        )
        
    except Exception as e:
        print(f"❌ Web content save error: {str(e)}")
        return AnalysisResponse(
            success=False,
            error=f"Failed to save web content: {str(e)}"
        )
