from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.user_vocabulary import User, UserGrammarKnowledge, GrammarPattern
from app.core.database import get_db

class GrammarService:
    
    @staticmethod
    def initialize_grammar_patterns(db: Session):
        """
        Varsayılan gramer kalıplarını veritabanına ekler
        """
        default_patterns = [
            {
                "pattern_name": "Present Perfect Tense",
                "pattern_key": "present_perfect",
                "description_turkish": "Şimdiki zamanın tamamlanmış hali. 'have/has + past participle' yapısıyla kullanılır.",
                "description_english": "Present perfect tense using 'have/has + past participle'",
                "difficulty_level": 3,
                "category": "tenses"
            },
            {
                "pattern_name": "Passive Voice",
                "pattern_key": "passive_voice", 
                "description_turkish": "Pasif yapı. Eylemin yapanından çok eylem kendisinin önemli olduğu durumlarda kullanılır.",
                "description_english": "Passive voice construction using 'be + past participle'",
                "difficulty_level": 4,
                "category": "voice"
            },
            {
                "pattern_name": "Modal Verbs",
                "pattern_key": "modal_verbs",
                "description_turkish": "Yardımcı fiiller (can, could, may, might, must, should, will, would) olasılık, yetenek, zorunluluk ifade eder.",
                "description_english": "Modal verbs expressing ability, possibility, necessity",
                "difficulty_level": 2,
                "category": "modals"
            },
            {
                "pattern_name": "Conditional Sentences",
                "pattern_key": "conditional",
                "description_turkish": "Koşul cümleleri. 'If' ile başlayan ve bir koşula bağlı olan durumları ifade eder.",
                "description_english": "Conditional sentences using 'if' clauses",
                "difficulty_level": 5,
                "category": "conditionals"
            },
            {
                "pattern_name": "Relative Clauses",
                "pattern_key": "relative_clauses",
                "description_turkish": "Sıfat cümleleri. 'who, which, that, where, when' ile başlayan açıklayıcı cümleler.",
                "description_english": "Relative clauses using who, which, that, where, when",
                "difficulty_level": 4,
                "category": "clauses"
            },
            {
                "pattern_name": "Comparative and Superlative",
                "pattern_key": "comparative",
                "description_turkish": "Karşılaştırma yapıları. '-er than', 'more than', 'the most' gibi yapılar.",
                "description_english": "Comparative and superlative forms",
                "difficulty_level": 2,
                "category": "comparison"
            },
            {
                "pattern_name": "Future Tense",
                "pattern_key": "future_tense",
                "description_turkish": "Gelecek zaman. 'will', 'going to', 'present continuous for future' yapıları.",
                "description_english": "Future tense using will, going to, present continuous",
                "difficulty_level": 2,
                "category": "tenses"
            },
            {
                "pattern_name": "Past Perfect Tense",
                "pattern_key": "past_perfect",
                "description_turkish": "Geçmiş zamanın tamamlanmış hali. 'had + past participle' yapısı.",
                "description_english": "Past perfect tense using 'had + past participle'",
                "difficulty_level": 4,
                "category": "tenses"
            },
            # Kalıp İfadeler ve Deyimler
            {
                "pattern_name": "Common Idioms",
                "pattern_key": "common_idioms",
                "description_turkish": "Yaygın deyimler ve kalıp ifadeler. 'piece of cake', 'break the ice' gibi.",
                "description_english": "Common idioms and idiomatic expressions",
                "difficulty_level": 5,
                "category": "idioms"
            },
            {
                "pattern_name": "Phrasal Verbs",
                "pattern_key": "phrasal_verbs",
                "description_turkish": "İki/üç kelimeli fiiller. 'get up', 'turn on', 'run out of' gibi yapılar.",
                "description_english": "Phrasal verbs - verb + particle combinations",
                "difficulty_level": 4,
                "category": "phrasal_verbs"
            },
            {
                "pattern_name": "Common Collocations",
                "pattern_key": "collocations",
                "description_turkish": "Kelime birleşimleri. 'make a decision', 'take a break', 'heavy rain' gibi.",
                "description_english": "Common word combinations and collocations",
                "difficulty_level": 3,
                "category": "collocations"
            },
            {
                "pattern_name": "Fixed Expressions",
                "pattern_key": "fixed_expressions",
                "description_turkish": "Sabit ifadeler. 'by the way', 'on the other hand', 'to be honest' gibi.",
                "description_english": "Fixed expressions and linking phrases",
                "difficulty_level": 3,
                "category": "expressions"
            }
        ]
        
        for pattern_data in default_patterns:
            # Kontrol et, zaten varsa ekleme
            existing = db.query(GrammarPattern).filter(
                GrammarPattern.pattern_key == pattern_data["pattern_key"]
            ).first()
            
            if not existing:
                pattern = GrammarPattern(**pattern_data)
                db.add(pattern)
        
        db.commit()
        print(f"✅ {len(default_patterns)} grammar patterns initialized")

    @staticmethod
    def get_user_grammar_knowledge(db: Session, user_id: int) -> Dict[str, str]:
        """
        Kullanıcının bildiği/bilmediği gramer kalıplarını getirir
        """
        knowledge = db.query(UserGrammarKnowledge).filter(
            UserGrammarKnowledge.user_id == user_id
        ).all()
        
        return {kg.grammar_pattern: kg.status for kg in knowledge}

    @staticmethod
    def update_grammar_knowledge(db: Session, user_id: int, pattern_key: str, status: str) -> bool:
        """
        Kullanıcının gramer kalıbı bilgisini günceller
        status: 'known', 'unknown', 'ignored'
        """
        try:
            # Mevcut kaydı kontrol et
            existing = db.query(UserGrammarKnowledge).filter(
                UserGrammarKnowledge.user_id == user_id,
                UserGrammarKnowledge.grammar_pattern == pattern_key
            ).first()
            
            if existing:
                existing.status = status
            else:
                new_knowledge = UserGrammarKnowledge(
                    user_id=user_id,
                    grammar_pattern=pattern_key,
                    status=status
                )
                db.add(new_knowledge)
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"Error updating grammar knowledge: {e}")
            db.rollback()
            return False

    @staticmethod
    def filter_known_patterns(db: Session, user_id: int, detected_patterns: List[Dict]) -> List[Dict]:
        """
        Kullanıcının bildiği veya görmezden geldiği gramer kalıplarını filtreler
        """
        if not user_id:
            return detected_patterns  # User yoksa tümünü göster
            
        user_knowledge = GrammarService.get_user_grammar_knowledge(db, user_id)
        
        filtered_patterns = []
        for pattern in detected_patterns:
            pattern_key = GrammarService.get_pattern_key_from_name(pattern.get('pattern_name', ''))
            
            # Bilinen veya görmezden gelinen kalıpları filtrele
            if pattern_key not in user_knowledge or user_knowledge[pattern_key] == 'unknown':
                filtered_patterns.append(pattern)
        
        return filtered_patterns

    @staticmethod
    def get_pattern_key_from_name(pattern_name: str) -> str:
        """
        Pattern name'den pattern key'i çıkarır
        """
        pattern_mapping = {
            "Present Perfect Tense": "present_perfect",
            "Passive Voice": "passive_voice",
            "Modal Verbs": "modal_verbs", 
            "Conditional Sentences": "conditional",
            "Relative Clauses": "relative_clauses",
            "Comparative and Superlative": "comparative",
            "Future Tense": "future_tense",
            "Past Perfect Tense": "past_perfect",
            "Present Tense": "present_tense",
            "Past Tense": "past_tense",
            "Gerund and Infinitive": "gerund_infinitive"
        }
        
        return pattern_mapping.get(pattern_name, pattern_name.lower().replace(" ", "_"))

    @staticmethod
    def get_all_grammar_patterns(db: Session) -> List[Dict[str, Any]]:
        """
        Tüm gramer kalıplarını getirir
        """
        patterns = db.query(GrammarPattern).all()
        return [
            {
                "pattern_key": p.pattern_key,
                "pattern_name": p.pattern_name,
                "description_turkish": p.description_turkish,
                "description_english": p.description_english,
                "difficulty_level": p.difficulty_level,
                "category": p.category
            }
            for p in patterns
        ]

    @staticmethod
    def create_or_get_user_by_session(db: Session, session_id: str = "anonymous") -> int:
        """
        Session için geçici user oluşturur veya mevcut olanı getirir
        Gerçek auth sistemi yoksa kullanılır
        """
        # Basit implementation - gerçek sistemde JWT token'dan user_id alınır
        user = db.query(User).filter(User.username == f"session_{session_id}").first()
        
        if not user:
            user = User(
                username=f"session_{session_id}",
                email=f"session_{session_id}@temp.com",
                password_hash="temp_hash",
                phone_number="0000000000"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user.id
