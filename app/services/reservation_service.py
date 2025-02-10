from typing import Optional, List
from app.schemas.reservation_schema import Reservation
from app.db.session import get_database
from bson import ObjectId
# 데이터베이스 가져오기
database = get_database()
collection = database["reservations"]

async def get_reservation_by_user_id(user_id: str) -> List[Reservation]:
    # 아이디 기준으로 예약 정보 조회
    reservations_cursor = collection.find({"user_id": ObjectId(user_id)})
    reservations = await reservations_cursor.to_list(length=None)

    # Convert each reservation to a Reservation object
    return [
        Reservation(
            **{
                **reservation,
                "id": str(reservation["_id"]),
                "user_id": str(reservation["user_id"]),
                "designer_id": str(reservation["designer_id"]),
            }
        )
        for reservation in reservations
    ]