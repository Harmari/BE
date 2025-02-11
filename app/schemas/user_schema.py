from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.config import settings

class UserBase(BaseModel):
    """기본 사용자 모델"""
    email: EmailStr
    google_id: str
    name: str
    profile_image: Optional[str] = None
    provider: str = "google"
    status: str = "active"
    created_at: str = settings.CURRENT_DATETIME  
    updated_at: str = settings.CURRENT_DATETIME  

class UserCreate(UserBase):
    """새로운 사용자 생성 요청 모델"""
    pass

class UserDB(UserBase):
    """MongoDB에서 조회되는 사용자 모델"""
    id: Optional[str] = None 

    class Config:
        from_attributes = True
