from typing import Optional
from app.schemas.reservation_schema import Reservation
from app.db.session import get_database

# 데이터베이스 가져오기
database = get_database()
collection = database["test"]

async def get_reservation_by_email(email: str) -> Optional[Reservation]:
    # 이메일 기준으로 예약 정보 조회
    reservation_data = await collection.find_one({"customer.email": email})

    if reservation_data:
        # ObjectId를 문자열로 변환
        reservation_data["_id"] = str(reservation_data["_id"])
        return Reservation(**reservation_data)
    return None
