from fastapi import HTTPException, Response, Request
from app.repository.user_repository import get_user_by_email, create_user, delete_user
from app.core.security import (
    create_access_token, 
    create_refresh_token, 
    verify_refresh_token, 
    set_auth_cookies, 
    clear_auth_cookies
)
from app.schemas.user_schema import UserCreateRequest, UserCreateResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def authenticate_user(userinfo: dict, response: Response) -> dict:
    """사용자 인증 및 토큰 발급"""
    try:
        email = userinfo["email"]
        
        # JWT 토큰 생성
        access_token = create_access_token(data={"sub": email})
        refresh_token = create_refresh_token(data={"sub": email})
        
        # 쿠키에 토큰 설정
        set_auth_cookies(response, access_token, refresh_token)
        
        # 로그 추가
        logger.info(f"Cookies set for user: {email}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        return {"success": True, "message": "로그인 성공"}
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인증 실패: {str(e)}")

async def refresh_access_token(request: Request, response: Response):
    """Refresh Token을 이용해 Access Token 재발급"""
    try:
        # Refresh Token 확인
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh Token이 없습니다.")
        
        payload = verify_refresh_token(refresh_token)
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token")

        access_token = create_access_token({"sub": email})

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="None",
        )

        return {"message": "Access Token이 갱신되었습니다."}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"토큰 갱신 실패: {str(e)}")

async def logout_user(request: Request, response: Response):
    """로그아웃 - Refresh Token 확인 후 삭제 및 쿠키 제거"""
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=400, detail="로그아웃 실패: Refresh Token이 없습니다.")

        response.delete_cookie(key="refresh_token")
        response.delete_cookie(key="access_token")

        return {"message": "로그아웃 완료"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그아웃 중 오류 발생: {str(e)}")

async def withdraw_user(email: str, response: Response):
    """회원 탈퇴 - 사용자 정보 삭제 및 쿠키 제거"""
    try:
        await delete_user(email)
        clear_auth_cookies(response)

        return {"message": "회원 탈퇴가 완료되었습니다."}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회원 탈퇴 실패: {str(e)}")