import re
from typing import List, Dict, Tuple, Set
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user_vocabulary import User, UserVocabulary, Vocabulary
import logging

logger = logging.getLogger(__name__)

class TextAdaptationService:
    """
    Krashen's i+1 Hypothesis Implementation
    
    Adapts text to maintain 90% known words + 10% unknown words
    for optimal language learning experience.
    """
    
    @staticmethod
    def clean_and_tokenize(text: str) -> List[str]:
        """
        Clean text and extract words, removing punctuation and converting to lowercase.
        Also handles contractions like "doesn't", "you're", etc.
        """
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Extract words (letters + apostrophes for contractions)
        words = re.findall(r'\b[a-zA-Z]+(?:\'[a-zA-Z]+)?\b', text.lower())
        
        return words
    
    @staticmethod
    def clean_word_for_comparison(word: str) -> str:
        """
        Clean word for comparison, preserving apostrophes and hyphens.
        """
        return word.lower().strip()
    
    @staticmethod
    def get_user_known_words(username: str, db: Session) -> Set[str]:
        """
        Get all words that user knows (status='known') from database.
        """
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return set()
            
            # Sadece 'known' status'lu kelimeleri al
            user_vocab = db.query(UserVocabulary).filter(
                UserVocabulary.user_id == user.id,
                UserVocabulary.status == "known"  # Sadece bilinen kelimeler
            ).all()
            
            known_words = set()
            for uv in user_vocab:
                vocab_word = db.query(Vocabulary).filter(
                    Vocabulary.id == uv.vocabulary_id
                ).first()
                if vocab_word:
                    known_words.add(vocab_word.word.lower())
            
            return known_words
            
        except Exception as e:
            logger.error(f"Error getting user vocabulary: {e}")
            return set()

    @staticmethod
    def get_user_ignored_words(username: str, db: Session) -> Set[str]:
        """
        Get all words that user has ignored from database.
        These words should not be colored (treated as neutral).
        """
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return set()
            
            # Get only ignored words
            user_vocab = db.query(UserVocabulary).filter(
                UserVocabulary.user_id == user.id,
                UserVocabulary.status == "ignored"
            ).all()
            
            ignored_words = set()
            for uv in user_vocab:
                vocab_word = db.query(Vocabulary).filter(
                    Vocabulary.id == uv.vocabulary_id
                ).first()
                if vocab_word:
                    ignored_words.add(vocab_word.word.lower())
            
            return ignored_words
            
        except Exception as e:
            logger.error(f"Error getting user ignored vocabulary: {e}")
            return set()
    
    @staticmethod
    def get_user_unknown_words(username: str, db: Session) -> Set[str]:
        """
        Get all words that user has marked as unknown from database.
        These words should be colored (treated as unknown).
        """
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return set()
            
            # Get only unknown words
            user_vocab = db.query(UserVocabulary).filter(
                UserVocabulary.user_id == user.id,
                UserVocabulary.status == "unknown"
            ).all()
            
            unknown_words = set()
            for uv in user_vocab:
                vocab_word = db.query(Vocabulary).filter(
                    Vocabulary.id == uv.vocabulary_id
                ).first()
                if vocab_word:
                    unknown_words.add(vocab_word.word.lower())
            
            return unknown_words
            
        except Exception as e:
            logger.error(f"Error getting user unknown vocabulary: {e}")
            return set()
    
    @staticmethod
    def analyze_text_difficulty(text: str, known_words: Set[str]) -> Dict:
        """
        Analyze text to determine word difficulty distribution.
        """
        words = TextAdaptationService.clean_and_tokenize(text)
        total_words = len(words)
        
        if total_words == 0:
            return {
                "total_words": 0,
                "known_words": 0,
                "unknown_words": 0,
                "known_percentage": 0.0,
                "unknown_percentage": 0.0,
                "difficulty_level": "N/A"
            }
        
        # Count known vs unknown with flexible matching
        def is_word_known(word: str, known_words: Set[str]) -> bool:
            # Direct match
            if word in known_words:
                return True
            
            # Check for "to" prefix variations
            if word.startswith('to '):
                base_word = word[3:]  # Remove "to "
                if base_word in known_words:
                    return True
            
            # Check if word matches any known word that starts with "to "
            for known_word in known_words:
                if known_word.startswith('to ') and known_word[3:] == word:
                    return True
            
            return False
        
        known_count = sum(1 for word in words if is_word_known(word, known_words))
        unknown_count = total_words - known_count
        
        known_percentage = (known_count / total_words) * 100
        unknown_percentage = (unknown_count / total_words) * 100
        
        # Determine difficulty level based on Krashen's theory
        if unknown_percentage <= 5:
            difficulty_level = "Too Easy (i-1)"
        elif unknown_percentage <= 15:
            difficulty_level = "Perfect (i+1)"
        elif unknown_percentage <= 25:
            difficulty_level = "Challenging (i+2)"
        else:
            difficulty_level = "Too Difficult (i+3+)"
        
        return {
            "total_words": total_words,
            "known_words": known_count,
            "unknown_words": unknown_count,
            "known_percentage": round(known_percentage, 1),
            "unknown_percentage": round(unknown_percentage, 1),
            "difficulty_level": difficulty_level,
            "unique_words": len(set(words)),
            "unique_unknown": len(set(word for word in words if word not in known_words))
        }

    @staticmethod
    def get_word_analysis_for_coloring(text: str, known_words: Set[str], username: str = None, db: Session = None) -> Dict:
        """
        Get detailed word-by-word analysis for frontend coloring.
        Returns which words are known/unknown for accurate coloring.
        """
        words = TextAdaptationService.clean_and_tokenize(text)
        
        # Get ignored words (words user has decided to ignore)
        ignored_words = set()
        # Get unknown words (words user has marked as unknown)
        unknown_words = set()
        if username and db:
            ignored_words = TextAdaptationService.get_user_ignored_words(username, db)
            unknown_words = TextAdaptationService.get_user_unknown_words(username, db)
        
        def is_word_known(word: str, known_words: Set[str]) -> bool:
            # Clean word for comparison
            clean_word = TextAdaptationService.clean_word_for_comparison(word)
            
            # Direct match
            if clean_word in known_words:
                return True
            
            # Check for "to" prefix variations
            if clean_word.startswith('to '):
                base_word = clean_word[3:]  # Remove "to "
                if base_word in known_words:
                    return True
            
            # Check if word matches any known word that starts with "to "
            for known_word in known_words:
                if known_word.startswith('to ') and known_word[3:] == clean_word:
                    return True
            
            # ✅ YENİ: Kelime sonları kontrolü (ed, ing, es, ies)
            # Eğer kelime bu sonlarla bitiyorsa kök kelimeyi kontrol et
            word_endings = ['ing', 'ed', 'ies', 'es']
            for ending in word_endings:
                if clean_word.endswith(ending) and len(clean_word) > len(ending):
                    # Kök kelimeyi bul
                    root_word = clean_word[:-len(ending)]
                    
                    # Özel durumlar
                    if ending == 'ies':
                        # flies -> fly, tries -> try
                        root_word = root_word + 'y'
                    elif ending == 'es':
                        # Sadece -es için değil, consonant+es durumları için kontrol
                        # goes -> go, does -> do, watches -> watch gibi
                        if len(root_word) > 0:
                            # Eğer kök kelime biliniyor ise
                            if root_word in known_words:
                                return True
                            # "to + kök kelime" formatını da kontrol et
                            if ('to ' + root_word) in known_words:
                                return True
                            # 'e' ekleyerek de dene (watches -> watch)
                            if (root_word + 'e') in known_words:
                                return True
                            # "to + kök kelime + e" formatını da kontrol et
                            if ('to ' + root_word + 'e') in known_words:
                                return True
                    elif ending == 'ed':
                        # Eğer kök kelime biliniyor ise (worked -> work)
                        if root_word in known_words:
                            return True
                        # "to + kök kelime" formatını da kontrol et
                        if ('to ' + root_word) in known_words:
                            return True
                        # 'e' ekleyerek de dene (used -> use)
                        if (root_word + 'e') in known_words:
                            return True
                        # "to + kök kelime + e" formatını da kontrol et
                        if ('to ' + root_word + 'e') in known_words:
                            return True
                    elif ending == 'ing':
                        # Eğer kök kelime biliniyor ise (working -> work)
                        if root_word in known_words:
                            return True
                        # "to + kök kelime" formatını da kontrol et
                        if ('to ' + root_word) in known_words:
                            return True
                        # 'e' ekleyerek de dene (using -> use)
                        if (root_word + 'e') in known_words:
                            return True
                        # "to + kök kelime + e" formatını da kontrol et
                        if ('to ' + root_word + 'e') in known_words:
                            return True
                    
                    # Normal kök kelime kontrolü
                    if root_word in known_words:
                        return True
                    # "to + kök kelime" formatını da kontrol et
                    if ('to ' + root_word) in known_words:
                        return True
            
            return False
        
        def is_word_ignored(word: str, ignored_words: Set[str]) -> bool:
            # Clean word for comparison
            clean_word = TextAdaptationService.clean_word_for_comparison(word)
            
            # Direct match
            if clean_word in ignored_words:
                return True
            
            # Check for "to" prefix variations
            if clean_word.startswith('to '):
                base_word = clean_word[3:]  # Remove "to "
                if base_word in ignored_words:
                    return True
            
            # Check if word matches any ignored word that starts with "to "
            for ignored_word in ignored_words:
                if ignored_word.startswith('to ') and ignored_word[3:] == clean_word:
                    return True
            
            return False
        
        # Create word status mapping
        word_status = {}
        for word in words:
            clean_word = TextAdaptationService.clean_word_for_comparison(word)
            
            # If word is ignored, treat as known (no coloring)
            if ignored_words and is_word_ignored(word, ignored_words):
                word_status[clean_word] = True  # Treat as known to avoid coloring
            # If word is marked as unknown by user, treat as unknown (colored)
            elif unknown_words and clean_word in unknown_words:
                word_status[clean_word] = False  # Treat as unknown to show coloring
            else:
                # Check if word is known (either naturally or user marked as known)
                word_status[clean_word] = is_word_known(word, known_words)
        
        # Also check for multi-word phrases that user has marked
        # This handles cases like "not only" where user selected the phrase
        if username and db:
            # Get all user's vocabulary to check for phrases
            user = db.query(User).filter(User.username == username).first()
            if user:
                user_vocab = db.query(UserVocabulary).filter(
                    UserVocabulary.user_id == user.id
                ).all()
                
                for uv in user_vocab:
                    vocab_word = db.query(Vocabulary).filter(
                        Vocabulary.id == uv.vocabulary_id
                    ).first()
                    if vocab_word and ' ' in vocab_word.word:  # This is a phrase
                        phrase_words = vocab_word.word.lower().split()
                        # If all words in the phrase are in our word list, mark them according to status
                        if all(word in words for word in phrase_words):
                            for phrase_word in phrase_words:
                                clean_phrase_word = TextAdaptationService.clean_word_for_comparison(phrase_word)
                                if uv.status == "unknown":
                                    word_status[clean_phrase_word] = False  # Mark as unknown
                                elif uv.status == "ignore":
                                    word_status[clean_phrase_word] = True   # Mark as known (no coloring)
                                elif uv.status == "known":
                                    word_status[clean_phrase_word] = True   # Mark as known
        
        return {
            "word_status": word_status,
            "known_words_list": list(known_words),  # This is already only "known" words from get_user_known_words
            "total_known_words": len(known_words),
            "total_words": len(words),
            "unknown_words_count": sum(1 for status in word_status.values() if not status)
        }
    
    @staticmethod
    def get_word_frequency_in_text(text: str) -> Dict[str, int]:
        """
        Get frequency count of each word in text.
        """
        words = TextAdaptationService.clean_and_tokenize(text)
        frequency = {}
        for word in words:
            frequency[word] = frequency.get(word, 0) + 1
        return frequency
    
    # Removed simplify_text_for_user method - system now uses only AI-powered adaptation
    
    @staticmethod
    def identify_learning_words(text: str, username: str) -> List[Dict]:
        """
        Identify words that are perfect for learning (unknown but not too complex).
        """
        db = next(get_db())
        
        try:
            known_words = TextAdaptationService.get_user_known_words(username, db)
            words = TextAdaptationService.clean_and_tokenize(text)
            word_freq = TextAdaptationService.get_word_frequency_in_text(text)
            
            def is_word_known(word: str, known_words: Set[str]) -> bool:
                # Direct match
                if word in known_words:
                    return True
                
                # Check for "to" prefix variations
                if word.startswith('to '):
                    base_word = word[3:]  # Remove "to "
                    if base_word in known_words:
                        return True
                
                # Check if word matches any known word that starts with "to "
                for known_word in known_words:
                    if known_word.startswith('to ') and known_word[3:] == word:
                        return True
                
                return False
            
            # Find unknown words using the same logic as analyze_text_difficulty
            unknown_words = [word for word in set(words) if not is_word_known(word, known_words)]
            
            # Sort by frequency and length (prefer shorter, more frequent words for learning)
            learning_candidates = []
            for word in unknown_words:
                learning_candidates.append({
                    "word": word,
                    "frequency": word_freq[word],
                    "length": len(word),
                    "learning_priority": word_freq[word] * (10 - min(len(word), 10))  # Prefer frequent, shorter words
                })
            
            # Sort by learning priority
            learning_candidates.sort(key=lambda x: x["learning_priority"], reverse=True)
            
            return learning_candidates[:10]  # Return top 10 learning candidates
            
        except Exception as e:
            logger.error(f"Error identifying learning words: {e}")
            return []
        finally:
            db.close() 