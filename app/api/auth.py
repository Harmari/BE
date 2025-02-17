from urllib.parse import urlencode

from fastapi import APIRouter, Request, HTTPException, Response
import logging
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.services.auth_service import (
    get_google_auth_url,
    get_google_access_token,
    get_google_user_info,
)
from app.services.user_service import (
    authenticate_user,
    refresh_access_token,
    logout_user
)

logger = logging.getLogger(__name__)
router = APIRouter()



@router.get("/login")
async def login():
    """Google OAuth 인증 URL 반환"""
    return await get_google_auth_url()

@router.get("/callback")
async def auth_callback(request: Request, response: Response):
    try:
        code = request.query_params.get("code")
        if not code:
            logger.error("1. 로그인 실패 - 인증 코드 없음")
            raise HTTPException(status_code=400, detail="1. 로그인 실패")

        # Google에 토큰 요청
        token_data = await get_google_access_token(code)
        access_token = token_data.get("access_token")
        if not access_token:
            logger.error("2. 로그인 실패 - 액세스 토큰 없음")
            raise HTTPException(status_code=400, detail="2. 로그인 실패")

        # 사용자 정보 요청
        userinfo = await get_google_user_info(access_token)
        if not userinfo or "email" not in userinfo:
            logger.error("3. 로그인 실패 - 사용자 정보 없음")
            raise HTTPException(status_code=400, detail="3. 로그인 실패")

        # 요청의 Origin 헤더 확인
        origin = request.headers.get("origin")
        is_local = origin and "localhost" in origin
        frontend_url = "http://localhost:5173" if is_local else "https://harmari-fe.vercel.app"
        
        # RedirectResponse 생성
        redirect_response = RedirectResponse(
            url=f"{frontend_url}/designer-list",
            status_code=302
        )

        # 로그인 성공 시 쿠키 설정 (RedirectResponse에 직접 설정)
        await authenticate_user(userinfo, redirect_response)
        logger.info(f"사용자 로그인 성공: {userinfo['email']}")
        
        # 쿠키가 설정된 리다이렉트 응답 반환
        return redirect_response

    except HTTPException as e:
        error_response = RedirectResponse(
            url=f"{frontend_url}/login?error={str(e.detail)}", 
            status_code=302
        )
        return error_response

    except Exception as e:
        logger.exception("4. 로그인 실패 - 알 수 없는 오류 발생")
        error_response = RedirectResponse(
            url=f"{frontend_url}/login?error=로그인 실패", 
            status_code=302
        )
        return error_response
    
@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    """Refresh Token을 이용한 Access Token 재발급"""
    try:
        return await refresh_access_token(request, response)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "message": f"토큰 갱신 실패: {str(e)}"})


@router.post("/logout")
async def logout(request: Request, response: Response):
    """로그아웃 - Refresh Token 삭제"""
    try:
        return await logout_user(request, response)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "message": f"로그아웃 실패: {str(e)}"})