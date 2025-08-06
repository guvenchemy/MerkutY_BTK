from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UrlContent(Base):
    __tablename__ = "url_content"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    title = Column(String(255))
    content = Column(Text, nullable=False)
    source_type = Column(String(50))  # 'wikipedia', 'medium', 'youtube'
    video_id = Column(String(20))  # YouTube için
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # CEFR Level Analysis (NEW)
    cefr_level = Column(String(5))  # A1, A2, B1, B2, C1, C2
    level_confidence = Column(Integer)  # 0-100%
    level_analysis = Column(Text)  # AI analysis details
    level_analyzed_at = Column(DateTime(timezone=True))  # When level was determined

class UnknownWord(Base):
    __tablename__ = "unknown_words"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word = Column(String(100), nullable=False)
    turkish_meaning = Column(Text)
    english_example = Column(Text)
    example_translation = Column(Text)
    status = Column(String(20), default="unknown")  # 'unknown', 'known', 'ignore'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="unknown_words") 