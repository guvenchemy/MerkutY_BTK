import os
import json
import logging
import re
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import google.generativeai as genai
from app.services.grammar_hierarchy_service import GrammarHierarchyService

logger = logging.getLogger(__name__)


class AITeacherService:
    """
    Intelligent AI Teacher Service
    Provides personalized, interactive grammar explanations with quizzes
    Adapts to user's knowledge level and avoids explaining known concepts
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.grammar_service = GrammarHierarchyService()
    
    async def analyze_text_for_user(self, text: str, user_id: int, db: Session) -> Dict:
        """
        Analyze text and provide personalized grammar explanations for user
        
        Args:
            text: Text to analyze
            user_id: User ID for personalization
            db: Database session
            
        Returns:
            Dict with personalized analysis and explanations
        """
        try:
            # 1. Detect grammar patterns in text
            detected_patterns = self._detect_grammar_patterns(text)
            
            # 2. Filter to unknown patterns only
            unknown_patterns = self.grammar_service.get_unknown_grammar_patterns(
                user_id, detected_patterns, db
            )
            
            if not unknown_patterns:
                return {
                    "success": True,
                    "message": "Bu metindeki tüm grammar yapılarını zaten biliyorsunuz! 🎉",
                    "explanations": [],
                    "user_level": self.grammar_service.calculate_user_level(user_id, db)
                }
            
            # 3. Generate explanations for unknown patterns
            explanations = []
            for pattern in unknown_patterns:  # Show ALL unknown patterns, not just first 3
                explanation = await self._generate_grammar_explanation(
                    text, pattern, user_id, db
                )
                if explanation and explanation.get("success"):
                    explanations.append(explanation["data"])
            
            return {
                "success": True,
                "explanations": explanations,
                "patterns_explained": len(explanations),
                "total_patterns_detected": len(detected_patterns),
                "user_level": self.grammar_service.calculate_user_level(user_id, db)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _detect_grammar_patterns(self, text: str) -> List[str]:
        """
        Detect grammar patterns in text using regex patterns
        Enhanced with better pattern detection order and accuracy
        """
        patterns_found = []
        
        # Grammar pattern definitions - ORDER MATTERS! (More specific first)
        pattern_map = {
            # Complex patterns first (to avoid false positives)
            "present_perfect_continuous": [
                r'\b(have|has)\s+been\s+\w+ing\b',  # have/has been + V-ing
                r'\b(have|has)\s+been\s+\w+ing\s+(for|since)\b'  # with time expressions
            ],
            "present_perfect": [
                r'\b(have|has)\s+\w+ed\b',  # have/has + past participle
                r'\b(have|has)\s+(been|gone|done|seen|made|taken|given)\b'  # irregular verbs
            ],
            "past_perfect": [
                r'\bhad\s+\w+ed\b',  # had + past participle
                r'\bhad\s+(been|gone|done|seen|made|taken|given)\b'
            ],
            "time_expressions": [
                r'\b(for|since)\s+(two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(years?|months?|days?|hours?|minutes?)\b',
                r'\b(yesterday|today|tomorrow|now|then|already|just|yet|ever|never)\b',
                r'\b(last|next|this)\s+(year|month|week|day|time)\b'
            ],
            "adjective_intensifiers": [
                r'\b(very|really|quite|extremely|incredibly|amazingly|absolutely|totally)\s+\w+\b',
                r'\b(so|such)\s+(a|an)?\s*\w+\b',
                r'\bit\s+is\s+(amazing|wonderful|great|fantastic|terrible|awful|beautiful|interesting)\b'
            ],
            "present_continuous": [
                r'\b(am|is|are)\s+\w+ing\b'  # am/is/are + V-ing
            ],
            "past_continuous": [
                r'\b(was|were)\s+\w+ing\b'  # was/were + V-ing
            ],
            "future_continuous": [
                r'\bwill\s+be\s+\w+ing\b',  # will be + V-ing
                r'\b(am|is|are)\s+going\s+to\s+be\s+\w+ing\b'  # going to be + V-ing
            ],
            "passive_voice_simple": [
                r'\b(am|is|are|was|were)\s+\w+ed\b',  # be + past participle
                r'\b(am|is|are|was|were)\s+(made|taken|given|seen|done|written|spoken)\b'
            ],
            "passive_voice_perfect": [
                r'\b(have|has|had)\s+been\s+\w+ed\b',  # have/has/had been + past participle
                r'\bwill\s+have\s+been\s+\w+ed\b'  # will have been + past participle
            ],
            "conditionals_type1": [
                r'\bif\s+\w+.*,\s*\w+.*will\b',  # if + present, will + infinitive
                r'\bif\s+\w+.*will\b'
            ],
            "conditionals_type2": [
                r'\bif\s+\w+.*would\b',  # if + past, would + infinitive
                r'\bif\s+.*were.*would\b'
            ],
            "conditionals_type3": [
                r'\bif\s+.*had\s+\w+ed.*would\s+have\b',  # if + past perfect, would have + participle
                r'\bif\s+.*had\s+.*would\s+have\s+\w+ed\b'
            ],
            "modal_verbs_basic": [
                r'\b(can|could|may|might|must|should|would|will|shall)\s+\w+\b',
                r'\b(ought\s+to|used\s+to|had\s+better)\s+\w+\b'
            ],
            "modal_verbs_advanced": [
                r'\b(might\s+have|could\s+have|should\s+have|would\s+have|must\s+have)\s+\w+ed\b',
                r'\b(can\'t\s+have|couldn\'t\s+have|shouldn\'t\s+have)\s+\w+ed\b'
            ],
            "relative_clauses_basic": [
                r'\b(who|which|that|where|when)\s+\w+',  # relative pronouns
                r'\b(whose|whom)\s+\w+'
            ],
            "relative_clauses_advanced": [
                r'\bthe\s+\w+\s+(who|which|that)\s+\w+',  # the person who/which
                r'\b\w+,\s+(who|which)\s+\w+',  # non-defining relative clauses
            ],
            "question_formation": [
                r'\b(what|where|when|why|how|who|which)\s+(do|does|did|are|is|was|were|will|would|can|could)\b',
                r'\b(do|does|did|are|is|was|were|will|would|can|could)\s+\w+\s+\w+\?'
            ],
            "gerunds_infinitives": [
                r'\b(enjoy|love|hate|like|dislike|avoid|finish|stop)\s+\w+ing\b',  # verbs + gerund
                r'\b(want|need|hope|decide|plan|refuse|agree|promise)\s+to\s+\w+\b',  # verbs + infinitive
                r'\bit\'s\s+(easy|hard|difficult|important|necessary)\s+to\s+\w+\b'
            ],
            "articles": [
                r'\b(a|an)\s+\w+\b',  # indefinite articles
                r'\bthe\s+\w+\b',  # definite article
                r'\b(some|any|many|much|few|little|a\s+lot\s+of)\s+\w+\b'  # quantifiers
            ],
            "prepositions_time": [
                r'\b(in|on|at)\s+(the\s+)?(morning|afternoon|evening|night|weekend)\b',
                r'\b(in|on|at)\s+\d+\b',  # at 5, in 2021, on Monday
                r'\b(during|throughout|within|by|until|since|for)\s+\w+\b'
            ],
            "prepositions_place": [
                r'\b(in|on|at|under|over|behind|in\s+front\s+of|next\s+to|between|among)\s+\w+\b',
                r'\b(here|there|everywhere|somewhere|nowhere|anywhere)\b'
            ],
            "future_will": [
                r'\bwill\s+\w+\b',  # will + infinitive
                r'\bshall\s+\w+\b'
            ],
            "future_going_to": [
                r'\b(am|is|are)\s+going\s+to\s+\w+\b'  # going to + infinitive
            ],
            "basic_comparatives": [
                r'\b\w+er\s+than\b',  # adjective + er than
                r'\bmore\s+\w+\s+than\b',  # more + adjective than
                r'\bthe\s+\w+est\b',  # the + adjective + est
                r'\bthe\s+most\s+\w+\b',  # the most + adjective
                r'\b(as\s+\w+\s+as|not\s+as\s+\w+\s+as)\b'  # as...as comparisons
            ],
            "superlatives": [
                r'\bthe\s+(best|worst|most|least)\s+\w+\b',
                r'\bthe\s+\w+est\s+(in|of|among)\b'
            ],
            "past_simple": [
                r'\b(was|were)\b',  # be verbs in past
                r'\b\w+ed\b',  # regular past tense
                r'\b(went|came|saw|did|made|took|gave|got|had|said|told|thought|found|knew)\b'  # irregular verbs
            ],
            "present_simple": [
                r'\bit\s+is\s+\w+\b',  # it is + adjective/noun (like "it is amazing")
                r'\b(am|is|are)\s+\w+(?!ing)\b',  # be + not V-ing
                r'\b(do|does)\s+\w+\b',  # do/does + verb
                r'\b(work|works|live|lives|play|plays|eat|eats|speak|speaks|know|knows)\b'  # simple verbs
            ]
        }
        
        # Check each pattern in order (most specific first)
        for pattern_name, regexes in pattern_map.items():
            for regex in regexes:
                if re.search(regex, text, re.IGNORECASE):
                    if pattern_name not in patterns_found:
                        patterns_found.append(pattern_name)
                    break
        
        return patterns_found
    
    async def _generate_grammar_explanation(self, text: str, pattern: str, user_id: int, db: Session) -> Dict:
        """
        Generate intelligent grammar explanation with interactive quiz
        
        Args:
            text: Original text containing the pattern
            pattern: Grammar pattern to explain
            user_id: User ID for level adaptation
            db: Database session
            
        Returns:
            Dict with detailed explanation and quiz
        """
        try:
            # Get user level for adaptation
            user_level_info = self.grammar_service.calculate_user_level(user_id, db)
            user_level = user_level_info.get("user_level", {}).get("level", "A1")
            
            # Limit text length for API
            text_sample = text[:1000] + "..." if len(text) > 1000 else text
            
            prompt = f"""
