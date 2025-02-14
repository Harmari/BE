from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    """기본 사용자"""
    email: EmailStr
    google_id: str
    name: str
    profile_image: Optional[str] = None
    provider: str = "google"
    status: str = "active"

class UserCreateRequest(UserBase):
    """새로운 사용자 생성 요청"""
    created_at: str
    updated_at: str

class UserCreateResponse(UserBase):
    """새로운 사용자 생성 응답"""
    user_id: str

class UserDetailResponse(UserCreateResponse):
    """사용자 상세 조회 응답"""
    created_at: str
    updated_at: str
