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

async def authenticate_user(user_info: dict, response: Response) -> dict:
    """OAuth 인증 후 기존 회원 여부 확인 및 로그인 처리"""
    email = user_info["email"]
    print("사용자 생성 요청: ", user_info)

    try:
        existing_user = await get_user_by_email(email)
    except HTTPException as e:
        existing_user = None

    if existing_user:
        if existing_user.status in ["inactive", "banned"]:
            raise HTTPException(status_code=403, detail="사용이 제한된 사용자")

        refresh_token = create_refresh_token({"sub": email})
        access_token = create_access_token({"sub": email})

        set_auth_cookies(response, access_token, refresh_token)

        return {"message": "로그인 성공"}

    # 새로운 사용자 등록
    new_user_data = UserCreateRequest(
        email=email,
        google_id=user_info["id"],
        name=user_info.get("name", "Unknown"),
        profile_image=user_info.get("picture"),
        provider="google",
        status="active",
        created_at=settings.CURRENT_DATETIME,
        updated_at=settings.CURRENT_DATETIME
    )

    new_user = await create_user(new_user_data)

    refresh_token = create_refresh_token({"sub": email})
    access_token = create_access_token({"sub": email})

    set_auth_cookies(response, access_token, refresh_token)

    return {"message": "회원가입 성공", "user": new_user}

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