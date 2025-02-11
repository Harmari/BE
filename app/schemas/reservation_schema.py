from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class DayList(BaseModel):
    reservation_date_time : str
    consulting_fee : int
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
    reservation_date_time: str
    consulting_fee: str
    google_meet_link: str
    mode: str

class ReservationCreateResponse(BaseModel):
    user_id: str
    designer_id: str
    reservation_date_time: str
    google_meet_link: str
    mode: str
    status: str


class Reservation(BaseModel):
    id: str
    user_id: str
    designer_id: str
    mode: str
    reservation_date_time: datetime
    consulting_fee: int
    google_meet_link: Optional[str]
    status: str
    create_at: datetime
    update_at: datetime
