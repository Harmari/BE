from typing import List, Optional

from bson import ObjectId

from app.core.config import settings
from app.db.session import get_database

DESIGNER_REGIONS = settings.DESIGNER_REGIONS

async def get_designers(region: Optional[List[str]], available_modes: Optional[str], min_consulting_fee: Optional[int], max_consulting_fee: Optional[int]):
    db = get_database()
    designer_collection = db["designers"]

    query = {}

    selected_regions = region if region else DESIGNER_REGIONS
    if not region or "서울 전체" in region:
        query["region"] = {"$in": DESIGNER_REGIONS}
    else:
        query["region"] = {"$in": region}

    if available_modes:
        query["available_modes"] = {"$regex": f"(^|, ){available_modes}(, |$)", "$options": "i"}
    
    price_filter = {}

    if min_consulting_fee is not None:
        price_filter["$gte"] = min_consulting_fee  # 최소 금액 설정

    if max_consulting_fee is not None:
        price_filter["$lte"] = max_consulting_fee  # 최대 금액 설정

    if available_modes == "대면":
        if price_filter:
            query["face_consulting_fee"] = price_filter  # 대면만 필터링

    elif available_modes == "비대면":
        if price_filter:
            query["non_face_consulting_fee"] = price_filter  # 비대면만 필터링

    else: 
        if price_filter:
            query["$or"] = [
                {"face_consulting_fee": price_filter},
                {"non_face_consulting_fee": price_filter},
            ]

    designers_cursor = designer_collection.find(query if query else {})
    return await designers_cursor.to_list(length=None)


async def get_designer_by_designer_id(designer_id: str):
    db = get_database()
    designer_collection = db["designers"]
    return await designer_collection.find({"_id": ObjectId(designer_id)}).to_list(length=None)