from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.core.database import get_db
from app.services.word_cache_service import WordCacheService
from app.services.ai_teacher_service import AITeacherService
from app.services.grammar_hierarchy_service import GrammarHierarchyService

router = APIRouter()

# Pydantic models
class WordExplanationRequest(BaseModel):
    word: str

class SmartAnalysisRequest(BaseModel):
    text: str
    user_id: int
    include_grammar_explanations: bool = True
    include_quiz: bool = True

class GrammarStatusRequest(BaseModel):
    user_id: int
    grammar_pattern: str
    status: str  # 'known' or 'practice'

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Initialize services
word_cache_service = WordCacheService()
ai_teacher_service = AITeacherService()
grammar_service = GrammarHierarchyService()

@router.post("/word-explanation", response_model=AnalysisResponse)
async def get_word_explanation(
    request: WordExplanationRequest,
    db: Session = Depends(get_db)
):
    """
    Get word explanation from cache or generate with AI
    Implements smart caching to avoid duplicate API calls
    """
    try:
        if not request.word or len(request.word.strip()) < 1:
            raise HTTPException(status_code=400, detail="Word cannot be empty")
        
        result = await word_cache_service.get_word_explanation(request.word, db)
        
        return AnalysisResponse(
            success=result["success"],
            data=result.get("data"),
            error=result.get("error")
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=f"Word explanation failed: {str(e)}"
        )

@router.post("/smart-analysis", response_model=AnalysisResponse)
async def smart_text_analysis(
    request: SmartAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    🤖 Intelligent text analysis with personalized grammar explanations
    Only explains grammar patterns the user doesn't know yet
    """
    try:
        if not request.text or len(request.text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Text must be at least 10 characters long")
        
        if not request.include_grammar_explanations:
            return AnalysisResponse(
                success=True,
                data={"message": "Grammar explanations disabled"}
            )
        
        # Use AI teacher service for intelligent analysis
        result = await ai_teacher_service.analyze_text_for_user(
            request.text, request.user_id, db
        )
        
        return AnalysisResponse(
            success=result["success"],
            data=result,
            error=result.get("error")
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=f"Smart analysis failed: {str(e)}"
        )

@router.post("/mark-grammar-knowledge", response_model=AnalysisResponse)
async def mark_grammar_knowledge(
    request: GrammarStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Mark user's grammar pattern knowledge status
    Updates user level automatically
    """
    try:
        if request.status not in ["known", "practice"]:
            raise HTTPException(status_code=400, detail="Status must be 'known' or 'practice'")
        
        result = await ai_teacher_service.mark_user_grammar_knowledge(
            request.user_id, request.grammar_pattern, request.status, db
        )
        
        return AnalysisResponse(
            success=result["success"],
            data=result,
            error=result.get("error")
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=f"Failed to mark grammar knowledge: {str(e)}"
        )

@router.get("/user-level/{user_id}", response_model=AnalysisResponse)
async def get_user_comprehensive_level(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user's comprehensive level based on vocabulary + grammar knowledge
    Uses hybrid scoring algorithm
    """
    try:
        result = grammar_service.calculate_user_level(user_id, db)
        
        return AnalysisResponse(
            success=result["success"],
            data=result,
            error=result.get("error")
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=f"Failed to get user level: {str(e)}"
        )

@router.get("/grammar-dashboard/{user_id}", response_model=AnalysisResponse)
async def get_grammar_dashboard(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive grammar learning dashboard for user
    Includes level info, progress overview, and learning path
    """
    try:
        result = ai_teacher_service.get_user_grammar_dashboard(user_id, db)
        
        return AnalysisResponse(
            success=result["success"],
            data=result,
            error=result.get("error")
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=f"Failed to get grammar dashboard: {str(e)}"
        )

@router.get("/cache-stats", response_model=AnalysisResponse)
async def get_cache_stats(db: Session = Depends(get_db)):
    """
    Get word cache statistics for admin monitoring
    """
    try:
        stats = word_cache_service.get_cache_stats(db)
        
        return AnalysisResponse(
            success=stats.get("cache_enabled", False),
            data=stats
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=f"Failed to get cache stats: {str(e)}"
        )

@router.get("/grammar-overview/{user_id}", response_model=AnalysisResponse)
async def get_user_grammar_overview(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed overview of user's grammar knowledge by level
    Shows what they know, what they're practicing, and what's missing
    """
    try:
        result = grammar_service.get_user_grammar_overview(user_id, db)
        
        return AnalysisResponse(
            success=result["success"],
            data=result,
            error=result.get("error")
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=f"Failed to get grammar overview: {str(e)}"
        ) 