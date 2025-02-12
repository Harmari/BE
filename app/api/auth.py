from fastapi import APIRouter, Request, HTTPException, Response
from app.services.auth_service import (
    get_google_auth_url,
    get_google_access_token,
    get_google_user_info,
    authenticate_user,
    refresh_access_token,
    logout_user
)

router = APIRouter()

@router.get("/login")
async def login():
    """Google OAuth 인증 URL 반환"""
    return await get_google_auth_url()

@router.get("/callback")
async def auth_callback(request: Request, response: Response):
    """Google OAuth 리디렉션 처리 후 로그인"""
    try:
        # 인증 코드 가져오기
        code = request.query_params.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="code를 가져오지 못하는중..")

        # 토큰 요청
        token_data = await get_google_access_token(code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="access token 못가져오는 중..")

        # 사용자 정보 요청
        userinfo = await get_google_user_info(access_token)

        # 로그인 성공 시 access_token과 refresh_token 반환
        return await authenticate_user(userinfo, response)
    
    # 예외처리(HTTPException, 그 외 예외)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    """Refresh Token을 이용한 Access Token 재발급"""
    return await refresh_access_token(request, response) 

@router.post("/logout")
async def logout(response: Response):
    """로그아웃 - Refresh Token 삭제"""
    return await logout_user(response)