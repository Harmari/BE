from pydantic import BaseModel
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
