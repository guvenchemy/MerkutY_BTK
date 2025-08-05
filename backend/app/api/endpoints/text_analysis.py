from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.text_analysis_service import TextAnalysisService
from app.services.yt_dlp_service import YTDlpService
from app.services.grammar_service import GrammarService
from app.services.vocabulary_service import VocabularyService
from app.core.database import get_db

router = APIRouter()

class TextAnalysisRequest(BaseModel):
    text: str
    include_examples: bool = True
    include_adaptation: bool = False
    user_id: Optional[int] = None  # Opsiyonel user tracking
    username: Optional[str] = None  # Username for user-specific analysis

class YouTubeAnalysisRequest(BaseModel):
    video_url: str
    include_examples: bool = True
    include_adaptation: bool = False
    user_id: Optional[int] = None

class GrammarKnowledgeRequest(BaseModel):
    user_id: int
    pattern_key: str
    status: str  # "known", "unknown", "ignored"

class TextDownloadRequest(BaseModel):
    text_type: str  # "original" or "adapted"
    text_content: str

class WordTranslationRequest(BaseModel):
    word: str
    user_id: Optional[int] = None

class VocabularyAddRequest(BaseModel):
    user_id: int
    word: str
    translation: str
    status: str  # "known", "unknown", "ignored", "learning"

class PDFGenerationRequest(BaseModel):
    analysis_data: Dict[str, Any]
    include_adaptation: bool = False

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def get_text_analysis_service():
    return TextAnalysisService()

