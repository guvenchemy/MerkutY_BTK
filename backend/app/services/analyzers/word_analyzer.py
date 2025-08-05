import re
from typing import Dict, Any, List, Optional, Set
from collections import Counter

# spaCy'yi opsiyonel yapalım
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class WordAnalyzer:
    """
    Kelime analizi ve kullanıcı kelime istatistikleri sınıfı
    Manual proper nouns listesi kaldırıldı - artık user ignore sistemi kullanılıyor
    """
    
    def __init__(self):
        # spaCy modeli yüklemeye çalış, yoksa basit analiz yap
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.spacy_available = True
            except OSError:
                print("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                self.spacy_available = False
        else:
            self.spacy_available = False

    def is_proper_noun_or_name(self, word: str) -> bool:
        """
        Kelimenin özel isim, kişi adı veya yer adı olup olmadığını kontrol eder
        SADECE spaCy NER kullanır, manual liste kaldırıldı
        """
        # Büyük harfle başlıyor ve ortasında büyük harf var mı? (CamelCase)
        if word[0].isupper() and any(c.isupper() for c in word[1:]):
            return True
            
        # Büyük harfle başlıyor ve 2+ karakterli mi? (basit özel isim kontrolü)
        if word[0].isupper() and len(word) > 2:
            # Eğer kelime tamamen büyük harfse (ACRONYM) özel isim değil
            if not word.isupper():
                # Yaygın kelimeler değilse özel isim olabilir
                common_capitalized = {
                    'the', 'this', 'that', 'there', 'then', 'they', 'them', 'these', 'those',
                    'when', 'where', 'what', 'who', 'why', 'how', 'which', 'while', 'with',
                    'will', 'would', 'was', 'were', 'are', 'and', 'but', 'for', 'not', 'all'
                }
                word_lower = word.lower()
                if word_lower not in common_capitalized:
                    return True
        
        # spaCy varsa NER kullan
        if self.spacy_available:
            try:
                doc = self.nlp(word)
                for ent in doc.ents:
                    if ent.label_ in ['PERSON', 'GPE', 'ORG', 'LOC']:  # Person, Geopolitical entity, Organization, Location
                        return True
            except:
                pass
                
        return False

    def analyze_words(self, text: str) -> Dict[str, Any]:
        """
        Kelime düzeyinde analiz
        """
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = Counter(words)
        
        # En sık kullanılan kelimeler
        most_common = word_freq.most_common(10)
        
        # Kelime çeşitliliği
        unique_words = len(set(words))
        lexical_diversity = unique_words / len(words) if words else 0
        
        # Uzun kelimeler (7+ karakter)
        long_words = [word for word in words if len(word) >= 7]
        
        return {
            "unique_word_count": unique_words,
            "total_word_count": len(words),
            "lexical_diversity": round(lexical_diversity, 3),
            "most_frequent_words": most_common,
            "long_words_count": len(long_words),
            "long_words_examples": long_words[:10]
        }

    def get_user_known_words(self, user_id: int, db_session) -> List[str]:
        """
        Kullanıcının bilinen kelimelerini veritabanından alır
        """
        try:
            from app.services.vocabulary_service import VocabularyService
            return VocabularyService.get_user_known_words(db_session, user_id)
        except Exception as e:
            print(f"Error getting user known words: {e}")
            return []

    def get_user_ignored_words(self, user_id: int, db_session) -> Set[str]:
        """
        Kullanıcının ignore listesindeki kelimeleri veritabanından alır
        """
        try:
            from app.models.user_vocabulary import User, UserVocabulary, Vocabulary
            
            user = db_session.query(User).filter(User.id == user_id).first()
            if not user:
                return set()
            
            # Status = "ignore" olan kelimeleri getir
            user_vocab = db_session.query(UserVocabulary).filter(
                UserVocabulary.user_id == user_id,
                UserVocabulary.status == "ignore"
            ).all()
            
            ignored_words = set()
            for uv in user_vocab:
                vocab_word = db_session.query(Vocabulary).filter(
                    Vocabulary.id == uv.vocabulary_id
                ).first()
                if vocab_word:
                    ignored_words.add(vocab_word.word.lower())
            
            return ignored_words
            
        except Exception as e:
            print(f"Error getting user ignored words: {e}")
            return set()

    def get_user_vocabulary_stats(self, user_id: int, db_session, text: str) -> Dict[str, Any]:
        """
        Kullanıcının kelime istatistiklerini hesaplar
        GÜNCELLEME: Manual liste yerine user ignore sistemi kullanılıyor
        """
        try:
            from app.models.user_vocabulary import UserVocabulary, Vocabulary
            
            # Metindeki tüm kelimeleri al
            words_in_text = re.findall(r'\b\w+\b', text.lower())
            unique_words_in_text = list(set(words_in_text))
            
            # Kullanıcının bilinen kelimelerini al
            user_known_words = self.get_user_known_words(user_id, db_session)
            user_known_words_lower = [w.lower() for w in user_known_words]
            
            # Kullanıcının ignore listesini al
            user_ignored_words = self.get_user_ignored_words(user_id, db_session)
            
            # Metindeki bilinen/bilinmeyen kelime sayısı
            known_words_in_text = [w for w in unique_words_in_text if w in user_known_words_lower]
            
            # ✅ YENİ: User ignore listesi + spaCy NER ile filtreleme
            unknown_words_in_text = [
                w for w in unique_words_in_text 
                if w not in user_known_words_lower 
                and w not in user_ignored_words  # Kullanıcının ignore listesi
                and not self.is_proper_noun_or_name(w)  # Sadece spaCy NER
            ]
            
            # Kullanıcının toplam kelime bilgisi
            total_user_vocabularies = db_session.query(UserVocabulary).filter(
                UserVocabulary.user_id == user_id
            ).count()
            
            known_count = len(known_words_in_text)
            unknown_count = len(unknown_words_in_text)
            total_words = len(unique_words_in_text)
            
            known_percentage = (known_count / total_words * 100) if total_words > 0 else 0
            unknown_percentage = (unknown_count / total_words * 100) if total_words > 0 else 0
            
            return {
                "text_analysis": {
                    "total_unique_words": total_words,
                    "known_words_count": known_count,
                    "unknown_words_count": unknown_count,
                    "known_percentage": round(known_percentage, 1),
                    "unknown_percentage": round(unknown_percentage, 1),
                    "known_words_list": known_words_in_text[:20],
                    "unknown_words_list": unknown_words_in_text[:20],
                    "ignored_words_count": len(user_ignored_words)  # Yeni bilgi
                },
                "user_vocabulary_size": total_user_vocabularies,
                "i_plus_1_readiness": {
                    "is_ready": unknown_percentage >= 5 and unknown_percentage <= 15,
                    "current_unknown_percentage": round(unknown_percentage, 1),
                    "recommended_range": "5-15%",
                    "feedback": self._get_i_plus_1_feedback(unknown_percentage)
                }
            }
            
        except Exception as e:
            print(f"Error calculating user vocabulary stats: {e}")
            return {
                "text_analysis": {
                    "total_unique_words": 0,
                    "known_words_count": 0,
                    "unknown_words_count": 0,
                    "known_percentage": 0,
                    "unknown_percentage": 0,
                    "known_words_list": [],
                    "unknown_words_list": [],
                    "ignored_words_count": 0
                },
                "user_vocabulary_size": 0,
                "i_plus_1_readiness": {
                    "is_ready": False,
                    "current_unknown_percentage": 0,
                    "recommended_range": "5-15%",
                    "feedback": "Kullanıcı kelime verisi bulunamadı"
                }
            }

    def _get_i_plus_1_feedback(self, unknown_percentage: float) -> str:
        """
        i+1 metoduna göre geri bildirim
        """
        if unknown_percentage < 5:
            return "Bu metin sizin için çok kolay. Daha zor bir metin deneyin."
        elif unknown_percentage <= 15:
            return "Bu metin öğrenme için ideal seviyede! Krashen'in i+1 metoduna uygun."
        elif unknown_percentage <= 25:
            return "Bu metin biraz zor olabilir ama hala öğrenilebilir seviyede."
        else:
            return "Bu metin şu an için çok zor. Daha kolay bir metinle başlayın." 