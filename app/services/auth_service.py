import httpx

from fastapi import HTTPException, Response, Request

from app.core.config import settings
from app.schemas.user_schema import UserCreate, UserDB
from app.repository.user_repository import (
    get_user_by_email,
    create_user,
    update_refresh_token,
    delete_user
)
from app.core.security import (
    create_access_token, 
    create_refresh_token, 
    verify_refresh_token, 
    set_auth_cookies, 
    clear_auth_cookies,
)

# Google OAuth 관련 URL
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

async def get_google_auth_url() -> dict:
    """Google OAuth 인증 URL 생성"""
    try:
        # URL 파라미터 설정
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }

        # URL 생성
        auth_url = f"{GOOGLE_AUTH_URL}?{httpx.QueryParams(params)}"

        return {"auth_url": auth_url}
    
    # 예외처리(HTTPException)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"url 생성 실패 : {str(e)}")

async def get_google_access_token(code: str) -> dict:
    """Google OAuth Access Token 요청"""
    try:
        # 토큰 요청
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

        # 토큰 요청 실패시 예외처리
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"token 안가져옴: {response.text}")
        
        # 토큰 데이터 반환
        token_data = response.json()

        return token_data
    
    # 예외처리(HTTPException)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

async def get_google_user_info(access_token: str) -> dict:
    """Google 사용자 정보 요청"""
    try:
        # 사용자 정보 요청
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        # 사용자 정보 반환
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"사용자 정보 오류: {response.text}")
        return response.json()
    
    # 예외처리(HTTPException)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"api 요청 실패: {str(e)}")

async def authenticate_user(user_info: dict, response: Response) -> dict:
    """OAuth 인증 후 기존 회원 여부 확인 및 로그인 처리"""
    try:
        # 사용자 정보 추출
        email = user_info["email"]
        google_id = user_info["id"]
        name = user_info.get("name", "Unknown")
        profile_image = user_info.get("picture")

        # 기존 사용자 확인
        existing_user = await get_user_by_email(email)

        if existing_user:
            # 사용자의 상태 확인
            if existing_user.get("status") in ["inactive", "banned"]:
                raise HTTPException(status_code=403, detail="이용이 제한된 사용자입니다.")

            # 기존 Refresh Token 확인
            refresh_token = existing_user.get("refresh_token")
            if not refresh_token:
                refresh_token = create_refresh_token({"sub": email})
                await update_refresh_token(email, refresh_token)

            # JWT Access Token 발급
            access_token = create_access_token({"sub": email})

            return {"message": "로그인 성공"}
        
        # 신규 사용자 자동 회원가입 
        new_user_data = UserCreate(
            email=email,
            google_id=google_id,
            name=name,
            profile_image=profile_image,
            provider="google",
            status="active",
            refresh_token=None,  
            created_at=settings.CURRENT_DATETIME,
            updated_at=settings.CURRENT_DATETIME
        )

        # 사용자 등록
        new_user = await create_user(new_user_data)

        # JWT 토큰 발급
        access_token = create_access_token({"sub": email})
        refresh_token = create_refresh_token({"sub": email})

        # Refresh Token을 DB에 저장
        await update_refresh_token(email, refresh_token)

        # 쿠키에 토큰 설정
        set_auth_cookies(response, access_token, refresh_token) 

        return {"message": "회원가입 및 로그인 성공"}
    
    # 예외처리(HTTPException, 그 외 예외)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 인증 실패: {str(e)}")
    
async def refresh_access_token(request: Request, response: Response):
    """Refresh Token을 이용해 Access Token 재발급"""
    try:

        # Refresh Token 검증
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh Token이 없습니다.")
        
        # Refresh Token 검증
        payload = verify_refresh_token(refresh_token)

        # 사용자 이메일 추출
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token")

        # Refresh Token 검증
        access_token = create_access_token({"sub": email})

        # 쿠키에 토큰 설정
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="None",
        )

        return {"message": "Access Token이 갱신되었습니다."}

    # 예외처리(HTTPException, 그 외 예외)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"토큰 갱신 실패: {str(e)}")

async def logout_user(response: Response):
    """로그아웃 - Refresh Token 삭제 및 쿠키 제거"""
    try:
        clear_auth_cookies(response) 
        return {"message": "로그아웃 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그아웃 실패: {str(e)}")

async def withdraw_user(email: str, response: Response):
    """회원 탈퇴 - 사용자 정보 삭제 및 쿠키 제거"""
    try:
        # 사용자 삭제
        await delete_user(email)

        # 인증 쿠키 제거
        clear_auth_cookies(response)

        return {"message": "회원 탈퇴가 됐습니다."}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회원 탈퇴 실패: {str(e)}")
