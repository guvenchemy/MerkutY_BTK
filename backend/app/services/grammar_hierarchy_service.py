import logging
from typing import Dict, List, Set, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user_vocabulary import User, UserGrammarKnowledge, GrammarPattern

logger = logging.getLogger(__name__)


class GrammarHierarchyService:
    """
    Service for managing user grammar knowledge hierarchy
    Tracks what grammar patterns user knows and calculates intelligent user levels
    """
    
    # Grammar patterns organized by difficulty level
    GRAMMAR_HIERARCHY = {
        "A1": [
            "present_simple",
            "present_continuous", 
            "basic_questions",
            "basic_negatives",
            "articles",
            "prepositions_place"
        ],
        "A2": [
            "past_simple",
            "future_will",
            "future_going_to",
            "basic_comparatives",
            "basic_modals",
            "time_expressions",
            "prepositions_time",
            "question_formation"
        ],
        "B1": [
            "present_perfect",
            "present_perfect_continuous",
            "conditionals_type1",
            "passive_voice_simple",
            "relative_clauses_basic",
            "modal_verbs_basic",
            "gerunds_infinitives",
            "adjective_intensifiers"
        ],
        "B2": [
            "past_perfect",
            "past_continuous",
            "future_continuous",
            "conditionals_type2",
            "passive_voice_advanced",
            "passive_voice_perfect",
            "reported_speech",
            "modal_verbs_advanced",
            "relative_clauses_advanced",
            "superlatives"
        ],
        "C1": [
            "conditionals_type3",
            "subjunctive",
            "advanced_passive",
            "complex_sentences",
            "inversion"
        ],
        "C2": [
            "mixed_conditionals",
            "cleft_sentences",
            "ellipsis",
            "advanced_discourse_markers"
        ]
    }
    
    def calculate_user_level(self, user_id: int, db: Session) -> Dict:
        """
        Calculate user's level based on BOTH vocabulary AND grammar requirements
        
        New Level Requirements:
        - A1: 1,000 words + 100% A1 grammar
        - A2: 2,000 words + 100% A2 grammar  
        - B1: 5,000 words + 100% B1 grammar
        - B2: 7,500 words + 100% B2 grammar
        - C1: 10,000 words + 100% C1 grammar
        - C2: 10,000+ words + 100% C2 grammar
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Dict with detailed level and progress information
        """
        try:
            # Get current vocabulary and grammar knowledge
            vocab_count = self._get_vocabulary_count(user_id, db)
            grammar_knowledge = self._get_grammar_knowledge_by_level(user_id, db)
            
            # Define level requirements (minimum requirements to START each level)
            level_requirements = {
                "A1": {"vocab": 0, "grammar": []},  # Starting level
                "A2": {"vocab": 1000, "grammar": ["A1"]},  # Need A1 to start A2
                "B1": {"vocab": 2000, "grammar": ["A1", "A2"]},  # Need A1+A2 to start B1
                "B2": {"vocab": 5000, "grammar": ["A1", "A2", "B1"]},  # Need A1+A2+B1 to start B2
                "C1": {"vocab": 7500, "grammar": ["A1", "A2", "B1", "B2"]},  # Need A1+A2+B1+B2 to start C1
                "C2": {"vocab": 10000, "grammar": ["A1", "A2", "B1", "B2", "C1"]}  # Need A1+A2+B1+B2+C1 to start C2
            }
            
            # Determine current level (which level the user is currently working on)
            current_level = "A1"
            for level in ["C2", "C1", "B2", "B1", "A2", "A1"]:  # Check from highest to lowest
                req = level_requirements[level]
                
                # Check if user meets minimum requirements to START this level
                vocab_met = vocab_count >= req["vocab"]
                
                # Check grammar requirement (must know 100% of all required previous levels)
                grammar_met = True
                for required_level in req["grammar"]:
                    level_patterns = self.GRAMMAR_HIERARCHY.get(required_level, [])
                    if level_patterns:  # Only check if level has patterns
                        known_patterns = grammar_knowledge.get(required_level, [])
                        if len(known_patterns) < len(level_patterns):
                            grammar_met = False
                            break
                
                # If user meets requirements to START this level, they are currently in this level
                if vocab_met and grammar_met:
                    current_level = level
                    break
            
            # Calculate progress for current level
            current_level_patterns = self.GRAMMAR_HIERARCHY.get(current_level, [])
            current_level_known = len(grammar_knowledge.get(current_level, []))
            current_level_total = len(current_level_patterns)
            
            # For vocabulary, use the next level's requirement as target
            next_level = self._get_next_level(current_level)
            if next_level != current_level:
                next_req = level_requirements[next_level]
                vocab_target = next_req["vocab"]
                vocab_progress = min(100, (vocab_count / vocab_target) * 100)
            else:
                # Already at highest level
                vocab_progress = 100
                vocab_target = vocab_count
            
            # Grammar progress for current level
            if current_level_total > 0:
                grammar_progress = (current_level_known / current_level_total) * 100
            else:
                grammar_progress = 100  # No patterns for this level
                
            # Overall progress to next level
            next_level = self._get_next_level(current_level)
            if next_level != current_level:
                next_req = level_requirements[next_level]
                
                # Progress towards next level requirements
                vocab_progress_next = min(100, (vocab_count / next_req["vocab"]) * 100)
                
                # Grammar progress towards next level (all required levels)
                total_required_patterns = 0
                total_known_patterns = 0
                
                for required_level in next_req["grammar"]:
                    level_patterns = self.GRAMMAR_HIERARCHY.get(required_level, [])
                    total_required_patterns += len(level_patterns)
                    total_known_patterns += len(grammar_knowledge.get(required_level, []))
                
                if total_required_patterns > 0:
                    grammar_progress_next = (total_known_patterns / total_required_patterns) * 100
                else:
                    grammar_progress_next = 100
                    
                # Overall progress to next level (both requirements must be 100%)
                overall_progress = min(vocab_progress_next, grammar_progress_next)
            else:
                overall_progress = 100  # Already at highest level
                
            # Calculate vocabulary and grammar scores for compatibility
            vocab_score = self._get_vocabulary_score(user_id, db)
            grammar_score = self._get_grammar_score(user_id, db)
            
            return {
                "success": True,
                "user_level": {
                    "level": current_level,
                    "score": round((vocab_score + grammar_score) / 2, 1),  # Average for compatibility
                    "vocabulary_strength": round(vocab_score, 1),
                    "grammar_strength": round(grammar_score, 1),
                    "balance": self._analyze_balance(vocab_score, grammar_score),
                    
                    # New detailed progress tracking
                    "current_level_progress": {
                        "vocabulary_count": vocab_count,
                        "vocabulary_required": vocab_target,
                        "vocabulary_progress": round(vocab_progress, 1),
                        "vocabulary_remaining": max(0, vocab_target - vocab_count),
                        
                        "grammar_known": current_level_known,
                        "grammar_required": current_level_total,
                        "grammar_progress": round(grammar_progress, 1),
                        "grammar_remaining": max(0, current_level_total - current_level_known),
                        
                        "overall_progress": round(min(vocab_progress, grammar_progress), 1)
                    },
                    
                    "next_level_progress": {
                        "next_level": next_level,
                        "vocabulary_progress": round(vocab_progress_next if next_level != current_level else 100, 1),
                        "grammar_progress": round(grammar_progress_next if next_level != current_level else 100, 1),
                        "overall_progress": round(overall_progress, 1)
                    }
                },
                "scores": {
                    "vocabulary_score": vocab_score,
                    "grammar_score": grammar_score,
                    "total_score": round((vocab_score + grammar_score) / 2, 1)
                },
                "recommendations": self._get_level_recommendations(user_id, db)
            }
            
        except Exception as e:
            logger.error(f"Error calculating user level for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_vocabulary_score(self, user_id: int, db: Session) -> float:
        """Calculate vocabulary score (0-100) based on CEFR standards"""
        try:
            from app.models.user_vocabulary import UserVocabulary
            
            known_words = db.query(UserVocabulary).filter(
                UserVocabulary.user_id == user_id,
                UserVocabulary.status == "known"
            ).count()
            
            # CEFR-based vocabulary scoring
            if known_words == 0:
                return 0
            elif known_words <= 1000:  # A1 level
                return (known_words / 1000) * 16.67  # 0-16.67 points
            elif known_words <= 2000:  # A2 level  
                return 16.67 + ((known_words - 1000) / 1000) * 16.66  # 16.67-33.33 points
            elif known_words <= 5000:  # B1 level
                return 33.33 + ((known_words - 2000) / 3000) * 16.67  # 33.33-50.0 points
            elif known_words <= 7500:  # B2 level (updated requirement)
                return 50.0 + ((known_words - 5000) / 2500) * 16.67   # 50.0-66.67 points
            elif known_words <= 10000: # C1 level
                return 66.67 + ((known_words - 7500) / 2500) * 16.66  # 66.67-83.33 points
            else:  # C2 level (10k+)
                return 83.33 + min(16.67, ((known_words - 10000) / 5000) * 16.67)  # 83.33-100 points
                
        except Exception as e:
            logger.error(f"Error calculating vocabulary score: {str(e)}")
            return 0
    
    def _get_grammar_score(self, user_id: int, db: Session) -> float:
        """Calculate grammar score (0-100) based on known patterns"""
        try:
            known_grammar = db.query(UserGrammarKnowledge).filter(
                UserGrammarKnowledge.user_id == user_id,
                UserGrammarKnowledge.status == "known"
            ).all()
            
            known_patterns = [g.grammar_pattern for g in known_grammar]
            total_score = 0
            
            # Score based on hierarchy
            for level, patterns in self.GRAMMAR_HIERARCHY.items():
                level_score = {
                    "A1": 10, "A2": 15, "B1": 20, "B2": 25, "C1": 15, "C2": 15
                }[level]
                
                known_in_level = sum(1 for pattern in patterns if pattern in known_patterns)
                total_in_level = len(patterns)
                
                if total_in_level > 0:
                    level_percentage = known_in_level / total_in_level
                    total_score += level_score * level_percentage
            
            return min(100, total_score)
            
        except Exception as e:
            logger.error(f"Error calculating grammar score: {str(e)}")
            return 0
    
    def _score_to_level(self, total_score: float, vocab_score: float, grammar_score: float) -> Dict:
        """Convert scores to level designation with within-level progress"""
        
        # Define CEFR level ranges
        level_ranges = {
            "A1": (0, 16.67),
            "A2": (16.67, 33.33),
            "B1": (33.33, 50.0),
            "B2": (50.0, 66.67),
            "C1": (66.67, 83.33),
            "C2": (83.33, 100)
        }
        
        # Determine current level
        level = "A1"
        level_min = 0
        level_max = 16.67
        
        for level_name, (min_score, max_score) in level_ranges.items():
            if min_score <= total_score < max_score:
                level = level_name
                level_min = min_score
                level_max = max_score
                break
            elif total_score >= 83.33:  # Handle C2 edge case
                level = "C2"
                level_min = 83.33
                level_max = 100
                break
        
        # Calculate progress within current level (0-100%)
        level_range = level_max - level_min
        progress_in_level = ((total_score - level_min) / level_range) * 100
        progress_in_level = min(100, max(0, progress_in_level))  # Clamp to 0-100%
        
        return {
            "level": level,
            "score": round(total_score, 1),
            "level_progress": round(progress_in_level, 1),  # Progress within current level (0-100%)
            "vocabulary_strength": round(vocab_score, 1),
            "grammar_strength": round(grammar_score, 1),
            "balance": self._analyze_balance(vocab_score, grammar_score),
            "level_info": {
                "current_level": level,
                "progress_percentage": round(progress_in_level, 1),
                "next_level": self._get_next_level(level),
                "points_to_next": round(level_max - total_score, 2) if total_score < level_max else 0
            }
        }
    
    def _get_next_level(self, current_level: str) -> str:
        """Get the next CEFR level"""
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        try:
            current_index = level_order.index(current_level)
            if current_index < len(level_order) - 1:
                return level_order[current_index + 1]
            else:
                return "C2"  # Already at max level
        except ValueError:
            return "A2"  # Default fallback
    
    def _analyze_balance(self, vocab_score: float, grammar_score: float) -> str:
        """Analyze vocabulary vs grammar balance"""
        diff = abs(vocab_score - grammar_score)
        
        if diff < 10:
            return "balanced"
        elif vocab_score > grammar_score:
            return "vocabulary_strong"
        else:
            return "grammar_strong"
    
    def get_pattern_difficulty_level(self, pattern_name: str) -> str:
        """
        Get the correct difficulty level for a grammar pattern
        
        Args:
            pattern_name: Grammar pattern key (e.g., 'present_perfect_continuous')
            
        Returns:
            Difficulty level string (A1, A2, B1, B2, C1, C2) or 'unknown' if not found
        """
        for level, patterns in self.GRAMMAR_HIERARCHY.items():
            if pattern_name in patterns:
                return level
        
        # Don't assume unknown patterns - be honest that we don't know
        logger.warning(f"Pattern '{pattern_name}' not found in GRAMMAR_HIERARCHY, marking as unknown")
        return "unknown"
    
    def get_patterns_for_level(self, level: str) -> List[str]:
        """
        Get all grammar patterns for a specific level
        
        Args:
            level: CEFR level (A1, A2, B1, B2, C1, C2)
            
        Returns:
            List of pattern names for that level
        """
        return self.GRAMMAR_HIERARCHY.get(level, [])
    
    def _get_level_recommendations(self, user_id: int, db: Session) -> List[str]:
        """Get personalized learning recommendations"""
        try:
            known_grammar = db.query(UserGrammarKnowledge).filter(
                UserGrammarKnowledge.user_id == user_id,
                UserGrammarKnowledge.status == "known"
            ).all()
            
            known_patterns = set(g.grammar_pattern for g in known_grammar)
            recommendations = []
            
            # Find next patterns to learn
            for level, patterns in self.GRAMMAR_HIERARCHY.items():
                missing_patterns = [p for p in patterns if p not in known_patterns]
                if missing_patterns and len(missing_patterns) <= 2:
                    recommendations.append(f"Focus on {level} level: {', '.join(missing_patterns)}")
                    break
            
            return recommendations[:3]  # Max 3 recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return ["Continue practicing with diverse texts"]
    
    def get_unknown_grammar_patterns(self, user_id: int, detected_patterns: List[str], db: Session) -> List[str]:
        """
        Filter detected patterns to only include unknown ones
        
        Args:
            user_id: User ID
            detected_patterns: List of grammar patterns detected in text
            db: Database session
            
        Returns:
            List of grammar patterns user doesn't know yet
        """
        try:
            # Get user's known grammar patterns
            known_grammar = db.query(UserGrammarKnowledge).filter(
                UserGrammarKnowledge.user_id == user_id,
                UserGrammarKnowledge.status == "known"
            ).all()
            
            known_patterns = set(g.grammar_pattern for g in known_grammar)
            
            # Also check for "practice" status - include these too
            practice_grammar = db.query(UserGrammarKnowledge).filter(
                UserGrammarKnowledge.user_id == user_id,
                UserGrammarKnowledge.status == "practice"
            ).all()
            
            practice_patterns = set(g.grammar_pattern for g in practice_grammar)
            
            # Filter: unknown patterns + practice patterns
            unknown_patterns = [
                pattern for pattern in detected_patterns 
                if pattern not in known_patterns or pattern in practice_patterns
            ]
            
            return unknown_patterns
            
        except Exception as e:
            logger.error(f"Error filtering unknown patterns: {str(e)}")
            return detected_patterns  # Return all if error
    
    def mark_grammar_status(self, user_id: int, grammar_pattern: str, status: str, db: Session) -> Dict:
        """
        Mark grammar pattern status for user
        
        Args:
            user_id: User ID
            grammar_pattern: Grammar pattern key
            status: 'known' or 'practice'
            db: Database session
            
        Returns:
            Dict with operation result
        """
        try:
            existing = db.query(UserGrammarKnowledge).filter(
                UserGrammarKnowledge.user_id == user_id,
                UserGrammarKnowledge.grammar_pattern == grammar_pattern
            ).first()
            
            if existing:
                existing.status = status
                existing.updated_at = func.now()
            else:
                new_knowledge = UserGrammarKnowledge(
                    user_id=user_id,
                    grammar_pattern=grammar_pattern,
                    status=status
                )
                db.add(new_knowledge)
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Grammar pattern '{grammar_pattern}' marked as '{status}'"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking grammar status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_grammar_overview(self, user_id: int, db: Session) -> Dict:
        """Get comprehensive overview of user's grammar knowledge"""
        try:
            known_grammar = db.query(UserGrammarKnowledge).filter(
                UserGrammarKnowledge.user_id == user_id,
                UserGrammarKnowledge.status == "known"
            ).all()
            
            practice_grammar = db.query(UserGrammarKnowledge).filter(
                UserGrammarKnowledge.user_id == user_id,
                UserGrammarKnowledge.status == "practice"
            ).all()
            
            known_patterns = set(g.grammar_pattern for g in known_grammar)
            practice_patterns = set(g.grammar_pattern for g in practice_grammar)
            
            overview = {}
            for level, patterns in self.GRAMMAR_HIERARCHY.items():
                known_in_level = [p for p in patterns if p in known_patterns]
                practice_in_level = [p for p in patterns if p in practice_patterns]
                missing_in_level = [p for p in patterns if p not in known_patterns and p not in practice_patterns]
                
                overview[level] = {
                    "known": known_in_level,
                    "practicing": practice_in_level,
                    "missing": missing_in_level,
                    "completion_percentage": round((len(known_in_level) / len(patterns)) * 100, 1)
                }
            
            return {
                "success": True,
                "overview": overview,
                "total_known": len(known_patterns),
                "total_practicing": len(practice_patterns)
            }
            
        except Exception as e:
            logger.error(f"Error getting grammar overview: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            } 
    
    def _get_vocabulary_count(self, user_id: int, db: Session) -> int:
        """Get total count of known vocabulary words"""
        try:
            from app.models.user_vocabulary import UserVocabulary
            
            return db.query(UserVocabulary).filter(
                UserVocabulary.user_id == user_id,
                UserVocabulary.status == "known"
            ).count()
            
        except Exception as e:
            logger.error(f"Error getting vocabulary count: {str(e)}")
            return 0
    
    def _get_grammar_knowledge_by_level(self, user_id: int, db: Session) -> Dict[str, List[str]]:
        """Get grammar knowledge organized by level"""
        try:
            # UserGrammarKnowledge is already imported at the top
            known_grammar = db.query(UserGrammarKnowledge).filter(
                UserGrammarKnowledge.user_id == user_id,
                UserGrammarKnowledge.status == "known"
            ).all()
            
            known_patterns = [g.grammar_pattern for g in known_grammar]
            
            # Organize by level
            knowledge_by_level = {}
            for level, patterns in self.GRAMMAR_HIERARCHY.items():
                knowledge_by_level[level] = [p for p in patterns if p in known_patterns]
                
            return knowledge_by_level
            
        except Exception as e:
            logger.error(f"Error getting grammar knowledge by level: {str(e)}")
            return {} 