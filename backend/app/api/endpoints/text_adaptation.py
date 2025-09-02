from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.text_adaptation_service import TextAdaptationService
from app.services.ai_text_adaptation_service import AITextAdaptationService
from app.services.yt_dlp_service import YTDlpService

router = APIRouter()

class TextAnalysisRequest(BaseModel):
    text: str
    username: str

class YouTubeAdaptationRequest(BaseModel):
    youtube_url: str
    username: str
    target_unknown_percentage: Optional[float] = 10.0

class TextAdaptationRequest(BaseModel):
    text: str
    username: str
    target_unknown_percentage: Optional[float] = 10.0

@router.post("/analyze")
async def analyze_text_difficulty(request: TextAnalysisRequest, db: Session = Depends(get_db)) -> Dict:
    """
    Analyze text difficulty for a specific user.
    Returns breakdown of known vs unknown words.
    """
    try:
        # Get user's known words
        known_words = TextAdaptationService.get_user_known_words(request.username, db)
        
        if not known_words:
            raise HTTPException(
                status_code=404, 
                detail=f"User '{request.username}' not found or has no vocabulary"
            )
        
        # Analyze text
        analysis = TextAdaptationService.analyze_text_difficulty(request.text, known_words)
        
        # Get word-by-word analysis for frontend coloring
        word_analysis = TextAdaptationService.get_word_analysis_for_coloring(request.text, known_words, request.username, db)
        
        # Add learning word suggestions
        learning_words = TextAdaptationService.identify_learning_words(request.text, request.username)
        
        return {
            "analysis": analysis,
            "word_analysis": word_analysis,
            "learning_suggestions": learning_words,
            "user_vocabulary_size": len(known_words)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Removed non-AI endpoints - system now uses only AI-powered adaptation

@router.get("/learning-words/{username}")
async def get_learning_suggestions(username: str, text: str) -> List[Dict]:
    """
    Get top learning word suggestions for user from given text.
    """
    try:
        learning_words = TextAdaptationService.identify_learning_words(text, username)
        return learning_words
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning suggestions: {str(e)}")

@router.get("/user-stats/{username}")
async def get_user_learning_stats(username: str, db: Session = Depends(get_db)) -> Dict:
    """
    Get user's learning statistics and vocabulary information.
    """
    try:
        from app.models.user_vocabulary import User, UserVocabulary, Vocabulary
        
        # Get user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=404, 
                detail=f"User '{username}' not found"
            )
        
        # Get detailed vocabulary stats - Use user_id instead of username
        user_known_words = db.query(Vocabulary.word).join(UserVocabulary).filter(
            UserVocabulary.user_id == user.id,
            UserVocabulary.status == "known"
        ).all()
        known_words = [row[0] for row in user_known_words]
        
        # Count words by status
        known_count = db.query(UserVocabulary).filter(
            UserVocabulary.user_id == user.id,
            UserVocabulary.status == "known"
        ).count()
        
        unknown_count = db.query(UserVocabulary).filter(
            UserVocabulary.user_id == user.id,
            UserVocabulary.status == "unknown"
        ).count()
        
        ignore_count = db.query(UserVocabulary).filter(
            UserVocabulary.user_id == user.id,
            UserVocabulary.status == "ignore"
        ).count()
        
        # Use grammar hierarchy service for proper level calculation
        from app.services.grammar_hierarchy_service import GrammarHierarchyService
        grammar_service = GrammarHierarchyService()
        level_info = grammar_service.calculate_user_level(user.id, db)
        
        # Get CEFR level and convert to user-friendly name
        cefr_level = level_info.get("user_level", {}).get("level", "A1")
        
        if cefr_level in ["A1", "A2"]:
            level = "Beginner"
            level_score = 1 if cefr_level == "A1" else 2
        elif cefr_level in ["B1", "B2"]:
            level = "Intermediate"
            level_score = 3 if cefr_level == "B1" else 4
        elif cefr_level in ["C1", "C2"]:
            level = "Advanced"
            level_score = 5 if cefr_level == "C1" else 6
        else:
            level = "Beginner"
            level_score = 1
        
        return {
            "username": username,
            "vocabulary_size": len(known_words),
            "level": level,
            "level_score": level_score,
            "known_words_sample": list(known_words)[:100] if known_words else [],
            "vocabulary_stats": {
                "known_words": known_count,
                "unknown_words": unknown_count,
                "ignored_words": ignore_count,
                "total_managed": known_count + unknown_count + ignore_count
            },
            "krashen_readiness": {
                "can_handle_i_plus_1": len(known_words) >= 100,
                "recommended_unknown_percentage": 10.0 if len(known_words) >= 200 else 5.0,
                "next_milestone": 200 if len(known_words) < 200 else 500 if len(known_words) < 500 else 1000
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")

# ============================================================================
# 🤖 AI-POWERED ENDPOINTS (OpenAI ChatGPT Integration)
# ============================================================================

@router.post("/adapt")
async def adapt_text_for_user(request: TextAdaptationRequest, db: Session = Depends(get_db)) -> Dict:
    """
    🤖 AI-Powered text adaptation using OpenAI ChatGPT.
    Intelligently rewrites text to achieve perfect i+1 level.
    """
    try:
        print(f"[DEBUG] Adaptation request received:")
        print(f"  - username: {request.username}")
        print(f"  - target_unknown_percentage: {request.target_unknown_percentage}")
        print(f"  - text length: {len(request.text)} characters")
        print(f"  - text preview: {request.text[:100]}...")
        
        ai_service = AITextAdaptationService()
        result = ai_service.adapt_text_with_ai(
            text=request.text,
            username=request.username,
            target_unknown_percentage=request.target_unknown_percentage,
            db=db
        )
        
        print(f"[DEBUG] Adaptation result keys: {list(result.keys())}")
        print(f"[DEBUG] Success field: {result.get('success', 'NO SUCCESS FIELD')}")
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI text adaptation failed: {str(e)}")

@router.post("/youtube")
async def ai_adapt_youtube_for_user(request: YouTubeAdaptationRequest, db: Session = Depends(get_db)) -> Dict:
    """
    🤖 AI-Powered YouTube adaptation pipeline:
    1. Extract transcript from YouTube
    2. Use ChatGPT to intelligently adapt to user's i+1 level
    3. Provide learning suggestions and analysis
    """
    try:
        ai_service = AITextAdaptationService()
        result = ai_service.adapt_youtube_with_ai(
            youtube_url=request.youtube_url,
            username=request.username,
            target_unknown_percentage=request.target_unknown_percentage,
            db=db
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI YouTube adaptation failed: {str(e)}")

class WordExplanationRequest(BaseModel):
    words: List[str]
    username: str

class GrammarAnalysisRequest(BaseModel):
    text: str
    username: str

@router.post("/explain")
async def explain_words(request: WordExplanationRequest) -> Dict:
    """
    🤖 Generate AI-powered explanations for unknown words in user's native language.
    """
    try:
        ai_service = AITextAdaptationService()
        result = ai_service.generate_learning_explanation(
            unknown_words=request.words,
            username=request.username
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI explanation failed: {str(e)}")

@router.get("/ai-test")
async def test_openai_connection(db: Session = Depends(get_db)) -> Dict:
    """
    🧪 Test OpenAI API connection and configuration.
    """
    import os
    
    api_key = os.getenv("OPENAI_API_KEY", "not-set")
    
    if api_key == "not-set" or api_key == "your-openai-api-key-here":
        return {
            "status": "❌ API Key Not Set",
            "message": "Please set OPENAI_API_KEY in .env file",
            "api_key_preview": "Not configured"
        }
    
    try:
        ai_service = AITextAdaptationService()
        
        # Simple test call
        test_result = ai_service.adapt_text_with_ai(
            text="Hello world. This is a simple test.",
            username="ibrahim",
            target_unknown_percentage=10.0,
            db=db
        )
        
        if "error" in test_result:
            return {
                "status": "❌ API Error",
                "message": test_result["error"],
                "api_key_preview": f"{api_key[:7]}...{api_key[-4:]}"
            }
        
        return {
            "status": "✅ OpenAI Connected",
            "message": "AI adaptation is working correctly",
            "api_key_preview": f"{api_key[:7]}...{api_key[-4:]}",
            "test_adaptation": {
                "original": test_result["original_text"],
                "adapted": test_result["adapted_text"][:100] + "..." if len(test_result["adapted_text"]) > 100 else test_result["adapted_text"]
            }
        }
        
    except Exception as e:
        return {
            "status": "❌ Connection Failed",
            "message": str(e),
            "api_key_preview": f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 10 else "Invalid format"
        } 

@router.post("/grammar-analysis")
async def analyze_grammar(request: GrammarAnalysisRequest) -> Dict:
    """
    🔍 Grammar Analysis: Analyze text and provide grammar learning insights.
    Identifies grammar patterns, explains rules, and provides examples.
    """
    try:
        ai_service = AITextAdaptationService()
        result = ai_service.analyze_grammar(request.text, request.username)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grammar analysis failed: {str(e)}") 