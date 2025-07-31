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