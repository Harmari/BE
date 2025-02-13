from fastapi import HTTPException

from app.db.session import get_database
from app.schemas.user_schema import UserCreate, UserDB
from app.core.config import settings

async def get_user_by_email(email: str):
    """이메일로 기존 사용자 조회"""
    db = get_database()
    users_collection = db["users"]
    user = await users_collection.find_one({"email": email})

    if user:
        user["id"] = str(user["_id"])  
        user.pop("_id", None)  
    return user

async def create_user(user_data: UserCreate) -> UserDB:
    """새로운 사용자 등록"""
    db = get_database()
    users_collection = db["users"]

    user_dict = user_data.model_dump()
    user_dict["provider"] = "google"
    user_dict["created_at"] = settings.CURRENT_DATETIME
    user_dict["updated_at"] = settings.CURRENT_DATETIME
    user_dict["status"] = "active"

    result = await users_collection.insert_one(user_dict)

    user_dict["id"] = str(result.inserted_id)  
    user_dict.pop("_id", None)

    return UserDB(**user_dict)

async def delete_user(email: str):
    """회원 탈퇴 기능 - 사용자의 데이터를 삭제"""
    db = get_database()
    users_collection = db["users"]

    user = await users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="사용자가 없습니다.")

    delete_result = await users_collection.delete_one({"email": email})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="회원 탈퇴에 실패하였습니다.")