You are an expert English teacher helping a {user_level} level Turkish student.

TASK: Analyze and explain the grammar pattern "{pattern}" found in this text for Turkish learners.

TEXT: "{text_sample}"

FIRST: PATTERN DETECTION
1. Find ALL instances of this grammar pattern in the text
2. Analyze how each instance is used
3. Note any variations or special cases

THEN PROVIDE DETAILED EXPLANATION:
1. PATTERN IDENTIFICATION: List all found instances with their complete sentences
2. STRUCTURE EXPLANATION: Explain the grammar rule and structure in simple terms
3. USAGE PURPOSE: Explain when and why this pattern is used
4. TEXT ANALYSIS: Analyze why this pattern was chosen in each instance
5. INTERACTIVE QUIZ: Create a translation exercise using a similar pattern
6. HIDDEN ANSWER: Provide the correct translation (to be revealed later)
7. LEARNING TIP: Give a practical tip for remembering this pattern

IMPORTANT:
- Focus on ACTUAL USAGE in the text
- Identify ALL instances of the pattern
- Explain each instance's purpose
- Explanations should be appropriate for {user_level} level
- Use Turkish for explanations but keep English examples
- Make quiz challenging but not too difficult
- Ensure quiz sentence uses the same pattern

OUTPUT FORMAT (JSON):
{{
    "pattern_name": "{pattern}",
    "pattern_display_name": "Display name in Turkish",
    "user_level": "{user_level}",
    "example_from_text": "ALL sentences from text using this pattern",
    "structure_rule": "grammar structure explanation in Turkish",
    "usage_purpose": "when and why to use this pattern (Turkish)",
    "text_analysis": "analysis of EACH instance in the text (Turkish)",
    "quiz_question": "English sentence for user to translate",
    "hidden_answer": "Turkish translation of quiz sentence",
    "learning_tip": "practical tip for remembering (Turkish)",
    "difficulty_level": "A1/A2/B1/B2/C1/C2"
}}

