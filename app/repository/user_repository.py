from fastapi import HTTPException

from app.db.session import get_database
from app.schemas.user_schema import UserCreate, UserDB
from app.core.config import settings

async def get_user_by_email(email: str):
    """이메일로 기존 사용자 조회"""
    db = get_database()

    # 사용자 정보 조회
    users_collection = db["users"]
    user = await users_collection.find_one({"email": email})

    # 몽고디비 id 문자열 변환
    if user:
        user["id"] = str(user["_id"])  
        user.pop("_id", None)  
    return user

async def create_user(user_data: UserCreate) -> UserDB:
    """새로운 사용자 등록"""
    db = get_database()
    
    # 사용자 정보 저장을 위한 컬렉션
    users_collection = db["users"]

    # 사용자 정보 저장
    user_dict = user_data.model_dump()
    user_dict["provider"] = "google"
    user_dict["created_at"] = settings.CURRENT_DATETIME
    user_dict["updated_at"] = settings.CURRENT_DATETIME
    user_dict["refresh_token"] = None
    user_dict["status"] = "active"

    result = await users_collection.insert_one(user_dict)

    # 몽고디비 id 문자열 변환
    user_dict["id"] = str(result.inserted_id)  
    user_dict.pop("_id", None)

    return UserDB(**user_dict)

async def update_refresh_token(email: str, refresh_token: str):
    """사용자의 refresh_token 업데이트"""
    db = get_database()
    
    # 사용자 정보 저장을 위한 컬렉션
    users_collection = db["users"]

    # 사용자의 상태 확인
    user = await users_collection.find_one({"email": email})
    
    # 사용자가 없을 경우 예외처리
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 사용자의 상태가 active가 아닐 경우 예외처리
    if user["status"] != "active":
        raise HTTPException(status_code=403, detail="이용이 제한된 사용자입니다.")

    # 사용자의 refresh_token 업데이트
    update_result = await users_collection.update_one(
        {"email": email},
        {"$set": {"refresh_token": refresh_token, "updated_at": settings.CURRENT_DATETIME}}
    )

    # 업데이트 실패시 예외처리
    if update_result.modified_count == 0:
        raise ValueError("사용자 refresh_token 업데이트 실패")