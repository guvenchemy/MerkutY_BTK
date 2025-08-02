from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class TranscriptLibrary(Base):
    __tablename__ = "transcript_library"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(20), unique=True, index=True, nullable=False)
    video_url = Column(String(500), nullable=False)
    video_title = Column(String(500))
    channel_name = Column(String(200))
    duration = Column(Integer)  # seconds
    
    # Transcript data
    original_transcript = Column(Text, nullable=False)
    adapted_transcript = Column(Text)
    
    # Metadata
    language = Column(String(10), default='en')
    transcript_length = Column(Integer)
    adapted_length = Column(Integer)
    
    # User who first added this transcript
    added_by_user_id = Column(Integer, ForeignKey("users.id"))
    added_by_username = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Usage stats
    view_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    added_by = relationship("User", back_populates="added_transcripts")
    
    def __repr__(self):
        return f"<TranscriptLibrary(video_id='{self.video_id}', title='{self.video_title}')>" 