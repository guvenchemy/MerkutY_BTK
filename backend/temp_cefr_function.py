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
