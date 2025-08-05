from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserGrammarKnowledge(Base):
    __tablename__ = "user_grammar_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    grammar_rule = Column(String, nullable=False)  # e.g., "present_simple", "past_tense", etc.
    proficiency_level = Column(Integer, default=0)  # 0-5 scale
    examples_seen = Column(Text)  # JSON string of examples
    last_practiced = Column(DateTime, default=datetime.utcnow)
    times_practiced = Column(Integer, default=0)
    mastery_score = Column(Integer, default=0)  # 0-100
    is_mastered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 