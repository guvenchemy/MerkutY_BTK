import re
from typing import Dict, List, Any, Optional
import os
from collections import Counter
import google.generativeai as genai

# spaCy'yi opsiyonel yapalım
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("spaCy not installed. Install with: pip install spacy")


class TextAnalysisService:
    def __init__(self):
        # Gemini API'yi konfigüre et
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
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
            
        # İsim olarak kabul edilecek kelimeler (işaretlenmeyecek)
        self.proper_nouns = {
            # Kişi adları
            'john', 'mary', 'david', 'sarah', 'michael', 'jennifer', 'james', 'lisa',
            'robert', 'susan', 'william', 'karen', 'richard', 'nancy', 'thomas', 'betty',
            'charles', 'helen', 'christopher', 'sandra', 'daniel', 'donna', 'matthew', 'carol',
            'anthony', 'ruth', 'mark', 'sharon', 'donald', 'michelle', 'steven', 'laura',
            'paul', 'sarah', 'andrew', 'kimberly', 'joshua', 'deborah', 'kenneth', 'dorothy',
            
            # Yer adları
            'london', 'paris', 'tokyo', 'newyork', 'california', 'texas', 'florida', 'chicago',
            'boston', 'washington', 'seattle', 'atlanta', 'miami', 'denver', 'phoenix', 'dallas',
            'houston', 'philadelphia', 'detroit', 'cleveland', 'baltimore', 'milwaukee',
            'england', 'france', 'germany', 'italy', 'spain', 'japan', 'china', 'brazil',
            'canada', 'australia', 'india', 'mexico', 'russia', 'turkey', 'greece', 'portugal',
            'america', 'europe', 'asia', 'africa', 'antarctica', 'america', 'united', 'states',
            
            # Şirket/Marka adları
            'google', 'apple', 'microsoft', 'amazon', 'facebook', 'twitter', 'instagram',
            'youtube', 'netflix', 'disney', 'coca', 'cola', 'mcdonald', 'walmart', 'target',
            'starbucks', 'nike', 'adidas', 'samsung', 'sony', 'toyota', 'ford', 'bmw',
            
            # Günler ve aylar
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
            'september', 'october', 'november', 'december',
            
            # Diller ve milletler
            'english', 'spanish', 'french', 'german', 'italian', 'chinese', 'japanese',
            'russian', 'portuguese', 'arabic', 'turkish', 'american', 'british', 'french',
            'german', 'italian', 'spanish', 'chinese', 'japanese', 'russian', 'turkish'
        }

    def _is_proper_noun_or_name(self, word: str) -> bool:
        """
        Kelimenin özel isim, kişi adı veya yer adı olup olmadığını kontrol eder
        """
        word_lower = word.lower()
        
        # Bilinen isimler listesinde mi?
        if word_lower in self.proper_nouns:
            return True
            
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

    def analyze_text(self, text: str, include_adaptation: bool = False, user_id: Optional[int] = None, db_session = None) -> Dict[str, Any]:
        """
        Verilen metni kapsamlı bir şekilde analiz eder
        user_id ve db_session varsa bilinen gramer kalıplarını filtreler
        """
        try:
            # Temel istatistikler
            basic_stats = self._get_basic_statistics(text)
            
            # Gramer analizi
            grammar_analysis = self._analyze_grammar(text)
            
            # Kelime analizi
            word_analysis = self._analyze_words(text)
            
            # Kullanıcı kelime istatistikleri (eğer user_id ve db_session varsa)
            user_vocabulary_stats = None
            if user_id and db_session:
                user_vocabulary_stats = self._get_user_vocabulary_stats(user_id, db_session, text)
            
            # AI destekli analiz (Türkçe açıklamalar)
            ai_analysis = self._get_ai_analysis_turkish(text)
            
            # i+1 adaptation (opsiyonel) - kullanıcının bilinen kelimeleri ile
            adapted_text = None
            if include_adaptation:
                user_known_words = []
                if user_id and db_session:
                    user_known_words = self._get_user_known_words(user_id, db_session)
                adapted_text = self._generate_i_plus_1_adaptation(text, user_known_words)
            
            result = {
                "original_text": text,
                "basic_statistics": basic_stats,
                "grammar_analysis": grammar_analysis,
                "word_analysis": word_analysis,
                "ai_insights": ai_analysis,
                "text_sample": text[:200] + "..." if len(text) > 200 else text
            }
            
            # Kullanıcı istatistikleri varsa ekle
            if user_vocabulary_stats:
                result["user_vocabulary_stats"] = user_vocabulary_stats
            
            # i+1 adaptation varsa ekle
            if adapted_text:
                result["adapted_text"] = adapted_text
                
            return result
        except Exception as e:
            return {"error": f"Text analysis failed: {str(e)}"}

    def _get_user_known_words(self, user_id: int, db_session) -> List[str]:
        """
        Kullanıcının bilinen kelimelerini veritabanından alır
        """
        try:
            from app.services.vocabulary_service import VocabularyService
            return VocabularyService.get_user_known_words(db_session, user_id)
        except Exception as e:
            print(f"Error getting user known words: {e}")
            return []

    def _get_user_vocabulary_stats(self, user_id: int, db_session, text: str) -> Dict[str, Any]:
        """
        Kullanıcının kelime istatistiklerini hesaplar
        """
        try:
            from app.models.user_vocabulary import UserVocabulary, Vocabulary
            
            # Metindeki tüm kelimeleri al
            words_in_text = re.findall(r'\b\w+\b', text.lower())
            unique_words_in_text = list(set(words_in_text))
            
            # Kullanıcının bilinen kelimelerini al
            user_known_words = self._get_user_known_words(user_id, db_session)
            user_known_words_lower = [w.lower() for w in user_known_words]
            
            # Metindeki bilinen/bilinmeyen kelime sayısı
            known_words_in_text = [w for w in unique_words_in_text if w in user_known_words_lower]
            unknown_words_in_text = [w for w in unique_words_in_text if w not in user_known_words_lower and not self._is_proper_noun_or_name(w)]
            
            # Kullanıcının toplam kelime bilgisi
            total_user_vocabularies = db_session.query(UserVocabulary).filter(
                UserVocabulary.user_id == user_id
            ).count()
            
            known_vocabularies = db_session.query(UserVocabulary).filter(
                UserVocabulary.user_id == user_id,
                UserVocabulary.status.in_(['known', 'learning'])
            ).count()
            
            # Seviye hesaplama
            if known_vocabularies < 500:
                level = "Beginner (A1-A2)"
                level_score = 1
            elif known_vocabularies < 1500:
                level = "Elementary (A2-B1)"
                level_score = 2
            elif known_vocabularies < 3000:
                level = "Intermediate (B1-B2)"
                level_score = 3
            elif known_vocabularies < 5000:
                level = "Upper-Intermediate (B2-C1)"
                level_score = 4
            else:
                level = "Advanced (C1-C2)"
                level_score = 5
            
            # Metin zorluğu değerlendirmesi
            text_difficulty = "Uygun"
            if len(unknown_words_in_text) > len(known_words_in_text):
                text_difficulty = "Zor"
            elif len(unknown_words_in_text) < len(known_words_in_text) * 0.1:
                text_difficulty = "Kolay"
            
            return {
                "user_level": level,
                "level_score": level_score,
                "total_known_words": known_vocabularies,
                "total_vocabulary_entries": total_user_vocabularies,
                "text_analysis": {
                    "total_unique_words_in_text": len(unique_words_in_text),
                    "known_words_in_text": len(known_words_in_text),
                    "unknown_words_in_text": len(unknown_words_in_text),
                    "comprehension_rate": round((len(known_words_in_text) / len(unique_words_in_text)) * 100, 1) if unique_words_in_text else 0,
                    "text_difficulty": text_difficulty,
                    "unknown_word_examples": unknown_words_in_text[:10]
                }
            }
            
        except Exception as e:
            print(f"Error calculating user vocabulary stats: {e}")
            return None

    def _get_basic_statistics(self, text: str) -> Dict[str, Any]:
        """
        Metinin temel istatistiklerini hesaplar
        """
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words = re.findall(r'\b\w+\b', text.lower())
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Ortalama kelime uzunluğu
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Ortalama cümle uzunluğu
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "average_word_length": round(avg_word_length, 2),
            "average_sentence_length": round(avg_sentence_length, 2),
            "reading_time_minutes": round(len(words) / 200, 1)  # Ortalama okuma hızı 200 kelime/dakika
        }

    def _analyze_grammar(self, text: str) -> Dict[str, Any]:
        """
        Gramer yapısını analiz eder
        """
        if self.spacy_available:
            return self._spacy_grammar_analysis(text)
        else:
            return self._basic_grammar_analysis(text)

    def _spacy_grammar_analysis(self, text: str) -> Dict[str, Any]:
        """
        spaCy kullanarak detaylı gramer analizi
        """
        doc = self.nlp(text)
        
        # POS (Part of Speech) etiketleri
        pos_counts = Counter([token.pos_ for token in doc if not token.is_space])
        
        # Named Entity Recognition
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        # Dependency parsing - cümle yapısı
        sentence_structures = []
        for sent in doc.sents:
            root_verb = None
            for token in sent:
                if token.dep_ == "ROOT":
                    root_verb = token.text
                    break
            sentence_structures.append({
                "sentence": sent.text.strip(),
                "root_verb": root_verb,
                "length": len([t for t in sent if not t.is_space])
            })
        
        return {
            "part_of_speech_distribution": dict(pos_counts),
            "named_entities": entities[:10],  # İlk 10 entity
            "sentence_structures": sentence_structures[:5],  # İlk 5 cümle
            "complex_sentences": len([s for s in sentence_structures if s["length"] > 15]),
            "total_sentences": len(sentence_structures)
        }

    def _basic_grammar_analysis(self, text: str) -> Dict[str, Any]:
        """
        spaCy olmadan temel gramer analizi
        """
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Temel kelime türleri (yaklaşık)
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Basit hesaplamalar
        question_sentences = len(re.findall(r'\?', text))
        exclamation_sentences = len(re.findall(r'!', text))
        
        # Gramer yapıları ve örnekleri
        grammar_patterns = self._detect_grammar_patterns(text, sentences)
        
        return {
            "sentence_types": {
                "total": len(sentences),
                "questions": question_sentences,
                "exclamations": exclamation_sentences,
                "statements": len(sentences) - question_sentences - exclamation_sentences
            },
            "grammar_patterns": grammar_patterns,
            "complexity_indicators": self._analyze_complexity(text, sentences)
        }

    def _detect_grammar_patterns(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """
        Metindeki gramer yapılarını tespit eder ve örnekler verir
        """
        patterns = []
        
        # Zaman formları (Tenses)
        tense_patterns = {
            "Present Simple": {
                "indicators": [r'\b(am|is|are)\b', r'\b(do|does)\b', r'\bwork[s]?\b', r'\blive[s]?\b'],
                "examples": [],
                "explanation": "Genel gerçekler, alışkanlıklar ve rutin eylemler için kullanılır. Örneğin: 'Su 100 derecede kaynar' veya 'Her sabah kahve içerim' gibi durumlar için kullanılır. İngilizce'de en temel zaman formudur.",
                "detailed_info": "Present Simple Tense - Geniş Zaman"
            },
            "Present Continuous": {
                "indicators": [r'\b(am|is|are)\s+\w+ing\b'],
                "examples": [],
                "explanation": "Şu anda devam eden eylemler için kullanılır. Konuşma anında olan veya geçici durumlar için kullanılır. 'am/is/are + fiil+ing' yapısıyla kurulur. Şu an bu metni okuyorsunuz - bu Present Continuous'a örnektir.",
                "detailed_info": "Present Continuous Tense - Şimdiki Zaman"
            },
            "Past Simple": {
                "indicators": [r'\b(was|were)\b', r'\b\w+ed\b', r'\b(went|came|saw|did)\b'],
                "examples": [],
                "explanation": "Geçmişte belirli bir zamanda tamamlanan eylemler için kullanılır. Düzenli fiillere '-ed' eklenir, düzensiz fiillerin özel halleri vardır. 'Dün sinemaya gittim' gibi geçmişteki tamamlanmış olayları anlatır.",
                "detailed_info": "Past Simple Tense - Geçmiş Zaman"
            },
            "Present Perfect": {
                "indicators": [r'\b(have|has)\s+\w+ed\b', r'\b(have|has)\s+(been|gone|done|seen)\b'],
                "examples": [],
                "explanation": "Geçmişte başlayıp şimdiye kadar devam eden veya şimdi tamamlanan eylemler için kullanılır. 'have/has + past participle' yapısıyla kurulur. Geçmişle şimdi arasında bağlantı kurar ve sonucun şimdi önemli olduğunu gösterir.",
                "detailed_info": "Present Perfect Tense - Şimdiki Zamanın Hikayesi"
            },
            "Future": {
                "indicators": [r'\bwill\s+\w+\b', r'\bgoing\s+to\s+\w+\b', r'\bshall\s+\w+\b'],
                "examples": [],
                "explanation": "Gelecekte olacak eylemler için kullanılır. 'will + fiil' ani kararlar için, 'going to + fiil' planlanan eylemler için kullanılır. Tahminler, vaatler ve gelecek planları ifade eder.",
                "detailed_info": "Future Tense - Gelecek Zaman"
            }
        }
        
        # Modal verbs
        modal_patterns = {
            "Modal Verbs": {
                "indicators": [r'\b(can|could|may|might|must|should|would|will|shall)\s+\w+\b'],
                "examples": [],
                "explanation": "Yetenek, izin, zorunluluk, tavsiye gibi kavramları ifade eder. 'Can' yetenek, 'must' zorunluluk, 'should' tavsiye anlamında kullanılır. Modal fiillerden sonra ana fiil infinitive (to'suz) halinde gelir.",
                "detailed_info": "Modal Verbs - Yardımcı Fiiller"
            }
        }
        
        # Conditional sentences
        conditional_patterns = {
            "Conditional Sentences": {
                "indicators": [r'\bif\s+.*,.*will\b', r'\bif\s+.*would\b', r'\bunless\s+\w+'],
                "examples": [],
                "explanation": "Şartlı durumları ifade eder (eğer-ise yapıları). Type 1: gerçek durumlar (if + present, will + infinitive), Type 2: hayali durumlar (if + past, would + infinitive). Sebep-sonuç ilişkisi kurar ve varsayımsal durumları anlatır.",
                "detailed_info": "Conditional Sentences - Şartlı Cümleler"
            }
        }
        
        # Passive voice
        passive_patterns = {
            "Passive Voice": {
                "indicators": [r'\b(am|is|are|was|were)\s+\w+ed\b', r'\bwas\s+\w+en\b'],
                "examples": [],
                "explanation": "Eylemin yapanından çok eyleme odaklanır. 'be + past participle' yapısıyla kurulur. Eylemi yapan kişi önemli değilse veya bilinmiyorsa kullanılır. Formal yazımda sıkça tercih edilir.",
                "detailed_info": "Passive Voice - Edilgen Çatı"
            }
        }
        
        # Relative clauses
        relative_patterns = {
            "Relative Clauses": {
                "indicators": [r'\b(who|which|that|where|when)\s+\w+'],
                "examples": [],
                "explanation": "İsmi tanımlayan ve açıklayan yan cümleler. 'Who' kişiler için, 'which' nesneler için, 'that' her ikisi için kullanılır. Cümleyi uzatmadan ek bilgi vermeyi sağlar ve metni daha akıcı hale getirir.",
                "detailed_info": "Relative Clauses - İlgi Zamirli Cümleler"
            }
        }
        
        # Comparatives and superlatives
        comparison_patterns = {
            "Comparatives & Superlatives": {
                "indicators": [r'\b\w+er\s+than\b', r'\bmore\s+\w+\s+than\b', r'\bthe\s+\w+est\b', r'\bthe\s+most\s+\w+\b'],
                "examples": [],
                "explanation": "Karşılaştırma ve üstünlük ifadeleri. Kısa sıfatlara '-er/-est' eklenir, uzun sıfatlarla 'more/most' kullanılır. İki şeyi karşılaştırmak veya bir grupta en üstün olanı belirtmek için kullanılır.",
                "detailed_info": "Comparatives & Superlatives - Karşılaştırma Dereceleri"
            }
        }
        
        # Common idioms and expressions
        idiom_patterns = {
            "Common Idioms": {
                "indicators": [
                    r'\bmake\s+up\s+\w+\s+mind\b', r'\bbreak\s+the\s+ice\b', r'\bpiece\s+of\s+cake\b',
                    r'\braining\s+cats\s+and\s+dogs\b', r'\bonce\s+in\s+a\s+\w+\s+moon\b',
                    r'\bbetter\s+late\s+than\s+never\b', r'\bkill\s+\w+\s+birds\s+with\s+\w+\s+stone\b',
                    r'\bball\s+is\s+in\s+\w+\s+court\b', r'\bcut\s+to\s+the\s+chase\b',
                    r'\bit\'s\s+a\s+small\s+world\b', r'\btime\s+flies\b', r'\bmoney\s+talks\b',
                    r'\bno\s+pain,?\s+no\s+gain\b', r'\bactions?\s+speak\s+louder\s+than\s+words\b',
                    r'\bdon\'t\s+count\s+your\s+chickens\b', r'\bevery\s+cloud\s+has\s+a\s+silver\s+lining\b',
                    r'\bthe\s+early\s+bird\s+catches\s+the\s+worm\b', r'\bwhen\s+pigs\s+fly\b'
                ],
                "examples": [],
                "explanation": "Deyimler ve kalıp ifadeler. Kelimelerin literal anlamından farklı bir anlam taşır. Günlük konuşmada ve yazılı dilde yaygın kullanılır ve dili daha doğal kılar.",
                "detailed_info": "Common Idioms - Yaygın Deyimler"
            }
        }
        
        # Phrasal verbs
        phrasal_verb_patterns = {
            "Phrasal Verbs": {
                "indicators": [
                    r'\bget\s+up\b', r'\bput\s+on\b', r'\btake\s+off\b', r'\brun\s+out\s+of\b',
                    r'\blook\s+for\b', r'\bfind\s+out\b', r'\bturn\s+on\b', r'\bturn\s+off\b',
                    r'\bgive\s+up\b', r'\bcome\s+back\b', r'\bgo\s+on\b', r'\bmake\s+up\b',
                    r'\bbreak\s+down\b', r'\bwork\s+out\b', r'\bshow\s+up\b', r'\bpick\s+up\b',
                    r'\btake\s+care\s+of\b', r'\blook\s+after\b', r'\bget\s+along\s+with\b',
                    r'\bcome\s+across\b', r'\bgo\s+through\b', r'\bput\s+up\s+with\b',
                    r'\brun\s+into\b', r'\bturn\s+out\b', r'\bcarry\s+out\b', r'\bbring\s+up\b',
                    r'\bset\s+up\b', r'\btake\s+up\b', r'\bgive\s+in\b', r'\bhold\s+on\b'
                ],
                "examples": [],
                "explanation": "Phrasal verb'ler fiil + preposition/adverb kombinasyonudur. Anlamları genellikle ana fiilin anlamından farklıdır. İngilizce'de çok yaygın kullanılır ve doğal konuşma için önemlidir.",
                "detailed_info": "Phrasal Verbs - İki/Üç Kelimeli Fiiller"
            }
        }
        
        # Collocations
        collocation_patterns = {
            "Common Collocations": {
                "indicators": [
                    r'\bmake\s+a\s+decision\b', r'\btake\s+a\s+break\b', r'\bhave\s+a\s+good\s+time\b',
                    r'\bdo\s+\w+\s+best\b', r'\bpay\s+attention\b', r'\btell\s+the\s+truth\b',
                    r'\bmake\s+an\s+effort\b', r'\btake\s+care\b', r'\bkeep\s+in\s+touch\b',
                    r'\bfast\s+food\b', r'\bheavy\s+rain\b', r'\bstrong\s+coffee\b',
                    r'\bmake\s+a\s+mistake\b', r'\btake\s+\w+\s+chance\b', r'\bdo\s+homework\b',
                    r'\bhave\s+\w+\s+idea\b', r'\bgive\s+\w+\s+hand\b', r'\bmake\s+\w+\s+choice\b',
                    r'\btake\s+\w+\s+shower\b', r'\bhave\s+\w+\s+look\b', r'\bmake\s+\w+\s+appointment\b'
                ],
                "examples": [],
                "explanation": "Collocation'lar birlikte kullanılan kelime çiftleridir. Doğal İngilizce için bu kombinasyonları öğrenmek önemlidir. 'Make a decision' derken 'do a decision' demeyiz.",
                "detailed_info": "Common Collocations - Kelime Birleşimleri"
            }
        }
        
        # Fixed expressions
        fixed_expression_patterns = {
            "Fixed Expressions": {
                "indicators": [
                    r'\bas\s+a\s+matter\s+of\s+fact\b', r'\bin\s+other\s+words\b', r'\bto\s+be\s+honest\b',
                    r'\bby\s+the\s+way\b', r'\bon\s+the\s+other\s+hand\b', r'\bat\s+the\s+end\s+of\s+the\s+day\b',
                    r'\bin\s+my\s+opinion\b', r'\bas\s+far\s+as\s+I\s+know\b', r'\bto\s+tell\s+you\s+the\s+truth\b'
                ],
                "examples": [],
                "explanation": "Sabit ifadeler değiştirilemeyen kelime dizileridir. Konuşmaya akıcılık katar ve düşünceleri bağlamak için kullanılır. Bu ifadeler ezberle öğrenilmelidir.",
                "detailed_info": "Fixed Expressions - Sabit İfadeler"
            }
        }
        
        # Bütün pattern'ları birleştir
        all_patterns = {**tense_patterns, **modal_patterns, **conditional_patterns, 
                       **passive_patterns, **relative_patterns, **comparison_patterns,
                       **idiom_patterns, **phrasal_verb_patterns, **collocation_patterns,
                       **fixed_expression_patterns}
        
        # Her pattern için metni kontrol et
        for pattern_name, pattern_info in all_patterns.items():
            found_examples = []
            
            for sentence in sentences[:10]:  # İlk 10 cümleyi kontrol et
                for indicator_pattern in pattern_info["indicators"]:
                    if re.search(indicator_pattern, sentence, re.IGNORECASE):
                        if sentence not in found_examples and len(found_examples) < 3:
                            found_examples.append(sentence.strip())
            
            if found_examples:
                # Örnekleri çevir
                translated_examples = []
                for example in found_examples:
                    translation = self._translate_sentence(example)
                    translated_examples.append({
                        "english": example,
                        "turkish": translation
                    })
                
                patterns.append({
                    "pattern_name": pattern_name,
                    "explanation": pattern_info["explanation"],
                    "detailed_info": pattern_info.get("detailed_info", pattern_name),
                    "examples": found_examples,
                    "translated_examples": translated_examples,
                    "count": len(found_examples)
                })
        
        return patterns

    def _analyze_complexity(self, text: str, sentences: List[str]) -> Dict[str, Any]:
        """
        Metnin karmaşıklık göstergelerini analiz eder
        """
        # Bağlaçlar
        conjunctions = ['and', 'but', 'or', 'because', 'although', 'however', 'therefore', 
                       'moreover', 'furthermore', 'nevertheless', 'consequently']
        conjunction_count = sum(text.lower().count(conj) for conj in conjunctions)
        
        # Karmaşık cümleler (15+ kelime)
        complex_sentences = [s for s in sentences if len(s.split()) > 15]
        
        # Subordinating conjunctions (yan cümle bağlaçları)
        subordinating = ['because', 'although', 'while', 'since', 'unless', 'until', 'before', 'after']
        subordinating_count = sum(text.lower().count(sub) for sub in subordinating)
        
        return {
            "conjunction_count": conjunction_count,
            "complex_sentence_count": len(complex_sentences),
            "complex_sentence_examples": complex_sentences[:3],
            "subordinating_clause_count": subordinating_count,
            "average_sentence_complexity": "High" if len(complex_sentences) > len(sentences) * 0.3 else "Medium" if len(complex_sentences) > 0 else "Low"
        }

    def _analyze_words(self, text: str) -> Dict[str, Any]:
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

    def _get_ai_analysis(self, text: str) -> Dict[str, Any]:
        """
        Gemini API kullanarak AI destekli analiz
        """
        try:
            # GOOGLE_API_KEY kontrolü
            if not os.getenv("GOOGLE_API_KEY"):
                return {
                    "ai_analysis": "AI analizi için GOOGLE_API_KEY environment variable'ı gerekli. Lütfen .env dosyasında GOOGLE_API_KEY'inizi ayarlayın.",
                    "error": "Missing GOOGLE_API_KEY"
                }
            
            # Metni kısalt (token limiti için)
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            prompt = f"""Aşağıdaki İngilizce metni analiz et ve Türkçe olarak şu konularda kısa bilgi ver:

1. Dil seviyesi (A1-C2 arasında)
2. Kullanılan ana gramer yapıları
3. Kelime hazinesi seviyesi
4. Öğrenme önerileri

Metin: "{text}"

Maksimum 100 kelime ile yanıt ver."""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return {
                    "ai_analysis": response.text.strip(),
                    "analysis_date": "Gemini AI tarafından oluşturuldu"
                }
            else:
                return {
                    "ai_analysis": "AI analizi şu anda mevcut değil. Lütfen daha sonra tekrar deneyin.",
                    "error": "Empty response from Gemini"
                }
                
        except Exception as e:
            print(f"AI Analysis Error: {str(e)}")
            return {
                "ai_analysis": f"AI analizi sırasında hata oluştu. Hata: {str(e)[:100]}...",
                "error": str(e)
            }

    def get_grammar_examples(self, text: str, user_id: Optional[int] = None, db_session = None) -> Dict[str, Any]:
        """
        Metinden gramer örnekleri çıkarır - detaylı analiz
        Kullanıcının bildiği gramer kalıplarını filtreler
        """
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        examples = {
            "detected_patterns": [],
            "tense_examples": [],
            "modal_examples": [],
            "complex_structures": []
        }
        
        # Gramer pattern'larını tekrar analiz et
        grammar_patterns = self._detect_grammar_patterns(text, sentences)
        
        # Kullanıcının bildiği gramer kalıplarını filtrele
        if user_id and db_session:
            try:
                from app.services.grammar_service import GrammarService
                grammar_patterns = GrammarService.filter_known_patterns(db_session, user_id, grammar_patterns)
                print(f"🔍 Filtered grammar patterns for user {user_id}: {len(grammar_patterns)} patterns shown")
            except Exception as e:
                print(f"Grammar filtering error: {e}")
                # Hata durumunda tüm pattern'ları göster
        
        examples["detected_patterns"] = grammar_patterns
        
        # Zaman formları için özel örnekler
        tense_examples = []
        for sentence in sentences[:8]:
            sentence = sentence.strip()
            if len(sentence) > 10:
                # Present tense
                if re.search(r'\b(am|is|are)\s+\w+', sentence, re.IGNORECASE):
                    tense_examples.append(f"Present: {sentence}")
                # Past tense
                elif re.search(r'\b(was|were|had|did)\b', sentence, re.IGNORECASE):
                    tense_examples.append(f"Past: {sentence}")
                # Future tense
                elif re.search(r'\b(will|going to|shall)\b', sentence, re.IGNORECASE):
                    tense_examples.append(f"Future: {sentence}")
                # Present perfect
                elif re.search(r'\b(have|has)\s+\w+ed\b', sentence, re.IGNORECASE):
                    tense_examples.append(f"Present Perfect: {sentence}")
        
        examples["tense_examples"] = tense_examples[:5]
        
        # Modal örnekleri
        modal_examples = []
        for sentence in sentences[:8]:
            if re.search(r'\b(can|could|may|might|must|should|would)\s+\w+', sentence, re.IGNORECASE):
                modal_examples.append(sentence.strip())
        
        examples["modal_examples"] = modal_examples[:3]
        
        # Karmaşık yapılar
        complex_examples = []
        for sentence in sentences[:8]:
            # Relative clauses
            if re.search(r'\b(who|which|that|where|when)\s+\w+', sentence, re.IGNORECASE):
                complex_examples.append(f"Relative Clause: {sentence.strip()}")
            # Conditional
            elif re.search(r'\bif\s+.*,', sentence, re.IGNORECASE):
                complex_examples.append(f"Conditional: {sentence.strip()}")
            # Passive voice
            elif re.search(r'\b(was|were|is|are)\s+\w+ed\b', sentence, re.IGNORECASE):
                complex_examples.append(f"Passive Voice: {sentence.strip()}")
        
        examples["complex_structures"] = complex_examples[:4]
        
        return examples

    def _translate_sentence(self, sentence: str) -> str:
        """
        Gemini API kullanarak cümleyi Türkçeye çevirir
        """
        try:
            if len(sentence.strip()) < 5:
                return sentence
                
            prompt = f"""
            Aşağıdaki İngilizce cümleyi Türkçeye çevir. Sadece çeviriyi ver, başka açıklama yapma:
            
            "{sentence}"
            """
            
            response = self.model.generate_content(prompt)
            translation = response.text.strip()
            
            # Gereksiz tırnak işaretlerini temizle
            translation = translation.strip('"').strip("'")
            
            return translation
            
        except Exception as e:
            # Hata durumunda basit çeviri sözlüğü kullan
            basic_translations = {
                "the": "the",
                "weather": "hava",
                "is": "dir/dır",
                "beautiful": "güzel",
                "today": "bugün",
                "will": "gelecek",
                "going": "gidiyor",
                "have": "sahip olmak",
                "had": "sahipti",
                "was": "idi",
                "were": "idiler"
            }
            
            words = sentence.lower().split()
            translated_words = []
            for word in words:
                clean_word = re.sub(r'[^\w]', '', word)
                if clean_word in basic_translations:
                    translated_words.append(basic_translations[clean_word])
                else:
                    translated_words.append(word)
            
            return f"[Çeviri: {' '.join(translated_words)}]"

    def translate_word(self, word: str) -> Dict[str, str]:
        """
        Kelime veya ifade çevirisi için özel fonksiyon
        Tek kelime, çoklu kelime ve ifadeleri destekler
        """
        try:
            if len(word.strip()) < 1:
                return {"word": word, "translation": word, "error": "Kelime çok kısa"}
                
            # Metni temizle ama kelime aralarındaki boşlukları koru
            clean_text = word.strip()
            
            # Çoklu kelime mi kontrol et
            words = clean_text.split()
            is_multi_word = len(words) > 1
            
            # Tek kelime ise özel isim kontrolü yap
            if not is_multi_word:
                clean_word = re.sub(r'[^\w]', '', clean_text)
                if self._is_proper_noun_or_name(clean_word):
                    return {
                        "word": word,
                        "translation": f"{clean_word} (özel isim)",
                        "explanation": "Bu kelime kişi adı, yer adı veya özel isim olduğu için çevrilmez.",
                        "success": True,
                        "is_proper_noun": True
                    }
            
            # AI ile çeviri yap
            if is_multi_word:
                prompt = f"""
                Bu İngilizce ifadeyi veya kelime grubunu Türkçeye çevir ve kısa bir açıklama ekle:
                
                İfade: "{clean_text}"
                
                Format:
                Çeviri: [ifade anlamı]
                Açıklama: [kısa kullanım açıklaması veya context bilgisi]
                
                Sadece bu formatı kullan, başka bir şey yazma.
                """
            else:
                clean_word_lower = clean_text.lower()
                prompt = f"""
                Bu İngilizce kelimeyi Türkçeye çevir ve kısa bir açıklama ekle:
                
                Kelime: "{clean_word_lower}"
                
                Format:
                Çeviri: [kelime anlamı]
                Açıklama: [kısa kullanım açıklaması]
                
                Sadece bu formatı kullan, başka bir şey yazma.
                """
            
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            # Sonucu parse et
            lines = result.split('\n')
            translation = ""
            explanation = ""
            
            for line in lines:
                if "Çeviri:" in line:
                    translation = line.replace("Çeviri:", "").strip()
                elif "Açıklama:" in line:
                    explanation = line.replace("Açıklama:", "").strip()
            
            # Eğer parse edilemezse tüm sonucu translation olarak al
            if not translation:
                translation = result
                
            return {
                "word": word,
                "translation": translation,
                "explanation": explanation,
                "success": True
            }
            
        except Exception as e:
            # Basit çeviri sözlüğü kullan
            basic_translations = {
                "the": "belirli artikel",
                "a": "belirsiz artikel",
                "an": "belirsiz artikel",
                "and": "ve",
                "or": "veya",
                "but": "ama, fakat",
                "is": "olmak (tekil)",
                "are": "olmak (çoğul)",
                "was": "idi",
                "were": "idiler",
                "have": "sahip olmak",
                "has": "sahip olmak (tekil)",
                "had": "sahipti",
                "will": "gelecek zaman yardımcısı",
                "would": "şartlı gelecek",
                "can": "yapabilmek",
                "could": "yapabilirdi",
                "should": "yapmalı",
                "must": "yapmalı (zorunluluk)",
                "may": "olabilir",
                "might": "olabilir (düşük ihtimal)",
                "do": "yapmak",
                "does": "yapmak (tekil)",
                "did": "yaptı",
                "go": "gitmek",
                "come": "gelmek",
                "get": "almak, olmak",
                "make": "yapmak",
                "take": "almak",
                "see": "görmek",
                "know": "bilmek",
                "think": "düşünmek",
                "say": "söylemek",
                "tell": "anlatmak",
                "give": "vermek",
                "find": "bulmak",
                "look": "bakmak",
                "use": "kullanmak",
                "work": "çalışmak",
                "time": "zaman",
                "day": "gün",
                "year": "yıl",
                "way": "yol",
                "man": "adam",
                "woman": "kadın",
                "child": "çocuk",
                "people": "insanlar",
                "place": "yer",
                "world": "dünya",
                "life": "hayat",
                "hand": "el",
                "eye": "göz",
                "word": "kelime",
                "number": "sayı",
                "good": "iyi",
                "bad": "kötü",
                "big": "büyük",
                "small": "küçük",
                "long": "uzun",
                "short": "kısa",
                "new": "yeni",
                "old": "eski",
                "right": "doğru, sağ",
                "left": "sol",
                "first": "ilk",
                "last": "son",
                "next": "sonraki",
                "other": "diğer",
                "same": "aynı",
                "different": "farklı"
            }
            
            clean_word = re.sub(r'[^\w]', '', word.strip().lower())
            
            if clean_word in basic_translations:
                return {
                    "word": word,
                    "translation": basic_translations[clean_word],
                    "explanation": "Basit çeviri sözlüğünden",
                    "success": True
                }
            else:
                return {
                    "word": word,
                    "translation": f"[Çeviri bulunamadı: {word}]",
                    "explanation": "Bu kelime sözlükte bulunamadı",
                    "success": False,
                    "error": str(e)
                }

    def _get_ai_analysis_turkish(self, text: str) -> Dict[str, str]:
        """
        AI destekli analiz - Türkçe açıklamalar
        """
        try:
            prompt = f"""
            Aşağıdaki İngilizce metni analiz et ve TÜRKÇE açıklamalar ver:

            Metin: "{text[:500]}"

            Lütfen şunları analiz et ve TÜRKÇE olarak açıkla:
            1. Genel İngilizce seviyesi 
            2. Kullanılan gramer yapıları
            3. Kelime hazinesi zorluğu
            4. Öğrenme önerileri
            
            Yanıtını JSON formatında ver:
            {{
                "genel_seviye": "açıklama",
                "gramer_yapilari": "açıklama", 
                "kelime_zorlugu": "açıklama",
                "ogrenme_onerileri": "açıklama"
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # JSON parse etmeye çalış
            try:
                import json
                # Response'tan JSON kısmını çıkar
                response_text = response.text.strip()
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text
                
                parsed_response = json.loads(json_text)
                return {
                    "ai_analysis": parsed_response.get("genel_seviye", "Analiz tamamlandı"),
                    "grammar_insights": parsed_response.get("gramer_yapilari", "Gramer analizi yapıldı"),
                    "vocabulary_insights": parsed_response.get("kelime_zorlugu", "Kelime analizi yapıldı"),
                    "learning_suggestions": parsed_response.get("ogrenme_onerileri", "Öğrenme önerileri hazırlandı")
                }
            except:
                # JSON parse edemezse basit response döner
                return {
                    "ai_analysis": response.text[:200] if response.text else "AI analizi başarısız"
                }
                
        except Exception as e:
            return {
                "ai_analysis": f"AI analizi sırasında hata: {str(e)}"
            }

    def _generate_i_plus_1_adaptation(self, text: str, user_known_words: List[str] = None) -> Dict[str, str]:
        """
        i+1 seviyesinde metin adaptasyonu - kullanıcının bilinen kelimeleri ile
        """
        try:
            # Kullanıcının bilinen kelimelerini prompt'a ekle
            known_words_context = ""
            if user_known_words and len(user_known_words) > 0:
                # İlk 50 kelimeyi örnek olarak al
                sample_known_words = user_known_words[:50]
                known_words_context = f"\n\nThe user already knows these words (keep them as they are): {', '.join(sample_known_words)}"
            
            prompt = f"""
            Please adapt this English text to i+1 level (slightly easier but educational):

            Original Text: "{text[:800]}"
            {known_words_context}

            Please:
            1. Replace complex words with simpler synonyms (but keep the words user already knows)
            2. Break long sentences into shorter, clearer ones
            3. Keep basic grammar structures but simplify them
            4. Maintain meaning and flow
            5. If user knows certain words, don't replace them with simpler alternatives
            
            Return ONLY the adapted English text, no explanations in Turkish or any other language.
            The adapted text must be in English.
            """
            
            response = self.model.generate_content(prompt)
            
            # Adaptasyon istatistikleri
            changes_made = "Kelimeler basitleştirildi, cümleler kısaltıldı, gramer yapıları sadeleştirildi"
            if user_known_words:
                changes_made += f". Kullanıcının bildiği {len(user_known_words)} kelime korundu"
            
            return {
                "adapted_text": response.text.strip(),
                "adaptation_level": "i+1 (Beginner-Intermediate)",
                "changes_made": changes_made,
                "user_known_words_count": len(user_known_words) if user_known_words else 0
            }
            
        except Exception as e:
            return {
                "adapted_text": text,
                "adaptation_level": "Original (Adaptation failed)",
                "changes_made": f"Adaptasyon hatası: {str(e)}",
                "user_known_words_count": len(user_known_words) if user_known_words else 0
            }

    def generate_pdf_report(self, analysis_result: Dict[str, Any], include_adaptation: bool = False) -> bytes:
        """
        Analiz sonuçlarından PDF raporu oluşturur
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfutils
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfbase import pdfmetrics
            import io
            from datetime import datetime

            # PDF buffer oluştur
            buffer = io.BytesIO()
            
            # Türkçe karakterler için DejaVu Sans font'unu yükle
            try:
                # DejaVu Sans font'unu sistem fontlarından bulmaya çalış
                import os
                import platform
                
                font_paths = []
                if platform.system() == "Windows":
                    font_paths = [
                        "C:/Windows/Fonts/DejaVuSans.ttf",
                        "C:/Windows/Fonts/arial.ttf",
                        "C:/Windows/Fonts/calibri.ttf"
                    ]
                elif platform.system() == "Linux":
                    font_paths = [
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "/usr/share/fonts/TTF/DejaVuSans.ttf"
                    ]
                else:  # macOS
                    font_paths = [
                        "/System/Library/Fonts/Arial.ttf",
                        "/Library/Fonts/Arial.ttf"
                    ]
                
                turkish_font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('TurkishFont', font_path))
                        turkish_font_registered = True
                        break
                
                if not turkish_font_registered:
                    # Fallback olarak Helvetica kullan
                    print("Warning: Turkish font not found, using Helvetica")
                    
            except Exception as font_error:
                print(f"Font loading error: {font_error}")
            
            # Document oluştur
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            
            # Styles - Türkçe karakterler için font ayarı
            styles = getSampleStyleSheet()
            
            # Türkçe font kullan (varsa)
            font_name = 'TurkishFont' if turkish_font_registered else 'Helvetica'
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.darkblue,
                fontName=font_name
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.darkgreen,
                fontName=font_name
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                fontName=font_name
            )
            
            italic_style = ParagraphStyle(
                'CustomItalic',
                parent=styles['Italic'],
                fontSize=9,
                fontName=font_name
            )
            
            # Content listesi
            content = []
            
            # Başlık
            content.append(Paragraph("📊 İngilizce Metin Analiz Raporu", title_style))
            content.append(Spacer(1, 12))
            content.append(Paragraph(f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
            content.append(Spacer(1, 20))
            
            # Orijinal Metin
            if analysis_result.get("original_text"):
                content.append(Paragraph("📝 Orijinal Metin", heading_style))
                # Uzun metinleri güvenli şekilde encode et
                original_text = analysis_result["original_text"]
                if len(original_text) > 500:
                    original_text = original_text[:500] + "..."
                # HTML karakterlerini escape et
                original_text = original_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                content.append(Paragraph(original_text, normal_style))
                content.append(Spacer(1, 15))
            
            # i+1 Adapted Text (varsa)
            if include_adaptation and analysis_result.get("adapted_text"):
                content.append(Paragraph("🔄 i+1 Seviyesinde Adapte Edilmiş Metin", heading_style))
                adapted_data = analysis_result["adapted_text"]
                if isinstance(adapted_data, dict):
                    adapted_text = adapted_data.get("adapted_text", "")
                    # HTML karakterlerini escape et
                    adapted_text = adapted_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    content.append(Paragraph(adapted_text, normal_style))
                    content.append(Spacer(1, 10))
                    content.append(Paragraph(f"Seviye: {adapted_data.get('adaptation_level', '')}", italic_style))
                    content.append(Paragraph(f"Değişiklikler: {adapted_data.get('changes_made', '')}", italic_style))
                content.append(Spacer(1, 15))
            
            # Temel İstatistikler
            basic_stats = analysis_result.get("basic_statistics", {})
            content.append(Paragraph("📈 Temel İstatistikler", heading_style))
            stats_data = [
                ['Kelime Sayısı', str(basic_stats.get('word_count', 'N/A'))],
                ['Cümle Sayısı', str(basic_stats.get('sentence_count', 'N/A'))],
                ['Paragraf Sayısı', str(basic_stats.get('paragraph_count', 'N/A'))],
                ['Ortalama Kelime Uzunluğu', f"{basic_stats.get('average_word_length', 0):.1f}"],
                ['Okuma Süresi (dakika)', str(basic_stats.get('reading_time_minutes', 'N/A'))]
            ]
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            content.append(stats_table)
            content.append(Spacer(1, 20))
            
            # Gramer Analizi
            grammar_analysis = analysis_result.get("grammar_analysis", {})
            if grammar_analysis.get("grammar_patterns"):
                content.append(Paragraph("🔍 Gramer Analizi", heading_style))
                
                for pattern in grammar_analysis["grammar_patterns"][:5]:  # İlk 5 pattern
                    pattern_name = pattern.get('pattern_name', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    content.append(Paragraph(f"• {pattern_name}", normal_style))
                    if pattern.get('explanation'):
                        explanation = pattern['explanation'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        content.append(Paragraph(f"  Açıklama: {explanation}", italic_style))
                    if pattern.get('examples'):
                        examples_text = "; ".join(pattern['examples'][:2])  # İlk 2 örnek
                        examples_text = examples_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        content.append(Paragraph(f"  Örnekler: {examples_text}", normal_style))
                    content.append(Spacer(1, 8))
            
            # AI Yorumları (Türkçe)
            ai_insights = analysis_result.get("ai_insights", {})
            if ai_insights:
                content.append(Paragraph("🤖 AI Analiz Sonuçları", heading_style))
                if ai_insights.get("grammar_insights"):
                    grammar_text = ai_insights['grammar_insights'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    content.append(Paragraph(f"Gramer Yapıları: {grammar_text}", normal_style))
                    content.append(Spacer(1, 8))
                if ai_insights.get("vocabulary_insights"):
                    vocab_text = ai_insights['vocabulary_insights'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    content.append(Paragraph(f"Kelime Zorluğu: {vocab_text}", normal_style))
                    content.append(Spacer(1, 8))
                if ai_insights.get("learning_suggestions"):
                    learning_text = ai_insights['learning_suggestions'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    content.append(Paragraph(f"Öğrenme Önerileri: {learning_text}", normal_style))
            
            # PDF'i oluştur
            doc.build(content)
            
            # Buffer'ı başa al ve bytes döndür
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            # Hata durumunda basit bir PDF oluştur
            buffer = io.BytesIO()
            buffer.write(f"PDF oluşturma hatası: {str(e)}".encode())
            return buffer.getvalue()

    def generate_simple_text_pdf(self, text_content: str, text_type: str) -> bytes:
        """
        Sadece metin içeren basit PDF oluşturur
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfbase import pdfmetrics
            import io
            from datetime import datetime
            import os
            import platform

            # PDF buffer oluştur
            buffer = io.BytesIO()
            
            # Türkçe font yükleme
            try:
                font_paths = []
                if platform.system() == "Windows":
                    font_paths = [
                        "C:/Windows/Fonts/DejaVuSans.ttf",
                        "C:/Windows/Fonts/arial.ttf",
                        "C:/Windows/Fonts/calibri.ttf"
                    ]
                elif platform.system() == "Linux":
                    font_paths = [
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "/usr/share/fonts/TTF/DejaVuSans.ttf"
                    ]
                else:  # macOS
                    font_paths = [
                        "/System/Library/Fonts/Arial.ttf",
                        "/Library/Fonts/Arial.ttf"
                    ]
                
                turkish_font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('TurkishFont', font_path))
                        turkish_font_registered = True
                        break
                        
            except Exception as font_error:
                turkish_font_registered = False
                print(f"Font loading error: {font_error}")
            
            # Document oluştur
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            
            # Font seçimi
            font_name = 'TurkishFont' if turkish_font_registered else 'Helvetica'
            
            # Style'lar
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=20,
                textColor=colors.darkblue,
                fontName=font_name,
                alignment=1  # Center
            )
            
            content_style = ParagraphStyle(
                'Content',
                parent=styles['Normal'],
                fontSize=11,
                spaceBefore=12,
                fontName=font_name,
                leading=16
            )
            
            info_style = ParagraphStyle(
                'Info',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                fontName=font_name
            )
            
            # Content
            content = []
            
            # Başlık
            if text_type == "original":
                title = "📝 Orijinal Metin"
            elif text_type == "adapted":
                title = "🔄 i+1 Adapte Edilmiş Metin"
            else:
                title = "📄 Metin"
                
            content.append(Paragraph(title, title_style))
            content.append(Spacer(1, 20))
            
            # Tarih
            content.append(Paragraph(f"İndirilme Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", info_style))
            content.append(Spacer(1, 20))
            
            # Metin içeriği - paragraflar halinde böl
            paragraphs = text_content.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    # HTML karakterlerini escape et
                    safe_paragraph = paragraph.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    content.append(Paragraph(safe_paragraph, content_style))
                    content.append(Spacer(1, 12))
            
            # İstatistikler
            word_count = len(text_content.split())
            char_count = len(text_content)
            sentence_count = len([s for s in text_content.split('.') if s.strip()])
            
            content.append(Spacer(1, 30))
            content.append(Paragraph("📊 Metin İstatistikleri", ParagraphStyle(
                'StatTitle',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.darkgreen,
                fontName=font_name
            )))
            content.append(Spacer(1, 10))
            content.append(Paragraph(f"Kelime Sayısı: {word_count}", info_style))
            content.append(Paragraph(f"Karakter Sayısı: {char_count}", info_style))
            content.append(Paragraph(f"Cümle Sayısı: {sentence_count}", info_style))
            
            # PDF'i oluştur
            doc.build(content)
            
            # Buffer'ı başa al ve bytes döndür
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            # Hata durumunda basit PDF
            buffer = io.BytesIO()
            buffer.write(f"Metin PDF oluşturma hatası: {str(e)}".encode())
            return buffer.getvalue()
