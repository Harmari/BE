import httpx

from urllib.parse import urlencode
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.user_schema import UserCreate,UserDB
from app.repository.user_repository import get_user_by_email, create_user
from app.core.security import create_access_token

# Google OAuth 관련 URL
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

async def get_google_auth_url() -> dict:
    """Google OAuth 인증 URL 생성"""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return {"auth_url": auth_url}

async def get_google_access_token(code: str) -> dict:
    """Google OAuth Access Token 요청"""
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_data = token_response.json()

    if "access_token" not in token_data:
        raise HTTPException(status_code=400, detail="access token을 얻을 수 없습니다.")

    return token_data

async def get_google_user_info(access_token: str) -> dict:
    """Google 사용자 정보 요청"""
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo = userinfo_response.json()

    return userinfo

async def authenticate_user(user_info: dict) -> dict:
    """OAuth 인증 후 기존 회원 여부 확인 및 로그인 처리"""
    email = user_info["email"]
    google_id = user_info["id"]
    name = user_info.get("name", "Unknown")
    profile_image = user_info.get("picture")

    # 기존 사용자 확인
    existing_user = await get_user_by_email(email)

    if existing_user:
        token = create_access_token({"sub": email})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": UserDB(**existing_user)
        }

    # 신규 사용자 자동 회원가입
    new_user_data = UserCreate(
        email=email,
        google_id=google_id,
        name=name,
        profile_image=profile_image,
        provider="google"
    )
    new_user = await create_user(new_user_data)

    token = create_access_token({"sub": email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user
    }
