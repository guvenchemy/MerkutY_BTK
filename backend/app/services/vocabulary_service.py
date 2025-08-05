import pandas as pd
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user_vocabulary import User, Vocabulary, UserVocabulary
import re

class VocabularyService:
    
    @staticmethod
    def read_excel_vocabulary(file_path: str) -> List[str]:
        """
        Read vocabulary from Excel file (single column of words)
        """
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Get the first column (assuming it contains the words)
            first_column = df.iloc[:, 0]
            
            # Clean and filter words
            words = []
            for word in first_column:
                if pd.notna(word):  # Skip empty cells
                    # Clean the word (remove extra spaces, convert to lowercase)
                    clean_word = str(word).strip().lower()
                    # Only include words with letters (filter out numbers, special chars)
                    if re.match(r'^[a-zA-Z\s-]+$', clean_word) and len(clean_word) > 1:
                        words.append(clean_word)
            
            # Remove duplicates while preserving order
            unique_words = list(dict.fromkeys(words))
            
            return unique_words
            
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")
    
    @staticmethod
    def create_or_get_user(db: Session, username: str, email: Optional[str] = None) -> User:
        """
        Create a new user or get existing user
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            # Create default email if none provided
            if not email:
                email = f"{username}@nexus.local"
            
            # Create user with default values
            user = User(
                username=username, 
                email=email,
                password_hash="default_hash_for_upload_users",  # Default password hash
                phone_number="0000000000"  # Default phone number
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def add_words_to_vocabulary(db: Session, words: List[str], language: str = "en") -> List[Vocabulary]:
        """
        Add words to global vocabulary if they don't exist
        """
        vocabulary_objects = []
        
        for word in words:
            # Check if word already exists
            existing_vocab = db.query(Vocabulary).filter(
                Vocabulary.word == word,
                Vocabulary.language == language
            ).first()
            
            if not existing_vocab:
                vocab = Vocabulary(
                    word=word,
                    language=language,
                    difficulty_level=VocabularyService._estimate_difficulty(word)
                )
                db.add(vocab)
                vocabulary_objects.append(vocab)
            else:
                vocabulary_objects.append(existing_vocab)
        
        db.commit()
        return vocabulary_objects
    
    @staticmethod
    def add_user_vocabulary_with_translation(
        db: Session, 
        user_id: int, 
        word: str, 
        translation: str, 
        status: str = "unknown"
    ) -> dict:
        """
        Kullanıcıya kelime ve çevirisini ekler
        status: 'known', 'unknown', 'ignored', 'learning'
        Returns: {"success": bool, "is_new": bool, "action": str}
        """
        try:
            print(f"🔍 VocabularyService: Adding word '{word}' for user {user_id} with status '{status}'")
            
            # Kelimeyi temizle
            clean_word = word.strip().lower()
            
            if not clean_word:
                print(f"❌ Clean word is empty")
                return {"success": False, "is_new": False, "action": "failed"}
            
            # Vocabulary tablosuna ekle (yoksa)
            vocab = db.query(Vocabulary).filter(
                Vocabulary.word == clean_word,
                Vocabulary.language == "en"
            ).first()
            
            vocab_created = False
            if not vocab:
                print(f"🔍 Creating new vocabulary entry for '{clean_word}'")
                vocab = Vocabulary(
                    word=clean_word,
                    language="en",
                    difficulty_level=VocabularyService._estimate_difficulty(clean_word)
                )
                db.add(vocab)
                db.flush()  # ID'yi al
                print(f"🔍 Created vocabulary with ID: {vocab.id}")
                vocab_created = True
            else:
                print(f"🔍 Found existing vocabulary with ID: {vocab.id}")
            
            # UserVocabulary tablosuna ekle/güncelle
            user_vocab = db.query(UserVocabulary).filter(
                UserVocabulary.user_id == user_id,
                UserVocabulary.vocabulary_id == vocab.id
            ).first()
            
            is_new_user_vocab = False
            action = ""
            
            if user_vocab:
                print(f"🔍 Updating existing user vocabulary")
                # Mevcut kayıt varsa güncelle
                old_status = user_vocab.status
                user_vocab.status = status
                user_vocab.translation = translation
                action = f"updated_from_{old_status}_to_{status}"
            else:
                print(f"🔍 Creating new user vocabulary")
                # Yeni kayıt oluştur
                user_vocab = UserVocabulary(
                    user_id=user_id,
                    vocabulary_id=vocab.id,
                    status=status,
                    translation=translation,
                    learned_at=None  # İlk öğrenme tarihi
                )
                db.add(user_vocab)
                is_new_user_vocab = True
                action = f"created_with_{status}"
                
                db.add(user_vocab)
            
            db.commit()
            print(f"✅ Successfully added vocabulary")
            return {
                "success": True, 
                "is_new": is_new_user_vocab, 
                "action": action,
                "vocab_created": vocab_created
            }
            
        except Exception as e:
            db.rollback()
            print(f"❌ Vocabulary add error: {str(e)}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return {"success": False, "is_new": False, "action": "failed"}
    
    @staticmethod
    def get_user_known_words(db: Session, user_id: int) -> List[str]:
        """
        Kullanıcının bilinen kelimelerini döner
        """
        try:
            # Known ve learning status'taki kelimeleri al
            user_vocabs = db.query(UserVocabulary).join(Vocabulary).filter(
                UserVocabulary.user_id == user_id,
                UserVocabulary.status.in_(['known', 'learning'])
            ).all()
            
            known_words = []
            for user_vocab in user_vocabs:
                if user_vocab.vocabulary:
                    known_words.append(user_vocab.vocabulary.word)
            
            return known_words
            
        except Exception as e:
            print(f"❌ Get known words error: {str(e)}")
            return []
    
    @staticmethod
    def assign_vocabulary_to_user(db: Session, user: User, vocabularies: List[Vocabulary]) -> int:
        """
        Assign vocabulary words to a user as 'known' words
        """
        added_count = 0
        
        for vocab in vocabularies:
            # Check if user already has this word
            existing_user_vocab = db.query(UserVocabulary).filter(
                UserVocabulary.user_id == user.id,
                UserVocabulary.vocabulary_id == vocab.id
            ).first()
            
            if not existing_user_vocab:
                user_vocab = UserVocabulary(
                    user_id=user.id,
                    vocabulary_id=vocab.id,
                    is_known=True,
                    confidence_level=4  # Default confidence for uploaded words
                )
                db.add(user_vocab)
                added_count += 1
        
        db.commit()
        return added_count
    
    @staticmethod
    def get_user_vocabulary_level(db: Session, user: User) -> dict:
        """
        Calculate user's vocabulary level (i level)
        """
        total_known_words = db.query(UserVocabulary).filter(
            UserVocabulary.user_id == user.id,
            UserVocabulary.is_known == True
        ).count()
        
        # Simple level calculation (can be made more sophisticated)
        if total_known_words < 500:
            level = "Beginner"
            level_score = 1
        elif total_known_words < 1500:
            level = "Elementary"
            level_score = 2
        elif total_known_words < 3000:
            level = "Intermediate"
            level_score = 3
        elif total_known_words < 5000:
            level = "Upper-Intermediate"
            level_score = 4
        else:
            level = "Advanced"
            level_score = 5
        
        return {
            "level": level,
            "level_score": level_score,
            "total_known_words": total_known_words,
            "estimated_vocabulary_size": total_known_words
        }
    
    @staticmethod
    def _estimate_difficulty(word: str) -> int:
        """
        Simple difficulty estimation based on word length and common patterns
        """
        word_length = len(word)
        
        if word_length <= 3:
            return 1
        elif word_length <= 5:
            return 2
        elif word_length <= 7:
            return 3
        elif word_length <= 10:
            return 4
        else:
            return 5 