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
    consultingFee: str
    googleMeetLink: str
    mode: str

class ReservationCreateResponse(BaseModel):
    user_id: str
    designer_id: str
    reservationDateTime: str
    googleMeetLink: str
    mode: str
    status: str