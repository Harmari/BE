from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Request, status

from app.schemas.designer_schema import DesignerListResponse, DesignerResponse
from app.services.designer_service import get_designer, get_designer_list

designer_router = APIRouter()

@designer_router.get("/", response_model=DesignerListResponse)
async def designer_list_endpoint(
                                region: Optional[List[str]] = Query(None),
                                available_modes: Optional[str] = Query(None),
                                min_consulting_fee: Optional[int] = Query(None),
                                max_consulting_fee: Optional[int] = Query(None)
    ):
    try:
        designer_list = await get_designer_list(region, available_modes, min_consulting_fee, max_consulting_fee)
        return designer_list
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오류 : {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오류 : {str(e)}"
        )
@designer_router.get("/{designer_id}", response_model=DesignerResponse)
async def designer_endpoint(designer_id: str):
    try:
        if not ObjectId.is_valid(designer_id):
            raise ValueError(f"디자이너 아이디가 올바르지 않습니다.: {designer_id}")

        designer = await get_designer(designer_id)
        return designer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오류 : {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오류 : {str(e)}"
        )