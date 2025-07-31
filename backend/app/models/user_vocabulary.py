from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    vocabularies = relationship("UserVocabulary", back_populates="user")
    unknown_words = relationship("UnknownWord", back_populates="user")
    grammar_knowledge = relationship("UserGrammarKnowledge", back_populates="user")

class Vocabulary(Base):
    __tablename__ = "vocabularies"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(100), unique=True, index=True, nullable=False)
    language = Column(String(10), default="en", nullable=False)  # 'en', 'tr', etc.
    difficulty_level = Column(Integer, default=1)  # 1-10 difficulty scale
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to users who know this word
    users = relationship("UserVocabulary", back_populates="vocabulary")

class UserVocabulary(Base):
    __tablename__ = "user_vocabularies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vocabulary_id = Column(Integer, ForeignKey("vocabularies.id"), nullable=False)
    is_known = Column(Boolean, default=True)  # Does user know this word?
    status = Column(String(20), default="known")  # 'known', 'unknown', 'ignored', 'learning'
    confidence_level = Column(Integer, default=3)  # 1-5 confidence scale
    translation = Column(Text, nullable=True)  # User's preferred translation
    learned_at = Column(DateTime(timezone=True), nullable=True)  # When user learned this word
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="vocabularies")
    vocabulary = relationship("Vocabulary", back_populates="users")

# Additional model for storing transcripts to avoid re-processing
class ProcessedTranscript(Base):
    __tablename__ = "processed_transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(20), unique=True, index=True, nullable=False)  # YouTube video ID
    original_text = Column(Text, nullable=False)
    language = Column(String(10), default="en", nullable=False)
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Model for tracking user's grammar pattern knowledge
class UserGrammarKnowledge(Base):
    __tablename__ = "user_grammar_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    grammar_pattern = Column(String(100), nullable=False)  # e.g., "present_perfect", "passive_voice"
    status = Column(String(20), default="unknown")  # "known", "unknown", "ignored"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="grammar_knowledge")

# Grammar pattern definitions
class GrammarPattern(Base):
    __tablename__ = "grammar_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String(100), unique=True, nullable=False)
    pattern_key = Column(String(50), unique=True, nullable=False)  # Machine readable key
    description_turkish = Column(Text, nullable=False)  # Turkish explanation
    description_english = Column(Text, nullable=False)  # English explanation
    difficulty_level = Column(Integer, default=1)  # 1-10 scale
    category = Column(String(50), nullable=False)  # e.g., "tenses", "voice", "conditionals"
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 