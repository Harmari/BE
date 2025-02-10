from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import List


class DayList(BaseModel):
    reservationDateTime : str
    consultingFee : int
    mode : str
    status : str


class ReservationListRequest(BaseModel):
    designer_id : str


class ReservationListResponse(BaseModel):
    designer_id : str
    reservation_list: List[DayList]


class ReservationCreateRequest(BaseModel):
    designer_id: str
    user_id: str
    reservationDateTime: str

    @field_validator("reservationDateTime")
    @classmethod
    def validate_reservation_datetime(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y%m%d%H%M")
        except ValueError:
            raise ValueError("reservationDateTime은 yyyymmddHHMM 형식이어야 합니다. 예: 202502100000")
        return v