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
    reservation_id: str
    designer_id: str
    user_id: str
    reservation_date_time: str
    consulting_fee: str
    google_meet_link: str
    mode: str
    status: str

class ReservationCreateResponse(BaseModel):
    user_id: str
    designer_id: str
    reservation_date_time: str
    google_meet_link: str
    mode: str
    status: str



class ReservationDetail(BaseModel):
    id: str
    user_id: str
    designer_id: str
    mode: str
    reservation_date_time: str
    consulting_fee: int
    google_meet_link: Optional[str]
    status: str
    create_at: str
    update_at: str

class ReservationSimple(BaseModel):
    id: str
    user_id: str
    designer_id: str
    mode: str
    reservation_date_time: str
    consulting_fee: int
    status: str


class GoogleMeetLinkResponse(BaseModel):
    google_meet_link: str
