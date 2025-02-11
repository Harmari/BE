from fastapi import APIRouter, Request, HTTPException
from app.services.auth_service import (
    get_google_auth_url,
    get_google_access_token,
    get_google_user_info,
    authenticate_user,
)

router = APIRouter()

@router.get("/login")
async def login():
    """Google OAuth 인증 URL 반환"""
    return await get_google_auth_url()

@router.get("/callback")
async def auth_callback(request: Request):
    """Google OAuth 리디렉션 처리 후 로그인"""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found")

    # 액세스 토큰 요청
    token_data = await get_google_access_token(code)
    access_token = token_data["access_token"]

    # 사용자 정보 가져오기
    userinfo = await get_google_user_info(access_token)

    # 기존 회원이면 로그인, 신규 회원은 차단
    auth_data = await authenticate_user(userinfo)

    return auth_data
