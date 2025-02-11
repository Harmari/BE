from fastapi import APIRouter, HTTPException, status, Request
from app.schemas.reservation_schema import (
    ReservationListResponse, ReservationListRequest, ReservationCreateResponse, ReservationCreateRequest, ReservationDetail, ReservationSimple
)
from app.services.reservation_service import (
    reservation_list_service, reservation_create_service, get_reservations_list_by_user_id, get_reservation_by_id
)
from typing import List

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

# 예약 리스트
@router.get("/get_list", response_model=List[ReservationSimple])
async def read_reservations(user_id: str):
    try:
        reservations = await get_reservations_list_by_user_id(user_id)
        if not reservations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
        return reservations
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

@router.get("/get_reservation", response_model=ReservationDetail)
async def read_reservation(reservation_id: str):
    try:
        reservations = await get_reservation_by_id(reservation_id)
        if not reservations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
        return reservations
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
