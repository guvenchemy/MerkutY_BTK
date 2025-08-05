from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import datetime
from app.services.text_analysis_service import TextAnalysisService
from app.services.yt_dlp_service import YTDlpService
from app.services.grammar_service import GrammarService
from app.services.vocabulary_service import VocabularyService
from app.core.database import get_db
from app.models.user_vocabulary import Vocabulary, UserVocabulary

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

class WebAnalysisRequest(BaseModel):
    web_url: str
    include_examples: bool = True
    include_adaptation: bool = False
    user_id: Optional[int] = None
    cached_content: Optional[str] = None  # Önceden cache'den alınmış content
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

class WordStatusRequest(BaseModel):
    user_id: int
    word: str

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

@router.post("/analyze-web")
async def analyze_web(request: WebAnalysisRequest, db: Session = Depends(get_db)):
    """
    🌐 Web Content Analysis
    Analyzes content from Medium and Wikipedia links
    """
    try:
        # URL validation
        if not request.web_url or not request.web_url.strip():
            raise HTTPException(status_code=400, detail="Web URL is required")
        
        url = request.web_url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Eğer cached_content varsa, web scraping'i atla
        if request.cached_content:
            print(f"🔄 Using cached content for analysis (length: {len(request.cached_content)})")
            text_content = request.cached_content
            title = "Cached Content"
            
            # URL'den site tipini belirle
            if 'medium.com' in url:
                site_type = "Medium Article"
            elif 'wikipedia.org' in url:
                site_type = "Wikipedia Article"
            else:
                site_type = "Web Content"
                
        else:
            # Cached content yoksa TextAnalysisService'den content çek
            print(f"🌐 Fetching content from web: {url}")
            text_service = TextAnalysisService()
            content_result = text_service.extract_web_content(url)
            
            if not content_result.get("success"):
                raise HTTPException(status_code=400, detail=content_result.get("error", "Failed to extract content"))
            
            content_data = content_result["data"]
            text_content = content_data.get("content", "")
            title = content_data.get("title", "Web Content")
            site_type = content_data.get("source_type", "Web Content")
        
        # Content validation
        if not text_content or len(text_content) < 50:
            raise HTTPException(status_code=400, detail="Content too short or empty")
        
        # Initialize services
        text_service = TextAnalysisService()
        
        # Analyze text
        difficulty_result = text_service.analyze_text(
            text=text_content,
            user_id=request.user_id,
            include_adaptation=request.include_examples,
            db_session=db
        )
        
        # Word count
        word_count = len(text_content.split())
        
        # Response data
        response_data = {
            "url": url,
            "title": title,
            "site_type": site_type,
            "word_count": word_count,
            "content": text_content,
            "original_text": text_content,  # Web içeriğinin kendisi original text
            "difficulty_analysis": difficulty_result,
            "cached": bool(request.cached_content)
        }
        
        # Include adaptation if requested
        if request.include_adaptation and request.user_id:
            from app.services.ai_text_adaptation_service import AITextAdaptationService
            ai_service = AITextAdaptationService()
            
            # Get username for adaptation
            from app.models.user_vocabulary import User
            user = db.query(User).filter(User.id == request.user_id).first()
            username = user.username if user else "unknown"
            
            adaptation_result = ai_service.adapt_text_with_ai(
                text=text_content,
                username=username,
                db=db,
                target_unknown_percentage=10.0
            )
            
            if not adaptation_result.get("error"):
                response_data["adaptation"] = {
                    "adapted_text": adaptation_result.get("adapted_text", text_content),
                    "original_text": text_content,  # Web içeriğinin kendisi original text
                    "adaptation_info": adaptation_result.get("adaptation_info", {}),
                    "user_level": adaptation_result.get("user_level", "A1"),
                    "method": adaptation_result.get("adaptation_method", "AI Adaptation")
                }
        
        return {
            "success": True,
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Web analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Web analysis failed: {str(e)}")
        # URL validation
        if not request.web_url or not request.web_url.strip():
            raise HTTPException(status_code=400, detail="Web URL is required")
        
        url = request.web_url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Eğer cached_content varsa, web scraping'i atla
        if request.cached_content:
            print(f"🔄 Using cached content for analysis (length: {len(request.cached_content)})")
            content_text = request.cached_content
            title = "Cached Content"
            
            # URL'den site tipini belirle
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            if 'medium.com' in domain:
                source_type = 'medium'
            elif 'wikipedia.org' in domain:
                source_type = 'wikipedia'
            else:
                source_type = 'web'
                
        else:
            # Cached content yoksa normal web scraping yap
            print(f"🌐 Fetching content from web: {url}")
            
        # Eğer cached_content varsa, web scraping'i atla
        if request.cached_content:
            print(f"🔄 Using cached content for analysis (length: {len(request.cached_content)})")
            text_content = request.cached_content
            title = "Cached Content"
            
            # URL'den site tipini belirle
            if 'medium.com' in url:
                site_type = "Medium Article"
            elif 'wikipedia.org' in url:
                site_type = "Wikipedia Article"
            else:
                site_type = "Web Content"
                
        else:
            # Cached content yoksa normal web scraping yap
            print(f"🌐 Fetching content from web: {url}")
            import requests
            from bs4 import BeautifulSoup
            from urllib.parse import urlparse            # Parse URL to check supported sites
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Check if it's a supported site
            supported_sites = ['medium.com', 'wikipedia.org', 'en.wikipedia.org', 'tr.wikipedia.org']
            is_supported = any(site in domain for site in supported_sites)
            
            if not is_supported:
                raise HTTPException(
                    status_code=400, 
                    detail="Only Medium.com and Wikipedia.org links are supported"
                )
            
            # Fetch content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse content based on site type
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if 'medium.com' in domain:
                source_type = 'medium'
            # Medium content extraction with comprehensive filtering
            # First, remove unwanted elements from entire page
            for unwanted in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 
                                          'aside', 'figure', 'figcaption', 'img']):
                unwanted.decompose()
            
            # Remove Medium-specific metadata elements
            for unwanted in soup.find_all(['h1', 'h2', 'h3']):  # Remove titles/headings
                unwanted.decompose()
            
            # Remove author info, dates, reading time, etc.
            for selector in ['[data-testid="authorName"]', '[data-testid="storyPublishDate"]',
                           '[data-testid="storyReadTime"]', '[class*="readingTime"]',
                           '[class*="followButton"]', '[class*="metabar"]',
                           '[class*="highlight"]', '[class*="clap"]',
                           '[class*="bookmark"]', '[class*="share"]',
                           '[class*="byline"]', '[class*="userInfo"]', '[class*="authorInfo"]']:
                for element in soup.select(selector):
                    element.decompose()
            
            # Now find the main content
            content_div = soup.find('article') or soup.find('div', class_='postArticle-content')
            if not content_div:
                content_div = soup.find('div', {'data-testid': 'storyContent'})
            
            if content_div:
                # Get only paragraph text
                paragraphs = content_div.find_all('p')
                text_content = ' '.join([p.get_text(strip=True) for p in paragraphs 
                                       if p.get_text(strip=True) and len(p.get_text(strip=True)) > 30])
            else:
                # Fallback: get all paragraphs from body
                paragraphs = soup.find_all('p')
                text_content = ' '.join([p.get_text(strip=True) for p in paragraphs 
                                       if len(p.get_text(strip=True)) > 30])
            
            # Advanced cleaning for Medium-specific patterns
            import re
            # Remove reading time patterns
            text_content = re.sub(r'\d+\s*min\s*read', '', text_content, flags=re.IGNORECASE)
            # Remove date patterns (various formats)
            text_content = re.sub(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}', '', text_content)
            text_content = re.sub(r'\d{1,2}\/\d{1,2}\/\d{4}', '', text_content)
            text_content = re.sub(r'\d{4}-\d{2}-\d{2}', '', text_content)
            # Remove social elements
            text_content = re.sub(r'\b(Follow|Share|Clap|Highlight|Bookmark|Subscribe|Published in|Member-only)\b', '', text_content, flags=re.IGNORECASE)
            # Remove figure/image references
            text_content = re.sub(r'Figure\s*\d+', '', text_content, flags=re.IGNORECASE)
            text_content = re.sub(r'Image\s*(by|from|via|source)\s*[^.]*', '', text_content, flags=re.IGNORECASE)
            # Remove email addresses
            text_content = re.sub(r'\S+@\S+\.\S+', '', text_content)
            # Remove author bylines
            text_content = re.sub(r'By\s+[A-Z][a-z]+\s+[A-Z][a-z]+', '', text_content)
            # Remove "Written by" patterns
            text_content = re.sub(r'Written by\s+[^.]*', '', text_content, flags=re.IGNORECASE)
            
            site_type = "Medium Article"
            
            
            # Clean up text content
            import re
            text_content = re.sub(r'\s+', ' ', text_content)  # Remove extra whitespace
        
        if len(text_content.strip()) < 100:
            raise HTTPException(
                status_code=400, 
                detail="Extracted content is too short for meaningful analysis"
            )
        
        # Limit content length (optional)
        if len(text_content) > 50000:
            text_content = text_content[:50000] + "..."
        
        # Initialize text analysis service
        text_service = TextAnalysisService()
        
        # User ID'yi al veya oluştur
        user_id = request.user_id
        if not user_id:
            user_id = GrammarService.create_or_get_user_by_session(db, "temp_session")
        
        # Gramer kalıplarını initialize et
        GrammarService.initialize_grammar_patterns(db)
        
        # Analyze extracted text with user context
        analysis_result = text_service.analyze_text(
            text_content, 
            include_adaptation=request.include_adaptation,
            user_id=user_id,
            db_session=db
        )
        
        # Adaptation bilgilerini düzenle (YouTube formatına uygun hale getir)
        if request.include_adaptation and "adapted_text" in analysis_result:
            # YouTube library format'ına uygun adaptation objesi oluştur
            adaptation_data = {
                "adapted_text": analysis_result["adapted_text"],
                "original_text": text_content,
                "word_analysis": analysis_result.get("word_analysis"),
                "analysis": analysis_result.get("analysis", {})
            }
            analysis_result["adaptation"] = adaptation_data
        
        # Add web source information
        analysis_result["web_info"] = {
            "source_url": url,
            "site_type": site_type,
            "domain": domain,
            "content_length": len(text_content),
            "extracted_at": str(datetime.datetime.now())
        }
        
        # Add examples if requested
        if request.include_examples:
            examples = text_service.get_grammar_examples(text_content)
            analysis_result["grammar_examples"] = examples
        
        return AnalysisResponse(
            success=True,
            data=analysis_result
        )
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to fetch content from URL: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Web analysis error: {str(e)}")
        return AnalysisResponse(
            success=False,
            error=f"Web analysis failed: {str(e)}"
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
        result = VocabularyService.add_user_vocabulary_with_translation(
            db=db,
            user_id=request.user_id,
            word=request.word,
            translation=request.translation,
            status=request.status
        )
        
        print(f"🔍 Vocabulary add result: {result}")
        
        if result["success"]:
            message = f"Word '{request.word}' added with status '{request.status}'"
            if result["is_new"]:
                message += " (new word added to your vocabulary)"
            else:
                message += f" (status updated: {result['action']})"
                
            return {
                "success": True,
                "message": message,
                "is_new": result["is_new"],
                "action": result["action"]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add vocabulary to database")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Add vocabulary API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Add vocabulary failed: {str(e)}")

@router.post("/word-status")
async def get_word_status(
    request: WordStatusRequest,  # Özel request model'ini kullan
    db: Session = Depends(get_db)
):
    """
    Kullanıcının belirli bir kelimeye sahip olup olmadığını ve status'unu kontrol eder
    """
    try:
        print(f"🔍 Checking word status: user_id={request.user_id}, word='{request.word}'")
        
        if not request.word or len(request.word.strip()) < 1:
            return {"success": False, "error": "Word cannot be empty"}
        
        # Kelimeyi temizle
        clean_word = request.word.strip().lower()
        
        # Vocabulary tablosundan kelimeyi bul
        vocab = db.query(Vocabulary).filter(
            Vocabulary.word == clean_word,
            Vocabulary.language == "en"
        ).first()
        
        print(f"🔍 Vocabulary lookup result: {vocab}")
        
        if not vocab:
            print(f"🔍 Word '{clean_word}' not found in vocabulary table")
            return {"success": True, "status": None, "message": "Word not in vocabulary"}
        
        print(f"🔍 Found vocabulary with ID: {vocab.id}")
        
        # UserVocabulary tablosundan kullanıcının bu kelimeye sahip olup olmadığını kontrol et
        user_vocab = db.query(UserVocabulary).filter(
            UserVocabulary.user_id == request.user_id,
            UserVocabulary.vocabulary_id == vocab.id
        ).first()
        
        print(f"🔍 UserVocabulary lookup result: {user_vocab}")
        
        if user_vocab:
            print(f"🔍 User has word with status: {user_vocab.status}")
            return {
                "success": True,
                "status": user_vocab.status,
                "word": clean_word,
                "message": f"User has this word with status: {user_vocab.status}"
            }
        else:
            print(f"🔍 User doesn't have this word")
            return {
                "success": True,
                "status": None,
                "word": clean_word,
                "message": "User doesn't have this word"
            }
            
    except Exception as e:
        print(f"❌ Word status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Word status check failed: {str(e)}")

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
