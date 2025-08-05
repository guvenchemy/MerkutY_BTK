import os
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from .analyzers.basic_statistics import BasicStatistics
from .analyzers.word_analyzer import WordAnalyzer


class TextAnalysisService:
    """
    Refactored Text Analysis Service
    Modular approach ile daha maintainable kod yapısı
    """
    
    def __init__(self):
        # Gemini API'yi konfigüre et
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Analyzer instance'larını oluştur
        self.basic_stats = BasicStatistics()
        self.word_analyzer = WordAnalyzer()

    def analyze_text(self, text: str, include_adaptation: bool = False, user_id: Optional[int] = None, db_session = None) -> Dict[str, Any]:
        """
        Verilen metni kapsamlı bir şekilde analiz eder
        user_id ve db_session varsa bilinen gramer kalıplarını filtreler
        """
        try:
            # Temel istatistikler
            basic_stats = self.basic_stats.get_basic_statistics(text)
            
            # Kelime analizi
            word_analysis = self.word_analyzer.analyze_words(text)
            
            # Kullanıcı kelime istatistikleri (eğer user_id ve db_session varsa)
            user_vocabulary_stats = None
            word_analysis_for_coloring = None
            if user_id and db_session:
                user_vocabulary_stats = self.word_analyzer.get_user_vocabulary_stats(user_id, db_session, text)
                
                # Word analysis for frontend coloring
                from app.services.text_adaptation_service import TextAdaptationService
                user_known_words = self.word_analyzer.get_user_known_words(user_id, db_session)
                
                # Get username for word analysis
                from app.models.user_vocabulary import User
                user = db_session.query(User).filter(User.id == user_id).first()
                username = user.username if user else None
                
                word_analysis_for_coloring = TextAdaptationService.get_word_analysis_for_coloring(
                    text, set(user_known_words), username, db_session
                )
            
            # AI destekli analiz (Türkçe açıklamalar)
            ai_analysis = self._get_ai_analysis_turkish(text)
            
            # i+1 adaptation (opsiyonel) - kullanıcının bilinen kelimeleri ile
            adapted_text = None
            if include_adaptation:
                user_known_words = []
                if user_id and db_session:
                    user_known_words = self.word_analyzer.get_user_known_words(user_id, db_session)
                adapted_text = self._generate_i_plus_1_adaptation(text, user_known_words)
            
            result = {
                "original_text": text,
                "basic_statistics": basic_stats,
                "word_analysis": word_analysis,
                "ai_insights": ai_analysis,
                "text_sample": text[:200] + "..." if len(text) > 200 else text
            }
            
            # Kullanıcı istatistikleri varsa ekle
            if user_vocabulary_stats:
                result["user_vocabulary_stats"] = user_vocabulary_stats
                result["analysis"] = user_vocabulary_stats["text_analysis"]
            
            # Word analysis for coloring varsa ekle
            if word_analysis_for_coloring:
                result["word_analysis"] = word_analysis_for_coloring
            
            # i+1 adaptation varsa ekle
            if adapted_text:
                result["adapted_text"] = adapted_text
                
            return result
        except Exception as e:
            return {"error": f"Text analysis failed: {str(e)}"}

    def _get_ai_analysis_turkish(self, text: str) -> Dict[str, str]:
        """
        Gemini AI kullanarak Türkçe analiz
        """
        try:
            # Metni kısalt (token limiti için)
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            prompt = f"""Bu İngilizce metni analiz edip Türkçe açıklama yap:

Metin: "{text}"

Şu başlıklar altında 3-4 cümlelik kısa analiz yap:
1. DİL SEVİYESİ: (A1-C2 arası seviye ve açıklama)
2. GRAMER YAPILARI: (Kullanılan ana gramer kalıpları)
3. KELİME HAZİNESİ: (Kelime zorluğu ve çeşitliliği)
4. ÖĞRENME ÖNERİSİ: (Bu metinle nasıl çalışılmalı)

Maksimum 150 kelime kullan."""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return {
                    "ai_analysis_turkish": response.text.strip(),
                    "analysis_language": "Turkish",
                    "generated_by": "Gemini AI"
                }
            else:
                return {
                    "ai_analysis_turkish": "AI analizi şu anda mevcut değil. Lütfen daha sonra tekrar deneyin.",
                    "error": "Empty response from Gemini"
                }
                
        except Exception as e:
            print(f"AI Analysis Error: {str(e)}")
            return {
                "ai_analysis_turkish": f"AI analizi yapılamadı: {str(e)}",
                "error": str(e)
            }

    def _generate_i_plus_1_adaptation(self, text: str, user_known_words: List[str] = None) -> Dict[str, str]:
        """
        i+1 metoduna göre metin adaptasyonu
        """
        try:
            if not user_known_words:
                user_known_words = []
            
            if len(text) > 1500:
                text = text[:1500] + "..."
            
            known_words_str = ', '.join(user_known_words[:50]) if user_known_words else "temel İngilizce kelimeler"
            
            prompt = f"""Bu metni Krashen'in i+1 metoduna göre adapte et:

ORİJİNAL METİN: "{text}"

KULLANICININ BİLDİĞİ KELİMELER: {known_words_str}

KURALLAR:
- Metnin anlamını koruyarak yeniden yaz
- %85-90 bilinen kelime, %10-15 yeni kelime kullan
- Gramer yapısını basitleştir ama doğal tut
- Yaklaşık aynı uzunlukta olsun

Sadece adapte edilmiş metni ver, açıklama yapma."""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return {
                    "adapted_text": response.text.strip(),
                    "adaptation_method": "i+1 AI Adaptation",
                    "adaptation_info": "Krashen'in i+1 metoduna göre adapte edildi"
                }
            else:
                return {
                    "adapted_text": "Adapte edilmiş metin oluşturulamadı.",
                    "error": "Empty response from Gemini"
                }
                
        except Exception as e:
            print(f"i+1 Adaptation Error: {str(e)}")
            return {
                "adapted_text": f"Metin adaptasyonu yapılamadı: {str(e)}",
                "error": str(e)
            } 