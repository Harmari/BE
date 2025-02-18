import httpx
from fastapi import HTTPException
from app.core.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

async def get_google_auth_url() -> dict:
    """Google OAuth 인증 URL 생성"""
    try:
        # Google OAuth 인증 URL 생성
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile https://www.googleapis.com/auth/calendar",
            "access_type": "offline",
            "prompt": "consent"
        }
        auth_url = f"{GOOGLE_AUTH_URL}?{httpx.QueryParams(params)}"
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"url 생성 실패 : {str(e)}")

async def get_google_access_token(code: str) -> dict:
    """Google OAuth Access Token 요청"""
    try:
        # Google OAuth Access Token 요청
        async with httpx.AsyncClient() as client:
            response = await client.post(
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
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Access Token을 가져올 수 없습니다: {response.text}")
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"api 요청 실패: {str(e)}")

async def get_google_user_info(access_token: str) -> dict:
    """Google 사용자 정보 요청"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"사용자 정보 오류: {response.text}")
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"사용자 요청 실패: {str(e)}")
