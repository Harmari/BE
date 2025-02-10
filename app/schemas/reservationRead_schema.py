from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Reservation(BaseModel):
    id: str
    user_id: str
    designer_id: str
    mode: str
    reservationDateTime: datetime
    consultingFee: int
    googleMeetLink: Optional[str]
    status: str
    createdAt: datetime
    updatedAt: datetime


