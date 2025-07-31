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
    status = Column(String(20), default="known")  # 'known', 'unknown', 'ignore'
    confidence_level = Column(Integer, default=3)  # 1-5 confidence scale
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