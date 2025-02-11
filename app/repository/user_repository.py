from app.db.session import get_database
from app.schemas.user_schema import UserCreate, UserDB
from app.core.config import settings

async def get_user_by_email(email: str):
    """이메일로 기존 사용자 조회"""
    db = get_database()
    users_collection = db["users"]
    return await users_collection.find_one({"email": email})

async def create_user(user_data: UserCreate) -> UserDB:
    """새로운 사용자 등록"""
    db = get_database()
    users_collection = db["users"]

    user_dict = user_data.model_dump()
    user_dict["provider"] = "google"
    user_dict["created_at"] = settings.CURRENT_DATETIME
    user_dict["updated_at"] = settings.CURRENT_DATETIME

    result = await users_collection.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id) 
    user_dict.pop("_id", None) 

    return UserDB(**user_dict) 