def get_youtube_service():
    return YTDlpService()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(
    request: TextAnalysisRequest,
    text_service: TextAnalysisService = Depends(get_text_analysis_service),
    db: Session = Depends(get_db)
):
    """
    Verilen metni analiz eder ve kullanıcıya özel kelime analizi yapar
    """
    try:
        if not request.text or len(request.text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Text must be at least 10 characters long")
        
        # Username varsa user_id'yi bul
        user_id = request.user_id
        if request.username and not user_id:
            from app.models.user_vocabulary import User
            user = db.query(User).filter(User.username == request.username).first()
            if user:
                user_id = user.id
        
        # Geçici user_id oluştur (gerçek auth sistemi yoksa)
        if not user_id:
            user_id = GrammarService.create_or_get_user_by_session(db, "temp_session")
        
        # Gramer kalıplarını initialize et
        GrammarService.initialize_grammar_patterns(db)
        
        # Metin analizi yap (i+1 adaptation dahil)
        analysis_result = text_service.analyze_text(
            request.text, 
            include_adaptation=request.include_adaptation,
            user_id=user_id,
            db_session=db
        )
        
        # Örnekler istenmişse ekle (filtrelenmiş)
        if request.include_examples:
            examples = text_service.get_grammar_examples(
                request.text,
                user_id=user_id,
                db_session=db
            )
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
    youtube_service: YTDlpService = Depends(get_youtube_service)
):
    """
    YouTube videosunun transkriptini alır ve analiz eder - IP block bypass ile
    """
    try:
        # YouTube video URL'sinden video ID'sini çıkar
        video_id = youtube_service.get_video_id(request.video_url)
        
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        print(f"🎯 Analyzing YouTube video: {video_id}")
        
        # Gelişmiş transcript alma (IP block bypass ile)
        transcript_result = youtube_service.get_transcript(video_id)
        
        if not transcript_result.get("success"):
            # IP block durumunda özel mesaj
            if "IP block" in str(transcript_result.get("error", "")):
                return AnalysisResponse(
                    success=False,
                    error="🚫 YouTube IP engeli algılandı. VPN kullanarak deneyin veya farklı bir video seçin.",
                    data={
                        "bypass_suggestions": youtube_service.suggest_working_videos(),
                        "video_info": {
                            "video_id": video_id,
                            "video_url": request.video_url,
                            "status": "blocked"
                        }
                    }
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to get transcript: {transcript_result.get('error', 'Unknown error')}"
                )
        
        transcript_text = transcript_result["transcript"]
        method_used = transcript_result.get("method", "unknown")
        
        # IP block bypass durumunda demo content uyarısı
        if method_used == "manual_fallback":
            print("⚠️ Using demo content due to IP block")
        
        if len(transcript_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Transcript too short for meaningful analysis")
        
        # Transkripti analiz et (i+1 adaptation dahil)
        analysis_result = text_service.analyze_text(transcript_text, include_adaptation=request.include_adaptation)
        
        # Video bilgilerini ekle
        analysis_result["video_info"] = {
            "video_id": video_id,
            "video_url": request.video_url,
            "transcript_length": len(transcript_text),
            "method_used": method_used,
            "language": transcript_result.get("language", "unknown")
        }
        
        # IP block uyarısı varsa ekle
        if transcript_result.get("warning"):
            analysis_result["video_info"]["warning"] = transcript_result["warning"]
        
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
        print(f"❌ YouTube analysis error: {str(e)}")
        return AnalysisResponse(
            success=False,
            error=f"YouTube analysis failed: {str(e)}"
        )

@router.get("/youtube-bypass-help")
async def get_youtube_bypass_help():
    """
    YouTube IP block'u aşma yöntemleri ve çalışan video örnekleri
    """
    youtube_service = YTDlpService()
    
    return {
        "ip_block_solutions": {
            "recommended": [
                "🌐 VPN kullanın (en etkili yöntem)",
                "🔄 Farklı internet bağlantısı deneyin",
                "⏰ Daha sonra tekrar deneyin",
                "🎯 Popüler videolar yerine daha az bilinen videolar deneyin"
            ],
            "technical": [
                "Proxy server kullanın",
                "Tor browser deneyin", 
                "Mobile data ile deneyin",
                "Farklı DNS sunucuları kullanın (8.8.8.8, 1.1.1.1)"
            ]
        },
        "test_videos": youtube_service.get_popular_video_ids(),
        "working_examples": youtube_service.suggest_working_videos(),
        "troubleshooting": {
            "common_errors": {
                "TranscriptsDisabled": "Video altyazıları kapalı",
                "NoTranscriptFound": "Altyazı bulunamadı", 
                "VideoUnavailable": "Video mevcut değil",
                "TooManyRequests": "Çok fazla istek - IP block"
            },
            "solutions": {
                "IP_block": "VPN kullanın veya farklı bağlantı deneyin",
                "No_transcript": "Altyazılı başka video seçin",
                "Rate_limit": "15-30 dakika bekleyin"
            }
        }
    }

@router.post("/test-youtube-connection")
async def test_youtube_connection():
    """
    YouTube bağlantısını test eder
    """
    youtube_service = YTDlpService()
    test_video_id = "dQw4w9WgXcQ"  # Test video
    
    try:
        result = youtube_service.get_transcript(test_video_id)
        
        return {
            "connection_status": "success" if result["success"] else "failed",
            "method_used": result.get("method", "unknown"),
            "ip_blocked": "IP block" in str(result.get("error", "")),
            "transcript_length": len(result.get("transcript", "")),
            "recommendation": "✅ Bağlantı çalışıyor" if result["success"] else "❌ IP block - VPN kullanın"
        }
        
    except Exception as e:
        return {
            "connection_status": "error",
            "error": str(e),
            "ip_blocked": True,
            "recommendation": "❌ Bağlantı hatası - VPN kullanın veya daha sonra deneyin"
        }

@router.post("/translate-word")
async def translate_word(
    request: WordTranslationRequest,
    text_service: TextAnalysisService = Depends(get_text_analysis_service)
):
    """
    Tek kelime çevirir ve veritabanına ekler (opsiyonel)
    """
    try:
        if not request.word or len(request.word.strip()) < 1:
            raise HTTPException(status_code=400, detail="Word cannot be empty")
        
        # Kelimeyi çevir
        translation_result = text_service.translate_word(request.word)
        
        # TODO: Kelimeyi veritabanına ekle (user_id varsa)
        # if request.user_id:
        #     vocabulary_service.add_user_vocabulary(request.user_id, request.word, translation_result["translation"])
        
        return {
            "success": True,
            "data": translation_result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Word translation failed: {str(e)}"
        }

@router.post("/add-vocabulary")
async def add_vocabulary(
    request: VocabularyAddRequest,
    db: Session = Depends(get_db)
):
    """
    Kelimeyi kullanıcı sözlüğüne ekler ve durumunu işaretler
    """
    try:
        print(f"🔍 Adding vocabulary: user_id={request.user_id}, word='{request.word}', translation='{request.translation}', status='{request.status}'")
        
        if not request.word or len(request.word.strip()) < 1:
            raise HTTPException(status_code=400, detail="Word cannot be empty")
        
        if not request.translation or len(request.translation.strip()) < 1:
            raise HTTPException(status_code=400, detail="Translation cannot be empty")
        
        if request.status not in ['known', 'unknown', 'ignored', 'learning']:
            raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
        
        # Kelimeyi veritabanına ekle
        success = VocabularyService.add_user_vocabulary_with_translation(
            db=db,
            user_id=request.user_id,
            word=request.word,
            translation=request.translation,
            status=request.status
        )
        
        print(f"🔍 Vocabulary add result: {success}")
        
        if success:
            return {
                "success": True,
                "message": f"Word '{request.word}' added with status '{request.status}'"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add vocabulary to database")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Add vocabulary API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Add vocabulary failed: {str(e)}")

@router.post("/generate-pdf")
async def generate_pdf_report(
    request: PDFGenerationRequest,
    text_service: TextAnalysisService = Depends(get_text_analysis_service)
):
    """
    Analiz sonuçlarından PDF raporu oluşturur
    """
    try:
        # PDF oluştur
        pdf_bytes = text_service.generate_pdf_report(
            request.analysis_data, 
            include_adaptation=request.include_adaptation
        )
        
        # PDF response döndür
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=text_analysis_report.pdf"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.post("/download-text")
async def download_text(
    request: TextDownloadRequest,
    text_service: TextAnalysisService = Depends(get_text_analysis_service)
):
    """
    Orijinal veya adapte edilmiş metni PDF dosyası olarak indirir
    """
    try:
        if not request.text_content or len(request.text_content.strip()) < 5:
            raise HTTPException(status_code=400, detail="Text content is too short")
            
        # PDF oluştur
        pdf_bytes = text_service.generate_simple_text_pdf(request.text_content, request.text_type)
        
        filename = f"{request.text_type}_text.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"❌ Text PDF download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text PDF download failed: {str(e)}")

@router.post("/update-grammar-knowledge")
async def update_grammar_knowledge(
    request: GrammarKnowledgeRequest,
    db: Session = Depends(get_db)
):
    """
    Kullanıcının gramer kalıbı bilgisini günceller
    """
    try:
        success = GrammarService.update_grammar_knowledge(
            db=db,
            user_id=request.user_id,
            pattern_key=request.pattern_key,
            status=request.status
        )
        
        if success:
            return {
                "success": True,
                "message": f"Grammar pattern '{request.pattern_key}' marked as '{request.status}'"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update grammar knowledge")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.get("/grammar-patterns")
async def get_grammar_patterns(db: Session = Depends(get_db)):
    """
    Tüm gramer kalıplarını döner
    """
    try:
        patterns = GrammarService.get_all_grammar_patterns(db)
        return {
            "success": True,
            "patterns": patterns
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")

@router.get("/user-vocabulary/{user_id}")
async def get_user_vocabulary(user_id: int, db: Session = Depends(get_db)):
    """
    Kullanıcının bilinen kelimelerini döner
    """
    try:
        # Kullanıcının bilinen kelimelerini al
        known_words = VocabularyService.get_user_known_words(db, user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "known_words": known_words
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user vocabulary: {str(e)}")

@router.get("/user-grammar-knowledge/{user_id}")
async def get_user_grammar_knowledge(user_id: int, db: Session = Depends(get_db)):
    """
    Kullanıcının gramer bilgilerini döner
    """
    try:
        knowledge = GrammarService.get_user_grammar_knowledge(db, user_id)
        return {
            "success": True,
            "user_id": user_id,
            "knowledge": knowledge
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user knowledge: {str(e)}")

class SimpleTextPDFRequest(BaseModel):
    text: str
    title: str = "Text Document"
    type: str = "document"

@router.post("/simple-pdf")
async def generate_simple_text_pdf(request: SimpleTextPDFRequest):
    """
    🔄 Simple Text to PDF Generator
    Creates a PDF from plain text with minimal formatting.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT
        from io import BytesIO
        import datetime

        # Create PDF buffer
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_LEFT,
            spaceAfter=20
        )
        
        content_style = ParagraphStyle(
            'CustomContent',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_LEFT,
            leading=14
        )
        
        # Build PDF content
        story = []
        
        # Add title
        story.append(Paragraph(request.title, title_style))
        story.append(Spacer(1, 12))
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"Generated: {timestamp}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add main content - split by paragraphs
        paragraphs = request.text.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                # Clean paragraph text for reportlab
                clean_paragraph = paragraph.replace('\n', ' ').strip()
                story.append(Paragraph(clean_paragraph, content_style))
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Return PDF as response
        from fastapi.responses import Response
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={request.type}_text_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )
        
    except ImportError:
        raise HTTPException(
            status_code=500, 
            detail="PDF generation requires reportlab. Install with: pip install reportlab"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
