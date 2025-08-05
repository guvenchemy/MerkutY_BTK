import os
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
import google.generativeai as genai
from app.models.word_cache import WordDefinition

logger = logging.getLogger(__name__)


class WordCacheService:
    """
    Service for caching word definitions globally
    Avoids duplicate AI API calls for the same words
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    async def get_word_explanation(self, word: str, db: Session) -> Dict:
        """
        Get word explanation from cache or generate with AI
        
        Args:
            word: English word to explain
            db: Database session
            
        Returns:
            Dict with word explanation data
        """
        try:
            # 1. Check cache first
            word_lower = word.lower().strip()
            cached_definition = db.query(WordDefinition).filter(
                WordDefinition.word == word_lower
            ).first()
            
            if cached_definition:
                logger.info(f"Cache hit for word: {word}")
                return {
                    "success": True,
                    "cached": True,
                    "data": cached_definition.to_dict()
                }
            
            # 2. Generate with AI if not in cache
            logger.info(f"Cache miss for word: {word}, generating with AI")
            ai_result = await self._generate_word_explanation(word)
            
            # 3. Save to cache
            word_definition = WordDefinition(
                word=word_lower,
                turkish_meaning=ai_result.get("turkish_meaning"),
                english_example=ai_result.get("english_example"),
                example_translation=ai_result.get("example_translation"),
                difficulty_level=ai_result.get("difficulty_level", 1)
            )
            
            db.add(word_definition)
            db.commit()
            db.refresh(word_definition)
            
            logger.info(f"Word cached successfully: {word}")
            return {
                "success": True,
                "cached": False,
                "data": word_definition.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error getting word explanation for '{word}': {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def _generate_word_explanation(self, word: str) -> Dict:
        """
        Generate word explanation using AI
        
        Args:
            word: English word to explain
            
        Returns:
            Dict with AI-generated explanation
        """
        try:
            prompt = f"""
You are an English teacher helping Turkish students learn English.

TASK: Explain the English word "{word}" for Turkish language learners.

PROVIDE:
1. Turkish meaning (clear, simple translation)
2. English example sentence (natural, common usage)
3. Turkish translation of the example sentence
4. Difficulty level (1-10 scale, where 1=basic, 10=advanced)

OUTPUT FORMAT (JSON):
{{
    "turkish_meaning": "clear Turkish translation",
    "english_example": "natural English sentence using the word",
    "example_translation": "Turkish translation of the example",
    "difficulty_level": 3
}}

RULES:
- Keep explanations simple and clear
- Use common, practical examples
- Ensure translations are accurate and natural
- Consider the word's most common usage
"""
            
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                raise Exception("Empty response from AI")
            
            # Parse AI response - handle JSON code blocks
            import json
            response_text = response.text.strip()
            
            # Remove markdown code block wrapper if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove ```
            
            response_text = response_text.strip()
            result = json.loads(response_text)
            
            return {
                "turkish_meaning": result.get("turkish_meaning", "Tanım bulunamadı"),
                "english_example": result.get("english_example", f"Example with {word}"),
                "example_translation": result.get("example_translation", "Çeviri bulunamadı"),
                "difficulty_level": result.get("difficulty_level", 1)
            }
            
        except json.JSONDecodeError:
            # Fallback if AI doesn't return valid JSON
            return self._fallback_explanation(word, response.text if response else "")
            
        except Exception as e:
            logger.error(f"Error generating AI explanation for '{word}': {str(e)}")
            return self._fallback_explanation(word, "")
    
    def _fallback_explanation(self, word: str, ai_text: str) -> Dict:
        """
        Fallback explanation when AI fails or returns invalid format
        """
        return {
            "turkish_meaning": f"'{word}' kelimesinin anlamı",
            "english_example": f"I use the word '{word}' in this sentence.",
            "example_translation": f"Bu cümlede '{word}' kelimesini kullanıyorum.",
            "difficulty_level": 1
        }
    
    def get_cache_stats(self, db: Session) -> Dict:
        """
        Get cache statistics
        """
        try:
            total_words = db.query(WordDefinition).count()
            return {
                "total_cached_words": total_words,
                "cache_enabled": True
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                "total_cached_words": 0,
                "cache_enabled": False,
                "error": str(e)
            } 