RULES:
- Find and analyze EVERY instance of the pattern
- Keep explanations clear and concise
- Use practical examples from the text
- Make quiz relevant to the pattern
- Ensure all explanations are in Turkish except English examples
- Adapt complexity to user level
"""
            
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                raise Exception("Empty response from AI")
            
            # Clean response and parse JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            result = json.loads(response_text)
            
            return {
                "success": True,
                "data": {
                    "pattern_name": result.get("pattern_name", pattern),
                    "pattern_display_name": result.get("pattern_display_name", pattern),
                    "user_level": result.get("user_level", user_level),
                    "example_from_text": result.get("example_from_text", ""),
                    "structure_rule": result.get("structure_rule", ""),
                    "usage_purpose": result.get("usage_purpose", ""),
                    "text_analysis": result.get("text_analysis", ""),
                    "quiz_question": result.get("quiz_question", ""),
                    "hidden_answer": result.get("hidden_answer", ""),
                    "learning_tip": result.get("learning_tip", ""),
                    "difficulty_level": self.grammar_service.get_pattern_difficulty_level(pattern)  # ✅ USE HIERARCHY!
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for pattern {pattern}: {str(e)}")
            return self._fallback_explanation(pattern, user_level, text)
            
        except Exception as e:
            logger.error(f"Error generating explanation for pattern {pattern}: {str(e)}")
            return self._fallback_explanation(pattern, user_level, text)
    
    def _fallback_explanation(self, pattern: str, user_level: str, text: str) -> Dict:
        """
        Fallback explanation when AI fails
        """
        return {
            "success": True,
            "data": {
                "pattern_name": pattern,
                "pattern_display_name": pattern.replace("_", " ").title(),
                "user_level": user_level,
                "example_from_text": "Metinden örnek bulunamadı",
                "structure_rule": f"{pattern} yapısının kuralları",
                "usage_purpose": f"{pattern} yapısının kullanım amaçları",
                "text_analysis": "Bu yapının metindeki kullanım analizi",
                "quiz_question": f"Practice sentence with {pattern}",
                "hidden_answer": "Türkçe çeviri",
                "learning_tip": f"{pattern} yapısını hatırlamak için ipucu",
                "difficulty_level": self.grammar_service.get_pattern_difficulty_level(pattern)  # ✅ USE HIERARCHY!
            }
        }
    
    async def mark_user_grammar_knowledge(self, user_id: int, pattern: str, status: str, db: Session) -> Dict:
        """
        Mark user's grammar knowledge status
        
        Args:
            user_id: User ID
            pattern: Grammar pattern key
            status: 'known' or 'practice'
            db: Database session
            
        Returns:
            Operation result
        """
        try:
            result = self.grammar_service.mark_grammar_status(user_id, pattern, status, db)
            
            if result.get("success"):
                # Recalculate user level after update
                updated_level = self.grammar_service.calculate_user_level(user_id, db)
                result["updated_level"] = updated_level
            
            return result
            
        except Exception as e:
            logger.error(f"Error marking grammar knowledge: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_grammar_dashboard(self, user_id: int, db: Session) -> Dict:
        """
        Get comprehensive grammar learning dashboard for user
        """
        try:
            overview = self.grammar_service.get_user_grammar_overview(user_id, db)
            level_info = self.grammar_service.calculate_user_level(user_id, db)
            
            return {
                "success": True,
                "user_level": level_info,
                "grammar_overview": overview,
                "learning_path": self._generate_learning_path(overview, level_info)
            }
            
        except Exception as e:
            logger.error(f"Error getting user dashboard: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_learning_path(self, overview: Dict, level_info: Dict) -> List[Dict]:
        """
        Generate personalized learning path for user
        """
        try:
            current_level = level_info.get("user_level", {}).get("level", "A1")
            learning_path = []
            
            # Find patterns to focus on next
            for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
                if level in overview.get("overview", {}):
                    level_data = overview["overview"][level]
                    missing = level_data.get("missing", [])
                    
                    if missing and len(missing) <= 3:  # Focus on levels with few missing patterns
                        for pattern in missing:
                            learning_path.append({
                                "pattern": pattern,
                                "level": level,
                                "priority": "high" if level == current_level else "medium",
                                "description": f"Learn {pattern.replace('_', ' ')} pattern"
                            })
                
                if len(learning_path) >= 5:  # Max 5 recommendations
                    break
            
            return learning_path
            
        except Exception as e:
            logger.error(f"Error generating learning path: {str(e)}")
            return [] 