from fastapi import APIRouter, Request, HTTPException
from app.services.auth_service import (
    get_google_auth_url,
    get_google_access_token,
    get_google_user_info,
)

router = APIRouter()

@router.get("/login")
async def login():
    """Google OAuth 인증 URL 반환"""
    return await get_google_auth_url()

@router.get("/callback")
async def auth_callback(request: Request):
    """Google OAuth 리디렉션 처리 및 사용자 정보 반환"""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found")

    token_data = await get_google_access_token(code)
    access_token = token_data["access_token"]
    
    userinfo = await get_google_user_info(access_token)

    return {"user": userinfo}
