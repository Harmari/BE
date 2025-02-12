import logging
from datetime import datetime

import pytz
from bson import ObjectId
from typing import List, Optional

from app.repository.designer_repository import get_designer_by_designer_id, get_designers
from app.schemas.designer_schema import DesignerListResponse, DesignerResponse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

kst = pytz.timezone("Asia/Seoul")

async def get_designer_list(region: Optional[List[str]], available_modes: Optional[str], min_consulting_fee: Optional[int], max_consulting_fee: Optional[int]) -> DesignerListResponse:
    
    designer_list = await get_designers(region, available_modes, min_consulting_fee, max_consulting_fee)
    logger.info(f"디자이너 리스트 조회 총: {len(designer_list)} 건")
    
    result = []
    for designer in designer_list:
        designer_result = DesignerResponse(
            id=str(designer.get("_id", "")),
            name=designer.get("name", ""),
            region=designer.get("region", ""),
            shop_address=designer.get("shop_address", ""),
            profile_image=designer.get("profile_image", ""),
            specialties=designer.get("specialties", ""),
            face_consulting_fee=designer.get("face_consulting_fee", 0),
            non_face_consulting_fee=designer.get("non_face_consulting_fee", 0),
            introduction=designer.get("introduction", ""),
            available_modes=designer.get("available_modes", "")
        )
        result.append(designer_result)

    response = DesignerListResponse(designer_list=result)
    return response

async def get_designer(designer_id: str) -> DesignerResponse:
        
    designer = await get_designer_by_designer_id(designer_id)
    if not designer:
        raise ValueError("디자이너 정보가 없습니다.")
    
    designer = designer[0]
    designer_result = DesignerResponse(
        id=str(designer.get("_id", "")),
        name=designer.get("name", ""),
        region=designer.get("region", ""),
        shop_address=designer.get("shop_address", ""),
        profile_image=designer.get("profile_image", ""),
        specialties=designer.get("specialties", ""),
        face_consulting_fee=designer.get("face_consulting_fee", 0),
        non_face_consulting_fee=designer.get("non_face_consulting_fee", 0),
        introduction=designer.get("introduction", ""),
        available_modes=designer.get("available_modes", "")
    )
    return designer_result