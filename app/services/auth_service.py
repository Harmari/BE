import httpx
from urllib.parse import urlencode
from fastapi import HTTPException
from app.core.config import settings
from app.db.session import get_database
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
    db = get_database()
    users_collection = db["users"]

    email = user_info["email"]
    existing_user = await users_collection.find_one({"email": email})

    if existing_user:
        # 기존 회원이면 JWT 발급 후 로그인
        token = create_access_token({"sub": email})
        return {"access_token": token, "token_type": "bearer", "user": existing_user}

    # 회원가입 불가 → 에러 반환
    raise HTTPException(status_code=403, detail="회원가입이 불가능한 계정입니다.")
