from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user_vocabulary import User

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    phone_number: str

class UserLoginRequest(BaseModel):
    identifier: str  # Can be email or username
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    phone_number: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

@router.post("/register", response_model=UserResponse)
async def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user with username, email, password, and phone number.
    """
    try:
        user_data = AuthService.register_user(
            db=db,
            username=request.username,
            email=request.email,
            password=request.password,
            phone=request.phone_number
        )
        return user_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login user with email/username and password.
    Returns JWT access token.
    """
    try:
        login_data = AuthService.login_user(
            db=db,
            identifier=request.identifier,
            password=request.password
        )
        return login_data
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current user information from JWT token.
    """
    try:
        user = AuthService.get_current_user(db, credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "created_at": user.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")

@router.get("/user-id/{username}")
async def get_user_id_by_username(username: str, db: Session = Depends(get_db)):
    """
    Get user ID by username for development purposes.
    """
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"user_id": user.id, "username": user.username}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user ID: {str(e)}")

@router.post("/logout")
async def logout():
    """
    Logout user (client should discard the token).
    """
    return {"message": "Successfully logged out"}

@router.post("/validate-token")
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Validate if the provided JWT token is valid.
    """
    try:
        payload = AuthService.verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {"valid": True, "user_id": payload.get("user_id")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token validation failed: {str(e)}") 