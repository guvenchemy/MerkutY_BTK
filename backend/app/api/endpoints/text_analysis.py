from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.text_analysis_service import TextAnalysisService
from app.services.youtube_service import YouTubeService

router = APIRouter()

class TextAnalysisRequest(BaseModel):
    text: str
    include_examples: bool = True

class YouTubeAnalysisRequest(BaseModel):
    video_url: str
    include_examples: bool = True

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def get_text_analysis_service():
    return TextAnalysisService()

def get_youtube_service():
    return YouTubeService()

@router.post("/analyze-text", response_model=AnalysisResponse)
async def analyze_text(
    request: TextAnalysisRequest,
    text_service: TextAnalysisService = Depends(get_text_analysis_service)
):
    """
    Verilen metni analiz eder ve gramer bilgileri döner
    """
    try:
        if not request.text or len(request.text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Text must be at least 10 characters long")
        
        # Metin analizi yap
        analysis_result = text_service.analyze_text(request.text)
        
        # Örnekler istenmişse ekle
        if request.include_examples:
            examples = text_service.get_grammar_examples(request.text)
            analysis_result["grammar_examples"] = examples
        
        return AnalysisResponse(
            success=True,
            data=analysis_result
        )
    
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=f"Text analysis failed: {str(e)}"
        )

@router.post("/analyze-youtube", response_model=AnalysisResponse)
async def analyze_youtube_transcript(
    request: YouTubeAnalysisRequest,
    text_service: TextAnalysisService = Depends(get_text_analysis_service),
    youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """
    YouTube videosunun transkriptini alır ve analiz eder
    """
    try:
        # YouTube video URL'sinden video ID'sini çıkar
        import re
        
        # YouTube URL pattern'leri
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        video_id = None
        for pattern in patterns:
            match = re.search(pattern, request.video_url)
            if match:
                video_id = match.group(1)
                break
        
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Transkripti al
        transcript_result = youtube_service.get_transcript(video_id)
        
        if not transcript_result.get("success"):
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to get transcript: {transcript_result.get('error', 'Unknown error')}"
            )
        
        transcript_text = transcript_result["transcript"]
        
        if len(transcript_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Transcript too short for meaningful analysis")
        
        # Transkripti analiz et
        analysis_result = text_service.analyze_text(transcript_text)
        
        # Video bilgilerini ekle
        analysis_result["video_info"] = {
            "video_id": video_id,
            "video_url": request.video_url,
            "transcript_length": len(transcript_text)
        }
        
        # Örnekler istenmişse ekle
        if request.include_examples:
            examples = text_service.get_grammar_examples(transcript_text)
            analysis_result["grammar_examples"] = examples
        
        return AnalysisResponse(
            success=True,
            data=analysis_result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=f"YouTube analysis failed: {str(e)}"
        )

@router.get("/analysis-info")
async def get_analysis_info():
    """
    Metin analizi hakkında bilgi döner
    """
    return {
        "supported_features": [
            "Basic text statistics (word count, sentence count, etc.)",
            "Grammar analysis (parts of speech, sentence structure)",
            "Word frequency analysis",
            "AI-powered language level assessment",
            "Grammar examples extraction",
            "YouTube transcript analysis"
        ],
        "analysis_categories": {
            "basic_statistics": "Character count, word count, reading time estimation",
            "grammar_analysis": "Part of speech distribution, sentence complexity",
            "word_analysis": "Vocabulary richness, word frequency",
            "ai_insights": "Language level assessment and learning recommendations"
        },
        "supported_inputs": [
            "Plain text (minimum 10 characters)",
            "YouTube video URLs (with available transcripts)"
        ],
        "example_usage": {
            "text_analysis": "POST /api/analysis/analyze-text with JSON body: {'text': 'Your text here', 'include_examples': true}",
            "youtube_analysis": "POST /api/analysis/analyze-youtube with JSON body: {'video_url': 'https://youtube.com/watch?v=...', 'include_examples': true}"
        }
    }
