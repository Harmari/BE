from fastapi import APIRouter, HTTPException, status, Request
from app.schemas.reservationList_schema import (
    ReservationListResponse, ReservationListRequest, ReservationCreateResponse, ReservationCreateRequest
)
from app.services.reservationList_service import (
    reservation_list_service, reservation_create_service
)

router = APIRouter()

@router.post("/list", response_model=ReservationListResponse)
async def reservation_list_endpoint(request: ReservationListRequest):
    try:
        reservation_list = await reservation_list_service(request)
        return reservation_list
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

@router.post("/create", response_model=ReservationCreateResponse)
async def reservation_list_endpoint(request: ReservationCreateRequest):
    try:
        reservation_list = await reservation_create_service(request)
        return reservation_list
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