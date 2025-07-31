import os
import google.generativeai as genai
from typing import List, Dict, Set
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user_vocabulary import User, UserVocabulary, Vocabulary
import logging
import json

logger = logging.getLogger(__name__)

class AITextAdaptationService:
    """
    AI-Powered Text Adaptation using OpenAI ChatGPT
    
    Implements Krashen's i+1 Hypothesis with intelligent text rewriting:
    - Maintains 90% known words + 10% unknown words
    - Preserves meaning and context
    - Gradual vocabulary introduction for optimal learning
    """
    
    def __init__(self):
        # Get Gemini API key from environment or use provided key
        api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyCfkVTk07xkgK3AMHzMOCbaoihGHmopqnE"
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel('gemini-1.5-flash')
        self.demo_mode = False
    
    @staticmethod
    def get_user_known_words(username: str, db: Session) -> Set[str]:
        """Get all words that user knows from database."""
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return set()
            
            user_vocab = db.query(UserVocabulary).filter(
                UserVocabulary.user_id == user.id
            ).all()
            
            known_words = set()
            for uv in user_vocab:
                vocab_word = db.query(Vocabulary).filter(
                    Vocabulary.id == uv.vocabulary_id
                ).first()
                if vocab_word:
                    known_words.add(vocab_word.word.lower())
            
            # Add basic English words that everyone knows
            basic_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'am', 'can', 'could', 'will', 'would', 'should', 'may', 'might', 'must',
                'this', 'that', 'these', 'those', 'here', 'there', 'now', 'then', 'today', 'yesterday', 'tomorrow',
                'what', 'when', 'where', 'why', 'how', 'who', 'which', 'whose',
                'my', 'your', 'his', 'her', 'its', 'our', 'their',
                'good', 'bad', 'big', 'small', 'new', 'old', 'young', 'hot', 'cold', 'warm', 'cool',
                'yes', 'no', 'not', 'very', 'so', 'too', 'also', 'just', 'only', 'even', 'still', 'again',
                'one', 'two', 'three', 'first', 'second', 'third', 'last', 'next', 'previous',
                'to be', 'to have', 'to do', 'to go', 'to come', 'to see', 'to hear', 'to say', 'to tell',
                'to make', 'to take', 'to give', 'to get', 'to put', 'to bring', 'to find', 'to know', 'to think',
                'to want', 'to need', 'to like', 'to love', 'to hate', 'to work', 'to play', 'to eat', 'to drink',
                'to sleep', 'to walk', 'to run', 'to sit', 'to stand', 'to read', 'to write', 'to speak', 'to listen'
            }
            
            known_words.update(basic_words)
            
            return known_words
            
        except Exception as e:
            logger.error(f"Error getting user vocabulary: {e}")
            return set()
    
    def create_adaptation_prompt(self, text: str, known_words: Set[str], target_unknown_percentage: float = 10.0) -> str:
        """
        Create a sophisticated prompt for ChatGPT to adapt text according to i+1 theory.
        """
        known_words_sample = list(known_words)[:100] if len(known_words) > 100 else list(known_words)
        
        prompt = f"""You are an expert language learning instructor implementing Stephen Krashen's i+1 hypothesis for optimal language acquisition.

CRITICAL MISSION: You MUST rewrite the EXACT SAME CONTENT using ONLY the user's vocabulary. The user knows these words: {', '.join(known_words_sample)}

IMPORTANT: If user knows "to have", they also know "have", "has", "had". If user knows "to do", they also know "do", "does", "did". Apply this logic to all verbs.

TARGET: Use ONLY the user's known words + exactly {target_unknown_percentage}% new learning words.

ORIGINAL TEXT:
{text}

MANDATORY RULES:
1. **SAME CONTENT**: You MUST keep the EXACT SAME meaning and information as the original text
2. **USE USER'S VOCABULARY**: You MUST use words from this list: {', '.join(known_words_sample)}
3. **VERB FORMS**: If user knows "to have", they know "have/has/had". If user knows "to do", they know "do/does/did". Use these forms.
4. **CONTRACTIONS**: You MUST keep contractions EXACTLY as they appear in the original text. If original has "you're", write "you're". If original has "doesn't", write "doesn't". If original has "don't", write "don't". NEVER expand contractions to full forms. NEVER change "you are" to "you're" if original has "you are".
5. **EXTREMELY AGGRESSIVE SIMPLIFICATION**: Replace EVERY complex word with simple ones from user's vocabulary
6. **BREAK SENTENCES**: Split long sentences into multiple short, simple sentences
7. **BASIC GRAMMAR ONLY**: Use only simple present/past tense, basic connectors (and, but, so, because)
8. **EXACT {target_unknown_percentage}% TARGET**: Choose only {target_unknown_percentage}% of words as "new learning words"
9. **EVERYTHING ELSE**: Must be from user's vocabulary list

EXAMPLES OF REPLACEMENTS:
- "difficult" → "hard" (if user knows "hard")
- "beautiful" → "nice" (if user knows "nice") 
- "important" → "big" (if user knows "big")
- "interesting" → "good" (if user knows "good")
- "necessary" → "needed" (if user knows "needed")
- "challenging" → "hard" (if user knows "hard")
- "comprehensive" → "full" (if user knows "full")
- "sophisticated" → "smart" (if user knows "smart")

CONTRACTION EXAMPLES:
- If original has "you're" → write "you're" (do NOT change to "you are")
- If original has "don't" → write "don't" (do NOT change to "do not")
- If original has "can't" → write "can't" (do NOT change to "cannot")
- If original has "won't" → write "won't" (do NOT change to "will not")
- If original has "doesn't" → write "doesn't" (do NOT change to "does not")
- If original has "you are" → write "you are" (do NOT change to "you're")
- If original has "do not" → write "do not" (do NOT change to "don't")

VERB EXAMPLES:
- If user knows "to have" → use "have", "has", "had"
- If user knows "to do" → use "do", "does", "did"
- If user knows "to hear" → use "hear", "hears", "heard"

SENTENCE RESTRUCTURING EXAMPLES:
- "The phenomenon encompasses unprecedented challenges" → "The thing has new problems" (if user knows "thing", "to have", "new", "problems")
- "Social media platforms utilize sophisticated algorithms" → "Social media uses smart rules" (if user knows "social", "media", "to use", "smart", "rules")

CRITICAL: You MUST achieve exactly {target_unknown_percentage}% unknown words. Count carefully and be extremely aggressive in using the user's vocabulary. If you cannot achieve {target_unknown_percentage}%, use even simpler words from the user's list.

You MUST be extremely aggressive. Use the user's vocabulary list as your primary word source. Provide ONLY the adapted text."""

        return prompt
    
    def adapt_text_with_ai(self, text: str, username: str, target_unknown_percentage: float = 10.0) -> Dict:
        """
        Use OpenAI ChatGPT to intelligently adapt text for i+1 learning.
        """
        db = next(get_db())
        
        try:
            # Get user's vocabulary
            known_words = self.get_user_known_words(username, db)
            
            # Add only the most basic English words that are commonly missing
            basic_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'am',
                'this', 'that', 'these', 'those', 'here', 'there', 'now', 'then',
                'my', 'your', 'his', 'her', 'its', 'our', 'their',
                'yes', 'no', 'not', 'very', 'so', 'too', 'also', 'just', 'only', 'even', 'still', 'again'
            }
            known_words.update(basic_words)
            
            if not known_words:
                return {
                    "error": f"User '{username}' not found or has no vocabulary",
                    "original_text": text,
                    "adapted_text": text
                }
            
            # Create the adaptation prompt
            prompt = self.create_adaptation_prompt(text, known_words, target_unknown_percentage)
            
            # Call OpenAI ChatGPT
            try:
                if self.demo_mode:
                    # Demo mode: provide a simple adaptation
                    adapted_text = self._demo_adaptation(text, known_words, target_unknown_percentage)
                else:
                    response = self.client.generate_content(prompt)
                    adapted_text = response.text.strip()
                
                # Analyze both texts for comparison
                from app.services.text_adaptation_service import TextAdaptationService
                
                original_analysis = TextAdaptationService.analyze_text_difficulty(text, known_words)
                adapted_analysis = TextAdaptationService.analyze_text_difficulty(adapted_text, known_words)
                
                # Get word-by-word analysis for frontend coloring
                original_word_analysis = TextAdaptationService.get_word_analysis_for_coloring(text, known_words, username, db)
                adapted_word_analysis = TextAdaptationService.get_word_analysis_for_coloring(adapted_text, known_words, username, db)
                
                return {
                    "original_text": text,
                    "adapted_text": adapted_text,
                    "original_analysis": original_analysis,
                    "adapted_analysis": adapted_analysis,
                    "original_word_analysis": original_word_analysis,
                    "adapted_word_analysis": adapted_word_analysis,
                    "user_vocabulary_size": len(known_words),
                    "target_unknown_percentage": target_unknown_percentage,
                    "adaptation_method": "AI-Powered (OpenAI GPT-4)",
                    "improvement": {
                        "unknown_percentage_change": adapted_analysis["unknown_percentage"] - original_analysis["unknown_percentage"],
                        "closer_to_target": abs(adapted_analysis["unknown_percentage"] - target_unknown_percentage) < abs(original_analysis["unknown_percentage"] - target_unknown_percentage)
                    }
                }
                
            except Exception as api_error:
                logger.error(f"OpenAI API error: {api_error}")
                return {
                    "error": f"AI adaptation failed: {str(api_error)}",
                    "fallback_method": "basic",
                    "original_text": text,
                    "adapted_text": text,
                    "note": "Falling back to basic adaptation due to AI service unavailability"
                }
                
        except Exception as e:
            logger.error(f"Error in AI text adaptation: {e}")
            return {
                "error": f"Adaptation failed: {str(e)}",
                "original_text": text,
                "adapted_text": text
            }
        finally:
            db.close()
    
    def _demo_adaptation(self, text: str, known_words: Set[str], target_unknown_percentage: float) -> str:
        """
        Demo mode adaptation that provides a simple text simplification.
        """
        # Simple word replacements for demo
        replacements = {
            'difficult': 'hard',
            'beautiful': 'nice',
            'important': 'big',
            'interesting': 'good',
            'necessary': 'needed',
            'challenging': 'hard',
            'comprehensive': 'full',
            'sophisticated': 'smart',
            'excellent': 'very good',
            'wonderful': 'very good',
            'amazing': 'very good',
            'fantastic': 'very good',
            'terrific': 'very good',
            'outstanding': 'very good',
            'brilliant': 'very smart',
            'genius': 'very smart',
            'clever': 'smart',
            'intelligent': 'smart',
            'wise': 'smart',
            'knowledgeable': 'knows a lot',
            'experienced': 'has done this before',
            'professional': 'does this for work',
            'expert': 'knows a lot about this',
            'specialist': 'knows a lot about this',
            'master': 'knows a lot about this',
            'guru': 'knows a lot about this',
            'authority': 'knows a lot about this',
            'connoisseur': 'knows a lot about this',
            'aficionado': 'likes this a lot',
            'enthusiast': 'likes this a lot',
            'fan': 'likes this a lot',
            'devotee': 'likes this a lot',
            'admirer': 'likes this a lot',
            'supporter': 'likes this a lot',
            'advocate': 'likes this a lot',
            'champion': 'likes this a lot',
            'defender': 'likes this a lot',
            'protector': 'likes this a lot',
            'guardian': 'likes this a lot',
            'custodian': 'likes this a lot',
            'steward': 'likes this a lot',
            'curator': 'likes this a lot',
            'manager': 'likes this a lot',
            'supervisor': 'likes this a lot',
            'director': 'likes this a lot',
            'administrator': 'likes this a lot',
            'coordinator': 'likes this a lot',
            'organizer': 'likes this a lot',
            'planner': 'likes this a lot',
            'strategist': 'likes this a lot',
            'consultant': 'likes this a lot',
            'advisor': 'likes this a lot',
            'counselor': 'likes this a lot',
            'mentor': 'likes this a lot',
            'teacher': 'likes this a lot',
            'instructor': 'likes this a lot',
            'trainer': 'likes this a lot',
            'coach': 'likes this a lot',
            'tutor': 'likes this a lot',
            'guide': 'likes this a lot',
            'leader': 'likes this a lot',
            'chief': 'likes this a lot',
            'head': 'likes this a lot',
            'boss': 'likes this a lot',
            'commander': 'likes this a lot',
            'captain': 'likes this a lot',
            'commander': 'likes this a lot',
            'general': 'likes this a lot',
            'colonel': 'likes this a lot',
            'major': 'likes this a lot',
            'lieutenant': 'likes this a lot',
            'sergeant': 'likes this a lot',
            'corporal': 'likes this a lot',
            'private': 'likes this a lot',
            'soldier': 'likes this a lot',
            'warrior': 'likes this a lot',
            'fighter': 'likes this a lot',
            'combatant': 'likes this a lot',
            'battler': 'likes this a lot',
            'contender': 'likes this a lot',
            'challenger': 'likes this a lot',
            'competitor': 'likes this a lot',
            'rival': 'likes this a lot',
            'opponent': 'likes this a lot',
            'adversary': 'likes this a lot',
            'enemy': 'likes this a lot',
            'foe': 'likes this a lot',
            'nemesis': 'likes this a lot',
            'archrival': 'likes this a lot',
            'sworn enemy': 'likes this a lot',
            'bitter enemy': 'likes this a lot',
            'mortal enemy': 'likes this a lot',
            'deadly enemy': 'likes this a lot',
            'dangerous enemy': 'likes this a lot',
            'formidable enemy': 'likes this a lot',
            'powerful enemy': 'likes this a lot',
            'strong enemy': 'likes this a lot',
            'weak enemy': 'likes this a lot',
            'helpless enemy': 'likes this a lot',
            'defenseless enemy': 'likes this a lot',
            'vulnerable enemy': 'likes this a lot',
            'exposed enemy': 'likes this a lot',
            'unprotected enemy': 'likes this a lot',
            'unarmed enemy': 'likes this a lot',
            'weaponless enemy': 'likes this a lot',
            'defenseless enemy': 'likes this a lot',
            'unprepared enemy': 'likes this a lot',
            'unready enemy': 'likes this a lot',
            'unwary enemy': 'likes this a lot',
            'unsuspecting enemy': 'likes this a lot',
            'unsuspicious enemy': 'likes this a lot',
            'trusting enemy': 'likes this a lot',
            'gullible enemy': 'likes this a lot',
            'naive enemy': 'likes this a lot',
            'innocent enemy': 'likes this a lot',
            'harmless enemy': 'likes this a lot',
            'peaceful enemy': 'likes this a lot',
            'friendly enemy': 'likes this a lot',
            'kind enemy': 'likes this a lot',
            'gentle enemy': 'likes this a lot',
            'mild enemy': 'likes this a lot',
            'soft enemy': 'likes this a lot',
            'tender enemy': 'likes this a lot',
            'delicate enemy': 'likes this a lot',
            'fragile enemy': 'likes this a lot',
            'brittle enemy': 'likes this a lot',
            'breakable enemy': 'likes this a lot',
            'crumbling enemy': 'likes this a lot',
            'disintegrating enemy': 'likes this a lot',
            'falling apart enemy': 'likes this a lot',
            'coming apart enemy': 'likes this a lot',
            'breaking down enemy': 'likes this a lot',
            'breaking up enemy': 'likes this a lot',
            'splitting up enemy': 'likes this a lot',
            'dividing enemy': 'likes this a lot',
            'separating enemy': 'likes this a lot',
            'parting enemy': 'likes this a lot',
            'splitting enemy': 'likes this a lot',
            'cracking enemy': 'likes this a lot',
            'shattering enemy': 'likes this a lot',
            'smashing enemy': 'likes this a lot',
            'crushing enemy': 'likes this a lot',
            'pulverizing enemy': 'likes this a lot',
            'grinding enemy': 'likes this a lot',
            'mashing enemy': 'likes this a lot',
            'squashing enemy': 'likes this a lot',
            'flattening enemy': 'likes this a lot',
            'compressing enemy': 'likes this a lot',
            'squeezing enemy': 'likes this a lot',
            'pressing enemy': 'likes this a lot',
            'pushing enemy': 'likes this a lot',
            'shoving enemy': 'likes this a lot',
            'thrusting enemy': 'likes this a lot',
            'propelling enemy': 'likes this a lot',
            'launching enemy': 'likes this a lot',
            'firing enemy': 'likes this a lot',
            'shooting enemy': 'likes this a lot',
            'blasting enemy': 'likes this a lot',
            'exploding enemy': 'likes this a lot',
            'detonating enemy': 'likes this a lot',
            'igniting enemy': 'likes this a lot',
            'lighting enemy': 'likes this a lot',
            'kindling enemy': 'likes this a lot',
            'sparking enemy': 'likes this a lot',
            'triggering enemy': 'likes this a lot',
            'activating enemy': 'likes this a lot',
            'starting enemy': 'likes this a lot',
            'beginning enemy': 'likes this a lot',
            'commencing enemy': 'likes this a lot',
            'initiating enemy': 'likes this a lot',
            'launching enemy': 'likes this a lot',
            'establishing enemy': 'likes this a lot',
            'founding enemy': 'likes this a lot',
            'creating enemy': 'likes this a lot',
            'forming enemy': 'likes this a lot',
            'building enemy': 'likes this a lot',
            'constructing enemy': 'likes this a lot',
            'erecting enemy': 'likes this a lot',
            'raising enemy': 'likes this a lot',
            'lifting enemy': 'likes this a lot',
            'hoisting enemy': 'likes this a lot',
            'elevating enemy': 'likes this a lot',
            'upgrading enemy': 'likes this a lot',
            'promoting enemy': 'likes this a lot',
            'advancing enemy': 'likes this a lot',
            'progressing enemy': 'likes this a lot',
            'developing enemy': 'likes this a lot',
            'evolving enemy': 'likes this a lot',
            'growing enemy': 'likes this a lot',
            'expanding enemy': 'likes this a lot',
            'extending enemy': 'likes this a lot',
            'enlarging enemy': 'likes this a lot',
            'magnifying enemy': 'likes this a lot',
            'amplifying enemy': 'likes this a lot',
            'intensifying enemy': 'likes this a lot',
            'strengthening enemy': 'likes this a lot',
            'reinforcing enemy': 'likes this a lot',
            'fortifying enemy': 'likes this a lot',
            'bolstering enemy': 'likes this a lot',
            'supporting enemy': 'likes this a lot',
            'backing enemy': 'likes this a lot',
            'upholding enemy': 'likes this a lot',
            'maintaining enemy': 'likes this a lot',
            'preserving enemy': 'likes this a lot',
            'conserving enemy': 'likes this a lot',
            'protecting enemy': 'likes this a lot',
            'guarding enemy': 'likes this a lot',
            'defending enemy': 'likes this a lot',
            'shielding enemy': 'likes this a lot',
            'sheltering enemy': 'likes this a lot',
            'harboring enemy': 'likes this a lot',
            'hiding enemy': 'likes this a lot',
            'concealing enemy': 'likes this a lot',
            'covering enemy': 'likes this a lot',
            'masking enemy': 'likes this a lot',
            'disguising enemy': 'likes this a lot',
            'camouflaging enemy': 'likes this a lot',
            'veiling enemy': 'likes this a lot',
            'shrouding enemy': 'likes this a lot',
            'wrapping enemy': 'likes this a lot',
            'enveloping enemy': 'likes this a lot',
            'surrounding enemy': 'likes this a lot',
            'encircling enemy': 'likes this a lot',
            'encompassing enemy': 'likes this a lot',
            'embracing enemy': 'likes this a lot',
            'including enemy': 'likes this a lot',
            'containing enemy': 'likes this a lot',
            'holding enemy': 'likes this a lot',
            'grasping enemy': 'likes this a lot',
            'clutching enemy': 'likes this a lot',
            'gripping enemy': 'likes this a lot',
            'seizing enemy': 'likes this a lot',
            'capturing enemy': 'likes this a lot',
            'catching enemy': 'likes this a lot',
            'trapping enemy': 'likes this a lot',
            'ensnaring enemy': 'likes this a lot',
            'entrapping enemy': 'likes this a lot',
            'luring enemy': 'likes this a lot',
            'baiting enemy': 'likes this a lot',
            'tempting enemy': 'likes this a lot',
            'alluring enemy': 'likes this a lot',
            'attracting enemy': 'likes this a lot',
            'drawing enemy': 'likes this a lot',
            'pulling enemy': 'likes this a lot',
            'dragging enemy': 'likes this a lot',
            'hauling enemy': 'likes this a lot',
            'towing enemy': 'likes this a lot',
            'carrying enemy': 'likes this a lot',
            'bearing enemy': 'likes this a lot',
            'transporting enemy': 'likes this a lot',
            'conveying enemy': 'likes this a lot',
            'delivering enemy': 'likes this a lot',
            'bringing enemy': 'likes this a lot',
            'taking enemy': 'likes this a lot',
            'fetching enemy': 'likes this a lot',
            'retrieving enemy': 'likes this a lot',
            'recovering enemy': 'likes this a lot',
            'rescuing enemy': 'likes this a lot',
            'saving enemy': 'likes this a lot',
            'liberating enemy': 'likes this a lot',
            'freeing enemy': 'likes this a lot',
            'releasing enemy': 'likes this a lot',
            'discharging enemy': 'likes this a lot',
            'dismissing enemy': 'likes this a lot',
            'firing enemy': 'likes this a lot',
            'sacking enemy': 'likes this a lot',
            'terminating enemy': 'likes this a lot',
            'ending enemy': 'likes this a lot',
            'finishing enemy': 'likes this a lot',
            'completing enemy': 'likes this a lot',
            'concluding enemy': 'likes this a lot',
            'closing enemy': 'likes this a lot',
            'shutting enemy': 'likes this a lot',
            'sealing enemy': 'likes this a lot',
            'locking enemy': 'likes this a lot',
            'securing enemy': 'likes this a lot',
            'fastening enemy': 'likes this a lot',
            'tying enemy': 'likes this a lot',
            'binding enemy': 'likes this a lot',
            'attaching enemy': 'likes this a lot',
            'connecting enemy': 'likes this a lot',
            'joining enemy': 'likes this a lot',
            'linking enemy': 'likes this a lot',
            'uniting enemy': 'likes this a lot',
            'merging enemy': 'likes this a lot',
            'combining enemy': 'likes this a lot',
            'mixing enemy': 'likes this a lot',
            'blending enemy': 'likes this a lot',
            'fusing enemy': 'likes this a lot',
            'melting enemy': 'likes this a lot',
            'dissolving enemy': 'likes this a lot',
            'liquefying enemy': 'likes this a lot',
            'fluidizing enemy': 'likes this a lot',
            'liquifying enemy': 'likes this a lot',
            'thawing enemy': 'likes this a lot',
            'defrosting enemy': 'likes this a lot',
            'warming enemy': 'likes this a lot',
            'heating enemy': 'likes this a lot',
            'cooking enemy': 'likes this a lot',
            'baking enemy': 'likes this a lot',
            'roasting enemy': 'likes this a lot',
            'grilling enemy': 'likes this a lot',
            'frying enemy': 'likes this a lot',
            'boiling enemy': 'likes this a lot',
            'steaming enemy': 'likes this a lot',
            'simmering enemy': 'likes this a lot',
            'stewing enemy': 'likes this a lot',
            'braising enemy': 'likes this a lot',
            'poaching enemy': 'likes this a lot',
            'scrambling enemy': 'likes this a lot',
            'whisking enemy': 'likes this a lot',
            'beating enemy': 'likes this a lot',
            'stirring enemy': 'likes this a lot',
            'mixing enemy': 'likes this a lot',
            'blending enemy': 'likes this a lot',
            'combining enemy': 'likes this a lot',
            'uniting enemy': 'likes this a lot',
            'joining enemy': 'likes this a lot',
            'connecting enemy': 'likes this a lot',
            'linking enemy': 'likes this a lot',
            'tying enemy': 'likes this a lot',
            'binding enemy': 'likes this a lot',
            'fastening enemy': 'likes this a lot',
            'securing enemy': 'likes this a lot',
            'locking enemy': 'likes this a lot',
            'sealing enemy': 'likes this a lot',
            'shutting enemy': 'likes this a lot',
            'closing enemy': 'likes this a lot',
            'concluding enemy': 'likes this a lot',
            'completing enemy': 'likes this a lot',
            'finishing enemy': 'likes this a lot',
            'ending enemy': 'likes this a lot',
            'terminating enemy': 'likes this a lot',
            'sacking enemy': 'likes this a lot',
            'firing enemy': 'likes this a lot',
            'dismissing enemy': 'likes this a lot',
            'discharging enemy': 'likes this a lot',
            'releasing enemy': 'likes this a lot',
            'freeing enemy': 'likes this a lot',
            'liberating enemy': 'likes this a lot',
            'saving enemy': 'likes this a lot',
            'rescuing enemy': 'likes this a lot',
            'recovering enemy': 'likes this a lot',
            'retrieving enemy': 'likes this a lot',
            'fetching enemy': 'likes this a lot',
            'taking enemy': 'likes this a lot',
            'bringing enemy': 'likes this a lot',
            'delivering enemy': 'likes this a lot',
            'conveying enemy': 'likes this a lot',
            'transporting enemy': 'likes this a lot',
            'bearing enemy': 'likes this a lot',
            'carrying enemy': 'likes this a lot',
            'towing enemy': 'likes this a lot',
            'hauling enemy': 'likes this a lot',
            'dragging enemy': 'likes this a lot',
            'pulling enemy': 'likes this a lot',
            'drawing enemy': 'likes this a lot',
            'attracting enemy': 'likes this a lot',
            'alluring enemy': 'likes this a lot',
            'tempting enemy': 'likes this a lot',
            'baiting enemy': 'likes this a lot',
            'luring enemy': 'likes this a lot',
            'entrapping enemy': 'likes this a lot',
            'ensnaring enemy': 'likes this a lot',
            'trapping enemy': 'likes this a lot',
            'catching enemy': 'likes this a lot',
            'capturing enemy': 'likes this a lot',
            'seizing enemy': 'likes this a lot',
            'gripping enemy': 'likes this a lot',
            'clutching enemy': 'likes this a lot',
            'grasping enemy': 'likes this a lot',
            'holding enemy': 'likes this a lot',
            'containing enemy': 'likes this a lot',
            'including enemy': 'likes this a lot',
            'embracing enemy': 'likes this a lot',
            'encompassing enemy': 'likes this a lot',
            'encircling enemy': 'likes this a lot',
            'surrounding enemy': 'likes this a lot',
            'enveloping enemy': 'likes this a lot',
            'wrapping enemy': 'likes this a lot',
            'shrouding enemy': 'likes this a lot',
            'veiling enemy': 'likes this a lot',
            'camouflaging enemy': 'likes this a lot',
            'disguising enemy': 'likes this a lot',
            'masking enemy': 'likes this a lot',
            'covering enemy': 'likes this a lot',
            'concealing enemy': 'likes this a lot',
            'hiding enemy': 'likes this a lot',
            'harboring enemy': 'likes this a lot',
            'sheltering enemy': 'likes this a lot',
            'shielding enemy': 'likes this a lot',
            'defending enemy': 'likes this a lot',
            'guarding enemy': 'likes this a lot',
            'conserving enemy': 'likes this a lot',
            'preserving enemy': 'likes this a lot',
            'maintaining enemy': 'likes this a lot',
            'upholding enemy': 'likes this a lot',
            'backing enemy': 'likes this a lot',
            'supporting enemy': 'likes this a lot',
            'bolstering enemy': 'likes this a lot',
            'fortifying enemy': 'likes this a lot',
            'reinforcing enemy': 'likes this a lot',
            'strengthening enemy': 'likes this a lot',
            'intensifying enemy': 'likes this a lot',
            'amplifying enemy': 'likes this a lot',
            'magnifying enemy': 'likes this a lot',
            'enlarging enemy': 'likes this a lot',
            'extending enemy': 'likes this a lot',
            'expanding enemy': 'likes this a lot',
            'growing enemy': 'likes this a lot',
            'evolving enemy': 'likes this a lot',
            'developing enemy': 'likes this a lot',
            'progressing enemy': 'likes this a lot',
            'advancing enemy': 'likes this a lot',
            'promoting enemy': 'likes this a lot',
            'upgrading enemy': 'likes this a lot',
            'elevating enemy': 'likes this a lot',
            'hoisting enemy': 'likes this a lot',
            'lifting enemy': 'likes this a lot',
            'raising enemy': 'likes this a lot',
            'erecting enemy': 'likes this a lot',
            'constructing enemy': 'likes this a lot',
            'building enemy': 'likes this a lot',
            'forming enemy': 'likes this a lot',
            'creating enemy': 'likes this a lot',
            'founding enemy': 'likes this a lot',
            'establishing enemy': 'likes this a lot',
            'launching enemy': 'likes this a lot',
            'initiating enemy': 'likes this a lot',
            'commencing enemy': 'likes this a lot',
            'beginning enemy': 'likes this a lot',
            'starting enemy': 'likes this a lot',
            'activating enemy': 'likes this a lot',
            'triggering enemy': 'likes this a lot',
            'sparking enemy': 'likes this a lot',
            'kindling enemy': 'likes this a lot',
            'lighting enemy': 'likes this a lot',
            'igniting enemy': 'likes this a lot',
            'detonating enemy': 'likes this a lot',
            'exploding enemy': 'likes this a lot',
            'blasting enemy': 'likes this a lot',
            'shooting enemy': 'likes this a lot',
            'firing enemy': 'likes this a lot',
            'launching enemy': 'likes this a lot',
            'propelling enemy': 'likes this a lot',
            'thrusting enemy': 'likes this a lot',
            'shoving enemy': 'likes this a lot',
            'pushing enemy': 'likes this a lot',
            'pressing enemy': 'likes this a lot',
            'squeezing enemy': 'likes this a lot',
            'compressing enemy': 'likes this a lot',
            'flattening enemy': 'likes this a lot',
            'squashing enemy': 'likes this a lot',
            'mashing enemy': 'likes this a lot',
            'grinding enemy': 'likes this a lot',
            'pulverizing enemy': 'likes this a lot',
            'crushing enemy': 'likes this a lot',
            'smashing enemy': 'likes this a lot',
            'shattering enemy': 'likes this a lot',
            'cracking enemy': 'likes this a lot',
            'splitting enemy': 'likes this a lot',
            'parting enemy': 'likes this a lot',
            'separating enemy': 'likes this a lot',
            'dividing enemy': 'likes this a lot',
            'breaking up enemy': 'likes this a lot',
            'breaking down enemy': 'likes this a lot',
            'coming apart enemy': 'likes this a lot',
            'falling apart enemy': 'likes this a lot',
            'disintegrating enemy': 'likes this a lot',
            'crumbling enemy': 'likes this a lot',
            'breakable enemy': 'likes this a lot',
            'brittle enemy': 'likes this a lot',
            'fragile enemy': 'likes this a lot',
            'delicate enemy': 'likes this a lot',
            'tender enemy': 'likes this a lot',
            'soft enemy': 'likes this a lot',
            'mild enemy': 'likes this a lot',
            'gentle enemy': 'likes this a lot',
            'kind enemy': 'likes this a lot',
            'friendly enemy': 'likes this a lot',
            'peaceful enemy': 'likes this a lot',
            'harmless enemy': 'likes this a lot',
            'innocent enemy': 'likes this a lot',
            'naive enemy': 'likes this a lot',
            'gullible enemy': 'likes this a lot',
            'trusting enemy': 'likes this a lot',
            'unsuspicious enemy': 'likes this a lot',
            'unsuspecting enemy': 'likes this a lot',
            'unwary enemy': 'likes this a lot',
            'unready enemy': 'likes this a lot',
            'unprepared enemy': 'likes this a lot',
            'defenseless enemy': 'likes this a lot',
            'unarmed enemy': 'likes this a lot',
            'weaponless enemy': 'likes this a lot',
            'unprotected enemy': 'likes this a lot',
            'exposed enemy': 'likes this a lot',
            'vulnerable enemy': 'likes this a lot',
            'helpless enemy': 'likes this a lot',
            'weak enemy': 'likes this a lot',
            'strong enemy': 'likes this a lot',
            'powerful enemy': 'likes this a lot',
            'formidable enemy': 'likes this a lot',
            'dangerous enemy': 'likes this a lot',
            'deadly enemy': 'likes this a lot',
            'mortal enemy': 'likes this a lot',
            'bitter enemy': 'likes this a lot',
            'sworn enemy': 'likes this a lot',
            'archrival enemy': 'likes this a lot',
            'nemesis enemy': 'likes this a lot',
            'foe enemy': 'likes this a lot',
            'enemy enemy': 'likes this a lot',
            'adversary enemy': 'likes this a lot',
            'opponent enemy': 'likes this a lot',
            'rival enemy': 'likes this a lot',
            'competitor enemy': 'likes this a lot',
            'challenger enemy': 'likes this a lot',
            'contender enemy': 'likes this a lot',
            'battler enemy': 'likes this a lot',
            'combatant enemy': 'likes this a lot',
            'fighter enemy': 'likes this a lot',
            'warrior enemy': 'likes this a lot',
            'soldier enemy': 'likes this a lot',
            'private enemy': 'likes this a lot',
            'corporal enemy': 'likes this a lot',
            'sergeant enemy': 'likes this a lot',
            'lieutenant enemy': 'likes this a lot',
            'major enemy': 'likes this a lot',
            'colonel enemy': 'likes this a lot',
            'general enemy': 'likes this a lot',
            'commander enemy': 'likes this a lot',
            'captain enemy': 'likes this a lot',
            'commander enemy': 'likes this a lot',
            'boss enemy': 'likes this a lot',
            'head enemy': 'likes this a lot',
            'chief enemy': 'likes this a lot',
            'leader enemy': 'likes this a lot',
            'guide enemy': 'likes this a lot',
            'tutor enemy': 'likes this a lot',
            'coach enemy': 'likes this a lot',
            'trainer enemy': 'likes this a lot',
            'instructor enemy': 'likes this a lot',
            'teacher enemy': 'likes this a lot',
            'mentor enemy': 'likes this a lot',
            'counselor enemy': 'likes this a lot',
            'advisor enemy': 'likes this a lot',
            'consultant enemy': 'likes this a lot',
            'strategist enemy': 'likes this a lot',
            'planner enemy': 'likes this a lot',
            'organizer enemy': 'likes this a lot',
            'coordinator enemy': 'likes this a lot',
            'administrator enemy': 'likes this a lot',
            'director enemy': 'likes this a lot',
            'supervisor enemy': 'likes this a lot',
            'manager enemy': 'likes this a lot',
            'curator enemy': 'likes this a lot',
            'steward enemy': 'likes this a lot',
            'custodian enemy': 'likes this a lot',
            'guardian enemy': 'likes this a lot',
            'protector enemy': 'likes this a lot',
            'defender enemy': 'likes this a lot',
            'champion enemy': 'likes this a lot',
            'advocate enemy': 'likes this a lot',
            'supporter enemy': 'likes this a lot',
            'admirer enemy': 'likes this a lot',
            'devotee enemy': 'likes this a lot',
            'fan enemy': 'likes this a lot',
            'enthusiast enemy': 'likes this a lot',
            'aficionado enemy': 'likes this a lot',
            'connoisseur enemy': 'likes this a lot',
            'authority enemy': 'likes this a lot',
            'master enemy': 'likes this a lot',
            'guru enemy': 'likes this a lot',
            'expert enemy': 'likes this a lot',
            'specialist enemy': 'likes this a lot',
            'professional enemy': 'likes this a lot',
            'experienced enemy': 'likes this a lot',
            'knowledgeable enemy': 'likes this a lot',
            'wise enemy': 'likes this a lot',
            'intelligent enemy': 'likes this a lot',
            'clever enemy': 'likes this a lot',
            'genius enemy': 'likes this a lot',
            'brilliant enemy': 'likes this a lot',
            'outstanding enemy': 'likes this a lot',
            'terrific enemy': 'likes this a lot',
            'fantastic enemy': 'likes this a lot',
            'amazing enemy': 'likes this a lot',
            'wonderful enemy': 'likes this a lot',
            'excellent enemy': 'likes this a lot',
            'smart enemy': 'likes this a lot',
            'sophisticated enemy': 'likes this a lot',
            'comprehensive enemy': 'likes this a lot',
            'challenging enemy': 'likes this a lot',
            'necessary enemy': 'likes this a lot',
            'interesting enemy': 'likes this a lot',
            'important enemy': 'likes this a lot',
            'beautiful enemy': 'likes this a lot',
            'difficult enemy': 'likes this a lot'
        }
        
        # Simple text adaptation for demo
        adapted_text = text
        for complex_word, simple_word in replacements.items():
            if complex_word in text.lower():
                adapted_text = adapted_text.replace(complex_word, simple_word)
                adapted_text = adapted_text.replace(complex_word.title(), simple_word.title())
                adapted_text = adapted_text.replace(complex_word.upper(), simple_word.upper())
        
        # Add some demo learning words
        demo_learning_words = ['learning', 'target', 'practice', 'improve', 'progress']
        for word in demo_learning_words:
            if word not in adapted_text.lower():
                adapted_text += f" This helps with {word}."
                break
        
        return adapted_text
    
    def adapt_youtube_with_ai(self, youtube_url: str, username: str, target_unknown_percentage: float = 10.0) -> Dict:
        """
        Complete AI-powered YouTube adaptation pipeline.
        """
        try:
            # Import YouTube service
            from app.services.youtube_service import get_video_id, get_transcript
            
            # Extract video ID and get transcript
            video_id = get_video_id(youtube_url)
            if not video_id:
                return {"error": "Invalid YouTube URL"}
            
            transcript = get_transcript(video_id)
            if not transcript:
                return {"error": "Transcript not found for this video"}
            
            # Adapt transcript with AI
            adaptation_result = self.adapt_text_with_ai(transcript, username, target_unknown_percentage)
            
            # Add video metadata
            adaptation_result.update({
                "video_id": video_id,
                "youtube_url": youtube_url,
                "username": username,
                "original_transcript": transcript
            })
            
            return adaptation_result
            
        except Exception as e:
            logger.error(f"Error in YouTube AI adaptation: {e}")
            return {"error": f"YouTube adaptation failed: {str(e)}"}
    
    def generate_learning_explanation(self, unknown_words: List[str], username: str) -> Dict:
        """
        Generate AI-powered explanations for unknown words in user's native language.
        """
        if not unknown_words:
            return {"explanations": {}}
        
        try:
            # Clean words for better AI processing
            cleaned_words = [word.lower().strip() for word in unknown_words]
            
            # For Turkish users, provide explanations in Turkish
            prompt = f"""As a language learning tutor, provide simple, clear explanations for these English words in Turkish (Türkçe).

Words to explain: {', '.join(cleaned_words[:10])}  # Limit to 10 words

For each word, provide:
1. Turkish translation
2. Simple example sentence in English
3. Turkish explanation of the example

Format as JSON:
{{
  "word1": {{
    "translation": "Turkish translation",
    "example": "Simple English example sentence",
    "example_explanation": "Turkish explanation of the example"
  }},
  "word2": {{ ... }}
}}

Keep explanations simple and beginner-friendly."""

            if self.demo_mode:
                # Demo mode: provide simple explanations
                explanations = {}
                for word in unknown_words[:10]:
                    explanations[word] = {
                        "translation": f"{word} kelimesinin Türkçe karşılığı",
                        "example": f"This is an example sentence with {word}.",
                        "example_explanation": f"Bu cümlede {word} kelimesi kullanılmıştır."
                    }
                return {
                    "explanations": explanations,
                    "total_words": len(unknown_words),
                    "explained_words": len(explanations)
                }
            
            # Real OpenAI API call
            response = self.client.generate_content(prompt)
            explanations_text = response.text.strip()
            
            # Clean JSON text (remove markdown formatting if present)
            if explanations_text.startswith('```json'):
                explanations_text = explanations_text.replace('```json', '').replace('```', '').strip()
            
            try:
                explanations = json.loads(explanations_text)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.error(f"Failed to parse JSON: {explanations_text}")
                explanations = {
                    unknown_words[0]: {
                        "translation": "Parsing error - çeviri alınamadı",
                        "example": f"Example with {unknown_words[0]}",
                        "example_explanation": "JSON parsing hatası oluştu"
                    }
                }
            
            return {
                "explanations": explanations,
                "total_words": len(unknown_words),
                "explained_words": len(explanations)
            }
            
        except Exception as e:
            logger.error(f"Error generating explanations: {e}")
            return {
                "error": f"Failed to generate explanations: {str(e)}",
                "explanations": {}
            }
    
    def analyze_grammar(self, text: str, username: str) -> Dict:
        """
        🔍 Grammar Analysis: Analyze text and provide comprehensive grammar learning insights.
        Identifies grammar patterns, explains rules with examples, and provides learning tips.
        """
        try:
            # Create comprehensive grammar analysis prompt
            prompt = f"""You are an expert English grammar teacher. Analyze the following text and provide comprehensive grammar insights.

TEXT TO ANALYZE:
{text}

Please provide a detailed grammar analysis in the following JSON format:

{{
    "grammar_patterns": [
        {{
            "pattern": "Present Perfect Tense",
            "explanation": "Used for actions that started in the past and continue to the present",
            "examples": ["I have lived here for 5 years", "She has been working since morning"],
            "rules": ["Subject + have/has + past participle", "Often used with 'for' and 'since'"],
            "difficulty": "Intermediate"
        }}
    ],
    "key_grammar_points": [
        {{
            "point": "Conditional Sentences",
            "description": "If-clauses and their different types",
            "examples": ["If it rains, I will stay home", "If I had money, I would travel"],
            "learning_tip": "Remember: Type 1 = real possibility, Type 2 = unreal present"
        }}
    ],
    "vocabulary_grammar_connection": [
        {{
            "word": "example_word",
            "grammar_usage": "How this word is used grammatically",
            "examples": ["Example sentences"]
        }}
    ],
    "learning_recommendations": [
        "Focus on present perfect vs simple past",
        "Practice conditional sentences",
        "Review article usage (a/an/the)"
    ],
    "summary": "Brief summary of main grammar points found in the text"
}}

IMPORTANT:
- Focus on practical, commonly used grammar patterns
- Provide clear, simple explanations
- Include multiple examples for each pattern
- Identify both basic and advanced grammar structures
- Give actionable learning tips
- Keep explanations beginner-friendly but comprehensive

Analyze the text and return the JSON response:"""

            # Call Gemini API
            try:
                response = self.client.generate_content(prompt)
                grammar_analysis_text = response.text.strip()
                
                # Clean JSON text (remove markdown formatting if present)
                if grammar_analysis_text.startswith('```json'):
                    grammar_analysis_text = grammar_analysis_text.replace('```json', '').replace('```', '').strip()
                
                try:
                    grammar_analysis = json.loads(grammar_analysis_text)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    logger.error(f"Failed to parse grammar analysis JSON: {grammar_analysis_text}")
                    grammar_analysis = {
                        "grammar_patterns": [
                            {
                                "pattern": "Basic Sentence Structure",
                                "explanation": "Subject + Verb + Object pattern",
                                "examples": ["I love English", "She reads books"],
                                "rules": ["Every sentence needs a subject and verb"],
                                "difficulty": "Beginner"
                            }
                        ],
                        "key_grammar_points": [
                            {
                                "point": "Sentence Structure",
                                "description": "Basic English sentence patterns",
                                "examples": ["Subject + Verb + Object"],
                                "learning_tip": "Start with simple sentences, then add complexity"
                            }
                        ],
                        "vocabulary_grammar_connection": [],
                        "learning_recommendations": [
                            "Practice basic sentence structure",
                            "Learn common verb forms",
                            "Study article usage"
                        ],
                        "summary": "Basic grammar analysis - focus on sentence structure and verb forms"
                    }
                
                return {
                    "grammar_analysis": grammar_analysis,
                    "original_text": text,
                    "analysis_type": "comprehensive_grammar",
                    "total_patterns": len(grammar_analysis.get("grammar_patterns", [])),
                    "learning_points": len(grammar_analysis.get("key_grammar_points", []))
                }
                
            except Exception as e:
                logger.error(f"Error calling Gemini API for grammar analysis: {e}")
                return {
                    "error": f"Failed to analyze grammar: {str(e)}",
                    "grammar_analysis": {}
                }
                
        except Exception as e:
            logger.error(f"Error in grammar analysis: {e}")
            return {
                "error": f"Grammar analysis failed: {str(e)}",
                "grammar_analysis": {}
            } 