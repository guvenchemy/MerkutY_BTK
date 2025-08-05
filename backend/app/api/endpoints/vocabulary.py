from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import tempfile
import os
from pydantic import BaseModel

from app.core.database import get_db
from app.services.vocabulary_service import VocabularyService
from app.models.user_vocabulary import User, Vocabulary, UserVocabulary

router = APIRouter()

# Pydantic models for request/response
class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    
    class Config:
        from_attributes = True

class VocabularyUploadResponse(BaseModel):
    message: str
    user_id: int
    words_processed: int
    words_added: int
    user_level: dict

class UserLevelResponse(BaseModel):
    user_id: int
    username: str
    level_info: dict

class AddWordRequest(BaseModel):
    username: str
    word: str
    action: str  # 'known', 'unknown', 'ignore'

@router.post("/user", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user or get existing user
    """
    try:
        user = VocabularyService.create_or_get_user(
            db=db, 
            username=user_data.username, 
            email=user_data.email
        )
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload", response_model=VocabularyUploadResponse)
async def upload_vocabulary(
    username: str = Form(...),
    file: UploadFile = File(...),
    language: str = Form("en"),
    db: Session = Depends(get_db)
):
    """
    Upload Excel file with user's known vocabulary
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
    
    try:
        # Create or get user
        user = VocabularyService.create_or_get_user(db=db, username=username)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Read vocabulary from Excel
            words = VocabularyService.read_excel_vocabulary(tmp_file_path)
            
            if not words:
                raise HTTPException(status_code=400, detail="No valid words found in the Excel file")
            
            # Add words to global vocabulary
            vocabularies = VocabularyService.add_words_to_vocabulary(
                db=db, 
                words=words, 
                language=language
            )
            
            # Assign vocabulary to user
            words_added = VocabularyService.assign_vocabulary_to_user(
                db=db, 
                user=user, 
                vocabularies=vocabularies
            )
            
            # Calculate user level
            user_level = VocabularyService.get_user_vocabulary_level(db=db, user=user)
            
            return VocabularyUploadResponse(
                message=f"Successfully processed {len(words)} words, added {words_added} new words to your vocabulary",
                user_id=user.id,
                words_processed=len(words),
                words_added=words_added,
                user_level=user_level
            )
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing vocabulary: {str(e)}")

@router.get("/level/{username}", response_model=UserLevelResponse)
async def get_user_level(username: str, db: Session = Depends(get_db)):
    """
    Get user's vocabulary level and statistics
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    level_info = VocabularyService.get_user_vocabulary_level(db=db, user=user)
    
    return UserLevelResponse(
        user_id=user.id,
        username=user.username,
        level_info=level_info
    )

@router.post("/add-word")
async def add_word_to_vocabulary(request: AddWordRequest, db: Session = Depends(get_db)):
    """
    Add a word to user's vocabulary based on action
    """
    try:
        # Get or create user
        user = db.query(User).filter(User.username == request.username).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User '{request.username}' not found")
        
        # Get or create vocabulary word
        vocab_word = db.query(Vocabulary).filter(Vocabulary.word == request.word.lower()).first()
        if not vocab_word:
            vocab_word = Vocabulary(word=request.word.lower(), language="en")
            db.add(vocab_word)
            db.flush()  # Get the ID
        
        # Check if user already has this word
        existing = db.query(UserVocabulary).filter(
            UserVocabulary.user_id == user.id,
            UserVocabulary.vocabulary_id == vocab_word.id
        ).first()
        
        if existing:
            # Update existing word status
            old_status = existing.status
            existing.status = request.action
            db.commit()
            return {
                "message": f"Word '{request.word}' status updated to '{request.action}'",
                "word": request.word,
                "action": request.action,
                "user_id": user.id,
                "updated": True,
                "is_new": False,
                "old_status": old_status
            }
        
        # Add new word to user vocabulary
        user_vocab = UserVocabulary(
            user_id=user.id,
            vocabulary_id=vocab_word.id,
            status=request.action  # 'known', 'unknown', 'ignore'
        )
        db.add(user_vocab)
        db.commit()
        
        return {
            "message": f"Word '{request.word}' added to vocabulary with status '{request.action}'",
            "word": request.word,
            "action": request.action,
            "user_id": user.id,
            "updated": False,
            "is_new": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add word: {str(e)}")

@router.get("/user-words/{username}")
async def get_user_words(username: str, db: Session = Depends(get_db)):
    """
    Get all vocabulary words for a specific user, organized by status
    """
    try:
        # Get user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")
        
        # Get all user vocabulary with word details
        user_words = db.query(UserVocabulary, Vocabulary).join(
            Vocabulary, UserVocabulary.vocabulary_id == Vocabulary.id
        ).filter(
            UserVocabulary.user_id == user.id
        ).order_by(UserVocabulary.created_at.desc()).all()
        
        # Format response
        words_list = []
        for user_vocab, vocab in user_words:
            # Handle potential None values for datetime fields
            created_at = user_vocab.created_at.isoformat() if user_vocab.created_at else ""
            updated_at = user_vocab.updated_at.isoformat() if user_vocab.updated_at else ""
            
            words_list.append({
                "id": user_vocab.id,
                "word": vocab.word,
                "translation": user_vocab.translation or "",  # Only use user's translation
                "status": user_vocab.status,
                "created_at": created_at,
                "updated_at": updated_at,
                "vocabulary_id": vocab.id,
                "difficulty_level": vocab.difficulty_level or 1
            })
        
        return words_list
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user words: {str(e)}")

@router.get("/users")
async def list_users(db: Session = Depends(get_db)):
    """
    List all users (for development/testing)
    """
    users = db.query(User).all()
    return [{"id": user.id, "username": user.username, "email": user.email} for user in users] 