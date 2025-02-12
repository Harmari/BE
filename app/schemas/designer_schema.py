from datetime import datetime
from typing import List

from pydantic import BaseModel

class Designer(BaseModel):
    id: str
    name: str
    region: str
    shop_address: str
    profile_image: str
    specialties: str
    face_consulting_fee: int
    non_face_consulting_fee: int
    introduction: str
    available_modes: str
    create_at: datetime
    update_at: datetime


class DesignerResponse(BaseModel):
    id: str
    name: str
    region: str
    shop_address: str
    profile_image: str
    specialties: str
    face_consulting_fee: int
    non_face_consulting_fee: int
    introduction: str
    available_modes: str

class DesignerListResponse(BaseModel):
    designer_list: List[DesignerResponse]
