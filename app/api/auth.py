from urllib.parse import urlencode

from fastapi import APIRouter, Request, HTTPException, Response
import logging
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
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
async def auth_callback(request: Request):
    """Google OAuth 리디렉션 처리 후 액세스 토큰 반환"""
    FRONTEND_URL = getattr(request.state, "client_origin", None)
    if not FRONTEND_URL:
        raise HTTPException(status_code=400, detail="접근할 수 없는 URL")

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

        logger.info(f"사용자 로그인 성공: {userinfo['email']}")

        return JSONResponse({
            "success": True,
            "userinfo": userinfo
        })

    except HTTPException as e:
        logger.error(f"로그인 중 오류 발생: {str(e.detail)}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error={str(e.detail)}", status_code=302)

    except Exception as e:
        logger.exception("4. 로그인 실패 - 알 수 없는 오류 발생")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=로그인 실패", status_code=302)

@router.post("/set-cookie")
async def set_cookie(request: Request, response: Response):
    """액세스 토큰을 받아 쿠키를 설정하는 엔드포인트"""
    try:
        data = await request.json()
        userinfo = data.get("userinfo")

        if not userinfo or "email" not in userinfo:
            raise HTTPException(status_code=400, detail="유효하지 않은 사용자 정보")

        # 사용자 인증 처리
        await authenticate_user(userinfo, response)

        logger.info(f"쿠키 설정 완료: {userinfo['email']}")
        return JSONResponse({"message": "쿠키 설정 완료"})

    except Exception as e:
        logger.exception("쿠키 설정 중 오류 발생")
        raise HTTPException(status_code=500, detail="쿠키 설정 실패")

    
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