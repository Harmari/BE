from fastapi import APIRouter, Request, HTTPException, Depends
from app.core.security import get_current_user
from app.repository.user_repository import get_user_by_email

router = APIRouter()

@router.get("/me")
async def get_logged_in_user(request: Request, current_user: dict = Depends(get_current_user)): 
    """현재 로그인한 사용자 정보 조회"""
    return {"user": current_user}

@router.get("/{email}")
async def get_user_info(email: str):
    """이메일로 특정 사용자 정보 조회"""
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user