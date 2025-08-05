from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class WordDefinition(Base):
    """
    Global word cache table for storing AI-generated word explanations
    Shared across all users to avoid duplicate API calls
    """
    __tablename__ = "word_definitions"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(100), unique=True, index=True, nullable=False)
    turkish_meaning = Column(Text, nullable=True)
    english_example = Column(Text, nullable=True)
    example_translation = Column(Text, nullable=True)
    
    # Metadata
    language = Column(String(10), default="en", nullable=False)
    difficulty_level = Column(Integer, default=1)  # 1-10 scale
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        return {
            "word": self.word,
            "turkish_meaning": self.turkish_meaning,
            "english_example": self.english_example,
            "example_translation": self.example_translation,
            "difficulty_level": self.difficulty_level,
            "created_at": self.created_at
        } 