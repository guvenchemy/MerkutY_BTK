import os
import google.generativeai as genai
from typing import List, Dict, Set
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user_vocabulary import User, UserVocabulary, Vocabulary
from app.models.user_grammar_knowledge import UserGrammarKnowledge
from app.services.grammar_hierarchy_service import GrammarHierarchyService
import logging
import json

logger = logging.getLogger(__name__)

class AITextAdaptationService:
    """
    AI-Powered Text Adaptation using Google Gemini
    
    Implements Krashen's i+1 Hypothesis with intelligent text rewriting:
    - Maintains 90% known words + 10% challenging words
    - Uses user's grammar knowledge for appropriate complexity
    - Preserves meaning and context
    - Gradual vocabulary and grammar introduction for optimal learning
    """
    
    def __init__(self):
        # Get Gemini API key from environment variables
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required")
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel('gemini-1.5-flash')
        self.grammar_service = GrammarHierarchyService()
    
    @staticmethod
    def get_user_known_words(username: str, db: Session) -> Set[str]:
        """Get all words that user knows from database."""
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return set()
            
            # Get words marked as "known" by user
            known_words = db.query(UserVocabulary, Vocabulary).join(
                Vocabulary, UserVocabulary.vocabulary_id == Vocabulary.id
            ).filter(
                UserVocabulary.user_id == user.id,
                UserVocabulary.status.in_(["known", "ignored"])  # Include ignored words as known
            ).all()
            
            words_set = set()
            for user_vocab, vocab in known_words:
                word = vocab.word.lower().strip()
                words_set.add(word)
                
                # ✅ GELIŞMIŞ KELIME ÇEŞİTLEME SİSTEMİ
                # "to + verb" formatından kök kelimeyi al
                if word.startswith('to ') and len(word) > 3:
                    base_verb = word[3:]  # "to speak" -> "speak"
                    words_set.add(base_verb)
                    
                    # Kök fiilden tüm çekimleri oluştur
                    AITextAdaptationService._add_word_variations_static(words_set, base_verb)
                else:
                    # Normal kelimeler için çekimleri oluştur
                    AITextAdaptationService._add_word_variations_static(words_set, word)
                
            logging.info(f"Found {len(words_set)} known words for user {username}")
            return words_set
            
        except Exception as e:
            logging.error(f"Error getting user vocabulary: {e}")
            return set()
    
    def get_user_grammar_knowledge(self, username: str, db: Session) -> Dict:
        """Get user's grammar knowledge and calculate appropriate level."""
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return {"known_patterns": [], "user_level": "A1", "avoid_patterns": []}
            
            # Get user's known grammar patterns
            known_grammar = db.query(UserGrammarKnowledge).filter(
                UserGrammarKnowledge.user_id == user.id,
                UserGrammarKnowledge.status == "known"
            ).all()
            
            known_patterns = [g.grammar_pattern for g in known_grammar]
            
            # Calculate user level based on combined vocabulary + grammar
            user_level_info = self.grammar_service.calculate_user_level(user.id, db)
            user_level = user_level_info.get("user_level", {}).get("level", "A1")
            
            # Debug log
            logging.info(f"User level calculation for {username}: {user_level_info}")
            logging.info(f"Extracted user level: {user_level}")
            
            # Get vocabulary count for level estimation
            vocab_count = db.query(UserVocabulary).filter(
                UserVocabulary.user_id == user.id,
                UserVocabulary.status == "known"
            ).count()
            
            # If user has no grammar patterns but significant vocabulary, 
            # estimate grammar based on vocabulary level (more reliable)
            if not known_patterns and vocab_count > 1000:
                if vocab_count >= 4000:  # B2+ level vocabulary
                    user_level = "B2"  # Override if vocabulary suggests higher level
                    known_patterns = [
                        "present_simple", "past_simple", "future_simple", "present_continuous",
                        "basic_questions", "simple_conditionals", "basic_comparatives", 
                        "modal_verbs", "basic_passive", "present_perfect_simple",
                        "past_continuous", "relative_clauses_basic", "reported_speech_basic"
                    ]
                elif vocab_count >= 2000:  # B1 level vocabulary
                    user_level = "B1"
                    known_patterns = [
                        "present_simple", "past_simple", "future_simple", "present_continuous",
                        "basic_questions", "simple_conditionals", "basic_comparatives", "modal_verbs"
                    ]
                elif vocab_count >= 1000:  # A2 level vocabulary
                    user_level = "A2"
                    known_patterns = ["present_simple", "past_simple", "future_simple", "basic_questions"]
                
                logging.info(f"Overrode user level to {user_level} based on vocabulary: {vocab_count} words")
            
            # Determine patterns to avoid (higher than user's level)
            all_patterns = []
            for level, patterns in self.grammar_service.GRAMMAR_HIERARCHY.items():
                all_patterns.extend(patterns)
            
            # Avoid patterns that are 2+ levels above user
            level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
            current_index = level_order.index(user_level) if user_level in level_order else 0
            avoid_patterns = []
            
            for level, patterns in self.grammar_service.GRAMMAR_HIERARCHY.items():
                level_index = level_order.index(level) if level in level_order else 0
                if level_index > current_index + 1:  # More than 1 level above
                    avoid_patterns.extend(patterns)
            
            return {
                "known_patterns": known_patterns,
                "user_level": user_level,
                "avoid_patterns": avoid_patterns
            }
            
        except Exception as e:
            logging.error(f"Error getting user grammar knowledge: {e}")
            return {"known_patterns": [], "user_level": "A1", "avoid_patterns": []}
    
    def create_adaptation_prompt(self, text: str, known_words: Set[str], grammar_info: Dict, target_unknown_percentage: float = 10.0) -> str:
        """
        Create a sophisticated prompt for Gemini to adapt text according to i+1 theory.
        Now includes user's grammar knowledge for more precise adaptation.
        """
        known_words_sample = list(known_words)[:100] if len(known_words) > 100 else list(known_words)
        known_patterns = grammar_info.get("known_patterns", [])
        user_level = grammar_info.get("user_level", "A1")
        avoid_patterns = grammar_info.get("avoid_patterns", [])
        
        prompt = f"""You are an expert English teacher implementing Stephen Krashen's i+1 hypothesis for optimal language acquisition.

CRITICAL MISSION: Adapt this text to be EXACTLY 90% comprehensible and 10% challenging for this specific student.

STUDENT PROFILE:
- Current Level: {user_level}
- Known Words: {', '.join(known_words_sample)}
- Known Grammar: {', '.join(known_patterns[:20])}
- AVOID these advanced grammar patterns: {', '.join(avoid_patterns[:15])}

ORIGINAL TEXT:
{text}

ADAPTATION RULES:
1. **VOCABULARY TARGET**: Use 90% words from student's known vocabulary + exactly 10% new learning words
2. **GRAMMAR TARGET**: Use only grammar patterns the student knows + maximum 1-2 new patterns from their level
3. **PRESERVE MEANING**: Keep the EXACT same information and message
4. **SENTENCE LENGTH**: Keep sentences short and clear (maximum 15 words per sentence)
5. **AVOID COMPLEXITY**: Do NOT use grammar patterns from the avoid list

VOCABULARY STRATEGY:
- If student knows "big", use "big" instead of "huge", "enormous", "massive"
- If student knows "good", use "good" instead of "excellent", "wonderful", "fantastic"
- If student knows "make", use "make" instead of "create", "construct", "produce"
- Choose the simplest synonym from their vocabulary

GRAMMAR STRATEGY:
- If student knows "present_simple" but not "present_perfect": Use "I work" instead of "I have worked"
- If student knows "past_simple" but not "past_continuous": Use "I walked" instead of "I was walking"
- If student knows "basic_questions" but not "question_formation": Use "What is this?" instead of "What do you think this could be?"

FORBIDDEN PATTERNS (DO NOT USE):
{', '.join(avoid_patterns)}

SENTENCE EXAMPLES:
Complex: "The sophisticated algorithm analyzes comprehensive data sets to determine optimal solutions."
→ Simple: "The smart computer program looks at all information to find the best answers."

Complex: "Having completed the arduous journey, they finally reached their destination."
→ Simple: "They finished the hard trip. They got to their place."

TARGET OUTPUT:
- 90% vocabulary comprehension (use known words)
- 10% vocabulary challenge (introduce 2-3 new words maximum)
- Grammar appropriate for {user_level} level
- Same meaning as original
- Natural English flow

IMPORTANT: Write ONLY the adapted English text. No explanations or comments."""

        return prompt
    
    def create_cefr_adaptation_prompt(self, text: str, current_level: str, target_level: str) -> str:
        """
        🎯 NEW CEFR-BASED ADAPTATION PROMPT
        
        Creates a prompt that adapts text to a specific CEFR level.
        This replaces the old vocabulary-percentage system.
        """
        
        # CEFR Level Descriptions
        level_descriptions = {
            "A1": "Very basic vocabulary (family, shopping, food), present tense, simple sentences",
            "A2": "Common everyday vocabulary, past/future tenses, basic connecting words",
            "B1": "Work/study vocabulary, conditional sentences, expressing opinions",
            "B2": "Abstract topics, complex sentences, passive voice, reported speech",
            "C1": "Specialized vocabulary, advanced grammar, nuanced expression",
            "C2": "Near-native vocabulary, all grammar structures, sophisticated style"
        }
        
        prompt = f"""You are an expert English language teacher specializing in CEFR-based text adaptation.

🎯 TASK: Rewrite the following text EXACTLY at {target_level} CEFR level.

📊 USER CONTEXT:
- Current Level: {current_level}
- Target Level: {target_level} (one level above current)

📋 {target_level} LEVEL REQUIREMENTS:
{level_descriptions.get(target_level, "Standard level")}

🔑 ADAPTATION RULES:

1. **VOCABULARY**: Use vocabulary appropriate for {target_level} level only
2. **GRAMMAR**: Use grammar structures typical of {target_level} level
3. **COMPLEXITY**: Match the complexity expected at {target_level} level
4. **MEANING**: Keep the exact same meaning and information
5. **NATURAL FLOW**: Write naturally - don't make it sound artificial

📝 LEVEL-SPECIFIC GUIDELINES:

A1-A2: Very simple words, present/past tense, short sentences
B1-B2: More complex vocabulary, various tenses, longer connected sentences  
C1-C2: Advanced vocabulary, sophisticated grammar, complex sentence structures

❌ FORBIDDEN:
- Do NOT explain what you're doing
- Do NOT add extra information
- Do NOT use vocabulary/grammar above {target_level} level
- Do NOT use vocabulary/grammar below {target_level} level

🎯 TARGET TEXT TO ADAPT:
"{text}"

✍️ ADAPTED TEXT (write ONLY the adapted text, nothing else):"""

        return prompt
    
    def adapt_text_with_ai(self, text: str, username: str, db: Session, target_unknown_percentage: float = 10.0) -> Dict:
        """
        🎯 CEFR LEVEL-BASED ADAPTATION (Updated System)
        
        New Strategy:
        1. Detect user's current CEFR level (A1, A2, B1, B2, C1, C2)
        2. Analyze original text's CEFR level
        3. Rewrite text at user's level + 1 (i+1 principle)
        
        Examples:
        - User B2 → Text adapted to C1 level
        - User A2 → Text adapted to B1 level
        """
        try:
            # Get user object first
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return {"error": f"User '{username}' not found"}
            
            # Get user's CEFR level instead of vocabulary
            user_level_info = self.grammar_service.calculate_user_level(user.id, db)
            
            # Extract user's current CEFR level
            current_level = user_level_info.get("user_level", {}).get("level", "A1")
            
            # Calculate target level (current + 1)
            cefr_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
            try:
                current_index = cefr_levels.index(current_level)
                target_level = cefr_levels[min(current_index + 1, len(cefr_levels) - 1)]
            except ValueError:
                # If level not found, default to A2
                target_level = "A2"
            
            # Create the NEW CEFR-based adaptation prompt
            prompt = self.create_cefr_adaptation_prompt(text, current_level, target_level)
            
            # Call Google Gemini
            try:
                response = self.client.generate_content(prompt)
                adapted_text = response.text.strip()
                
                # Clean up any formatting artifacts
                adapted_text = adapted_text.replace('```', '').strip()
                if adapted_text.startswith('"') and adapted_text.endswith('"'):
                    adapted_text = adapted_text[1:-1]
                
                # Generate adaptation statistics
                adaptation_info = {
                    "user_current_level": current_level,
                    "target_level": target_level,
                    "adaptation_strategy": f"CEFR Level-Based: {current_level} → {target_level}",
                    "method": "i+1 CEFR Progression"
                }
                
                return {
                    "original_text": text,
                    "adapted_text": adapted_text,
                    "adaptation_method": f"CEFR Level Adaptation: {target_level}",
                    "adaptation_info": adaptation_info,
                    "user_level": current_level,
                    "target_level": target_level,
                    "success": True
                }
                
            except Exception as api_error:
                logging.error(f"Gemini API error: {str(api_error)}")
                return {
                    "error": f"AI adaptation failed: {str(api_error)}",
                    "original_text": text,
                    "adapted_text": text
                }
                
        except Exception as e:
            logging.error(f"Adaptation service error: {str(e)}")
            return {
                "error": f"Adaptation failed: {str(e)}",
                "original_text": text,
                "adapted_text": text
            }
    
    def _demo_adaptation(self, text: str, known_words: Set[str], target_unknown_percentage: float) -> str:
        """
        Demo mode adaptation using AI for simple text simplification.
        """
        try:
            # Use AI for demo adaptation too
            prompt = f"""Please simplify this text for English language learners.
            Keep it simple and clear. Use basic vocabulary.
            
            Text to simplify:
            {text}
            
            Return only the simplified text, nothing else."""
            
            response = self.client.generate_content(prompt)
            adapted_text = response.text.strip()
            return adapted_text
            
        except Exception as e:
            logging.error(f"Demo adaptation failed: {e}")
            # Fallback: return original text with note
            return f"{text}\n\n[Note: This is a simplified version for learning]"
    
    def adapt_youtube_with_ai(self, youtube_url: str, username: str, db: Session, target_unknown_percentage: float = 10.0) -> Dict:
        """
        Complete AI-powered YouTube adaptation pipeline.
        """
        try:
            # Import YouTube service
            from app.services.yt_dlp_service import YTDlpService
            
            # Extract video ID and get transcript
            youtube_service = YTDlpService()
            video_id = youtube_service.get_video_id(youtube_url)
            if not video_id:
                return {"error": "Invalid YouTube URL"}
            
            transcript_result = youtube_service.get_transcript(video_id)
            if not transcript_result.get("success"):
                return {"error": f"Transcript not found: {transcript_result.get('error', 'Unknown error')}"}
            
            transcript = transcript_result["transcript"]
            
            # Adapt transcript with AI using NEW CEFR system
            adaptation_result = self.adapt_text_with_ai(transcript, username, db, target_unknown_percentage)
            
            # Add video metadata
            adaptation_result.update({
                "video_id": video_id,
                "youtube_url": youtube_url,
                "username": username,
                "original_transcript": transcript
            })
            
            return adaptation_result
            
        except Exception as e:
            logging.error(f"Error in YouTube AI adaptation: {e}")
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
                logging.error(f"Failed to parse JSON: {explanations_text}")
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
            logging.error(f"Error generating explanations: {e}")
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
                    logging.error(f"Failed to parse grammar analysis JSON: {grammar_analysis_text}")
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
                logging.error(f"Error calling Gemini API for grammar analysis: {e}")
                return {
                    "error": f"Failed to analyze grammar: {str(e)}",
                    "grammar_analysis": {}
                }
                
        except Exception as e:
            logging.error(f"Error in grammar analysis: {e}")
            return {
                "error": f"Grammar analysis failed: {str(e)}",
                "grammar_analysis": {}
            }
    
    @staticmethod
    def _add_word_variations_static(words_set: Set[str], word: str):
        """
        Static version of word variations for use in static methods.
        """
        if not word or len(word) < 2:
            return
            
        # Orijinal kelimeyi ekle
        words_set.add(word)
        
        # Basit çekim kuralları - sadece temel formlar
        try:
            # -ing formu
            if word.endswith('e') and len(word) > 2:
                words_set.add(word[:-1] + 'ing')  # use -> using
            else:
                words_set.add(word + 'ing')  # work -> working
            
            # -ed formu  
            if word.endswith('e') and len(word) > 2:
                words_set.add(word + 'd')  # use -> used
            else:
                words_set.add(word + 'ed')  # work -> worked
            
            # -s/-es formu
            if word.endswith(('s', 'sh', 'ch', 'x', 'z')) or word.endswith('o'):
                words_set.add(word + 'es')  # go -> goes
            elif word.endswith('y') and len(word) > 2:
                words_set.add(word[:-1] + 'ies')  # try -> tries
            else:
                words_set.add(word + 's')  # work -> works
                
        except Exception as e:
            # Hata durumunda sadece orijinal kelimeyi ekle
            logging.warning(f"Error in word variations for '{word}': {e}")
            pass

    def _add_word_variations(self, words_set: Set[str], word: str):
        """
        Kelimeye ait tüm çekimli hallerini words_set'e ekler.
        Basitleştirilmiş ve performans odaklı versiyon.
        """
        if not word or len(word) < 2:
            return
            
        # Orijinal kelimeyi ekle
        words_set.add(word)
        
        # Basit çekim kuralları - sadece temel formlar
        try:
            # -ing formu
            if word.endswith('e') and len(word) > 2:
                words_set.add(word[:-1] + 'ing')  # use -> using
            else:
                words_set.add(word + 'ing')  # work -> working
            
            # -ed formu  
            if word.endswith('e') and len(word) > 2:
                words_set.add(word + 'd')  # use -> used
            else:
                words_set.add(word + 'ed')  # work -> worked
            
            # -s/-es formu
            if word.endswith(('s', 'sh', 'ch', 'x', 'z')) or word.endswith('o'):
                words_set.add(word + 'es')  # go -> goes
            elif word.endswith('y') and len(word) > 2:
                words_set.add(word[:-1] + 'ies')  # try -> tries
            else:
                words_set.add(word + 's')  # work -> works
                
        except Exception as e:
            # Hata durumunda sadece orijinal kelimeyi ekle
            logging.warning(f"Error in word variations for '{word}': {e}")
            pass 