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
    
    Implements Current Level Approach with intelligent text rewriting:
    - Maintains 95-100% known words for full comprehension
    - Uses user's grammar knowledge for appropriate complexity
    - Preserves meaning and context
    - Comfortable learning environment at user's current level
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
    
    def create_adaptation_prompt(self, text: str, known_words: Set[str], grammar_info: Dict, target_unknown_percentage: float = 5.0) -> str:
        """
        Create a sophisticated prompt for Gemini to adapt text to user's current level (i level).
        Focuses on making text fully comprehensible using only known vocabulary and grammar.
        """
        known_words_sample = list(known_words)[:100] if len(known_words) > 100 else list(known_words)
        known_patterns = grammar_info.get("known_patterns", [])
        user_level = grammar_info.get("user_level", "A1")
        avoid_patterns = grammar_info.get("avoid_patterns", [])
        
        prompt = f"""You are an expert English teacher adapting text to the student's CURRENT LEVEL for maximum comprehension.

CRITICAL MISSION: Adapt this text to be FULLY COMPREHENSIBLE (95-100%) for this specific student using only their known vocabulary and grammar.

STUDENT PROFILE:
- Current Level: {user_level}
- Known Words: {', '.join(known_words_sample)}
- Known Grammar: {', '.join(known_patterns[:20])}
- STRICTLY AVOID these patterns: {', '.join(avoid_patterns[:15])}

ORIGINAL TEXT:
{text}

ADAPTATION RULES (CURRENT LEVEL - i APPROACH):
1. **VOCABULARY TARGET**: Use 95-100% words from student's known vocabulary ONLY
2. **GRAMMAR TARGET**: Use ONLY grammar patterns the student already knows
3. **PRESERVE MEANING**: Keep the EXACT same information and message
4. **SENTENCE LENGTH**: Keep sentences short and clear (maximum 12 words per sentence)
5. **STRICT AVOIDANCE**: NEVER use unknown grammar patterns or vocabulary

VOCABULARY STRATEGY:
- ONLY use words from student's known vocabulary list
- If a concept requires unknown words, explain with multiple known words
- Replace ALL unknown words with simpler alternatives from their vocabulary
- Example: "enormous" → "very big" (if student knows "very" and "big")

GRAMMAR STRATEGY:
- ONLY use grammar patterns from the known list
- If student knows only "present_simple": Use only "I work", "He works", etc.
- If student knows only "past_simple": Use only "I worked", "He went", etc.
- NO complex grammar - keep it at their current level

STRICTLY FORBIDDEN:
- Unknown vocabulary (not in their known words list)
- Unknown grammar patterns (from avoid list)
- Complex sentence structures beyond their level

CURRENT LEVEL EXAMPLES:
Complex: "The sophisticated algorithm analyzes comprehensive data sets to determine optimal solutions."
→ Current Level: "The smart computer program looks at information to find good answers."

Complex: "Having completed the arduous journey, they finally reached their destination."
→ Current Level: "They finished the hard trip. Now they are at their place."

TARGET OUTPUT FORMAT:
- Use ONLY vocabulary and grammar from student's current level
- Write clear, simple sentences (max 12 words each)
- Maintain original meaning completely
- Ensure 95-100% comprehensibility for current level
- Natural English flow within level constraints

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
    
    def adapt_text_with_ai(self, text: str, username: str, db: Session, target_unknown_percentage: float = 0.0) -> Dict:
        """
        🎯 CEFR LEVEL-BASED ADAPTATION (Current Level System)
        
        New Strategy:
        1. Detect user's current CEFR level (A1, A2, B1, B2, C1, C2)
        2. Analyze original text's CEFR level
        3. Rewrite text at user's EXACT level (current level approach)
        
        Examples:
        - User B2 → Text adapted to B2 level (current level)
        - User A2 → Text adapted to A2 level (current level)
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
            
            # Use current level (no +1)
            target_level = current_level
            
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
                    "adaptation_strategy": f"CEFR Level-Based: {current_level} → {target_level} (Current Level)",
                    "method": "Current Level Adaptation"
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
    def detect_cefr_level(self, text: str) -> Dict[str, any]:
        """
        🎯 CEFR LEVEL DETECTION using AI
        
        Analyzes text and determines CEFR level (A1-C2) with confidence score.
        Returns detailed analysis for library filtering.
        """
        try:
            prompt = f"""
🎯 CEFR LEVEL ANALYSIS TASK

Analyze the following English text and determine its CEFR level.

ANALYSIS CRITERIA:
📚 VOCABULARY COMPLEXITY:
- A1: Basic everyday words (300-600 words)
- A2: Common words, simple descriptions (600-1200 words) 
- B1: More varied vocabulary, some abstract concepts (1200-2500 words)
- B2: Wide vocabulary range, specialized terms (2500-3250 words)
- C1: Advanced vocabulary, nuanced expressions (3250-5000 words)
- C2: Very advanced, sophisticated language (5000+ words)

🔤 GRAMMAR COMPLEXITY:
- A1: Present simple, basic sentence structures
- A2: Past simple, future, basic comparatives
- B1: Present perfect, conditional, complex sentences
- B2: Passive voice, reported speech, advanced tenses
- C1: Complex grammar, sophisticated structures
- C2: Near-native grammar mastery

📝 SENTENCE STRUCTURE:
- A1-A2: Simple, short sentences
- B1-B2: Compound and some complex sentences  
- C1-C2: Complex, sophisticated sentence structures

🎯 TEXT TO ANALYZE:
"{text[:1000]}..." 

PROVIDE YOUR ANALYSIS IN THIS EXACT JSON FORMAT:
{{
    "cefr_level": "B1",
    "confidence": 85,
    "analysis": "This text demonstrates B1 level complexity with present perfect tense, conditional structures, and vocabulary around 1500 words. Sentence structures are moderately complex with some subordinate clauses.",
    "vocabulary_level": "B1",
    "grammar_level": "B1", 
    "sentence_complexity": "B1",
    "key_indicators": [
        "Present perfect tense usage",
        "Conditional sentences", 
        "Moderate vocabulary complexity",
        "Some complex sentence structures"
    ],
    "word_count_estimate": 1500
}}

RESPOND ONLY WITH THE JSON, NO OTHER TEXT."""

            response = self.client.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up response
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            # Parse JSON response
            try:
                analysis_result = json.loads(result_text)
                return {
                    "success": True,
                    "cefr_level": analysis_result.get("cefr_level", "B1"),
                    "confidence": analysis_result.get("confidence", 50),
                    "analysis": analysis_result.get("analysis", "AI analysis completed"),
                    "vocabulary_level": analysis_result.get("vocabulary_level", "B1"),
                    "grammar_level": analysis_result.get("grammar_level", "B1"),
                    "sentence_complexity": analysis_result.get("sentence_complexity", "B1"),
                    "key_indicators": analysis_result.get("key_indicators", []),
                    "word_count_estimate": analysis_result.get("word_count_estimate", len(text.split()))
                }
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error in CEFR detection: {e}")
                return {
                    "success": False,
                    "error": "Failed to parse AI response",
                    "cefr_level": "B1",
                    "confidence": 50,
                    "analysis": "Default analysis due to parsing error"
                }
                
        except Exception as e:
            logger.error(f"Error in CEFR level detection: {e}")
            return {
                "success": False,
                "error": str(e),
                "cefr_level": "B1", 
                "confidence": 50,
                "analysis": "Error occurred during analysis"
            }
