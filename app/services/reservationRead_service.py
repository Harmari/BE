from typing import Optional, List
from app.schemas.reservationRead_schema import Reservation
from app.db.session import get_database
from bson import ObjectId
# 데이터베이스 가져오기
database = get_database()
collection = database["reservations"]
