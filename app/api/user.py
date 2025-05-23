from fastapi import APIRouter, Request, HTTPException, Response
from app.core.security import verify_access_token
from app.services.user_service import withdraw_user
from app.repository.user_repository import get_user_by_email
from app.schemas.user_schema import UserDetailResponse

router = APIRouter()

@router.get("/me", response_model=UserDetailResponse)
async def get_logged_in_user(request: Request):
    """현재 로그인한 사용자 정보 조회 (쿠키 기반)"""
    # 쿠키에서 access_token 가져오기
    access_token = request.cookies.get("access_token")

    # 토큰이 없으면 401 오류 반환
    if not access_token:
        raise HTTPException(status_code=401, detail="토큰이 제공 안됨")

    # 토큰 검증
    try:
        payload = await verify_access_token(access_token)
        email = payload.get("sub")  # 토큰에서 이메일 추출
        if not email:
            raise HTTPException(status_code=401, detail="토큰이 문제 있음")

        # 사용자 정보 조회
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없다.")

        return user

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error : {str(e)}")

@router.get("/{email}", response_model=UserDetailResponse)
async def get_user_info(email: str):
    """이메일로 특정 사용자 정보 조회"""
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user

@router.delete("/me")
async def delete_logged_in_user(request: Request, response: Response):
    """현재 로그인한 사용자 삭제"""
    # 쿠키에서 access_token 가져오기
    access_token = request.cookies.get("access_token")

    # 토큰이 없으면 401 오류 반환
    if not access_token:
        raise HTTPException(status_code=401, detail="토큰이 제공되지 않았습니다.")

    # 토큰 검증
    try:
        payload = await verify_access_token(access_token)
        email = payload.get("sub")  # 토큰에서 이메일 추출
        if not email:
            raise HTTPException(status_code=401, detail="토큰이 문제 있음")

        # 사용자 삭제 요청을 서비스 계층을 통해 처리
        return await withdraw_user(email, response)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회원 탈퇴 실패: {str(e)}")