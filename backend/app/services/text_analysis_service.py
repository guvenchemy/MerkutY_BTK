import re
from typing import Dict, List, Any
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
        self.model = genai.GenerativeModel('gemini-pro')
        
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

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Verilen metni kapsamlı bir şekilde analiz eder
        """
        try:
            # Temel istatistikler
            basic_stats = self._get_basic_statistics(text)
            
            # Gramer analizi
            grammar_analysis = self._analyze_grammar(text)
            
            # Kelime analizi
            word_analysis = self._analyze_words(text)
            
            # AI destekli analiz
            ai_analysis = self._get_ai_analysis(text)
            
            return {
                "basic_statistics": basic_stats,
                "grammar_analysis": grammar_analysis,
                "word_analysis": word_analysis,
                "ai_insights": ai_analysis,
                "text_sample": text[:200] + "..." if len(text) > 200 else text
            }
        except Exception as e:
            return {"error": f"Text analysis failed: {str(e)}"}

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
        
        # Bütün pattern'ları birleştir
        all_patterns = {**tense_patterns, **modal_patterns, **conditional_patterns, 
                       **passive_patterns, **relative_patterns, **comparison_patterns}
        
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

    def get_grammar_examples(self, text: str) -> Dict[str, Any]:
        """
        Metinden gramer örnekleri çıkarır - detaylı analiz
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
