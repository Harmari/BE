from fastapi import HTTPException
from bson import ObjectId
from app.db.session import get_database
from app.schemas.user_schema import (
    UserCreateRequest, UserCreateResponse, UserDetailResponse
)
from app.core.config import settings

db = get_database()
users_collection = db["users"]

async def get_user_by_email(email: str) -> UserDetailResponse:
    """이메일로 기존 사용자 조회"""
    user = await users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return UserDetailResponse(
        user_id=str(user["_id"]),
        email=user["email"],
        google_id=user["google_id"],
        name=user["name"],
        profile_image=user.get("profile_image"),
        provider=user["provider"],
        status=user["status"],
        created_at=user["created_at"],
        updated_at=user["updated_at"]
    )

async def create_user(user_data: UserCreateRequest) -> UserCreateResponse:
    """새로운 사용자 등록"""
    user_dict = user_data.dict()
    user_dict["provider"] = "google"
    user_dict["created_at"] = settings.CURRENT_DATETIME
    user_dict["updated_at"] = settings.CURRENT_DATETIME
    user_dict["status"] = "active"

    result = await users_collection.insert_one(user_dict)

    return UserCreateResponse(
        user_id=str(result.inserted_id),
        **user_dict
    )

async def delete_user(email: str):
    """회원 탈퇴 기능 - 사용자의 데이터를 삭제"""
    user = await users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="사용자가 없습니다.")

    delete_result = await users_collection.delete_one({"email": email})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="회원 탈퇴에 실패하였습니다.")

    return {"message": "회원 탈퇴가 완료되었습니다."}