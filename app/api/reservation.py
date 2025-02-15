from fastapi import APIRouter, HTTPException, status, Request, Depends

from app.core.security import get_auth_user
from app.schemas.reservation_schema import (
    ReservationListResponse, ReservationListRequest, ReservationCreateResponse, ReservationCreateRequest, \
    ReservationDetail, ReservationSimple, GoogleMeetLinkResponse
)
from app.services.reservation_service import (
    reservation_list_service, reservation_create_service, get_reservations_list_by_user_id, get_reservation_by_id, \
    update_reservation_status, generate_google_meet_link_service, reservation_pay_ready_service
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
async def reservation_list_endpoint(request: ReservationCreateRequest, user : dict = Depends(get_auth_user)):
    try:
        reservation_list = await reservation_create_service(request, user)
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
@router.post("/get_list", response_model=List[ReservationSimple])
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

@router.post("/get_detail", response_model=ReservationDetail)
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

@router.patch("/cancel", response_model=ReservationDetail)
async def cancel_reservation_endpoint(reservation_id: str):
    try:
        updated_reservation = await update_reservation_status(reservation_id)
        if not updated_reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
        return updated_reservation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"오류 : {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오류 : {str(e)}"
        )
    
@router.patch("/generate_google_meet_link", response_model=GoogleMeetLinkResponse)
async def generate_google_meet_link(reservation_id: str):
    try:
        return await generate_google_meet_link_service(reservation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오류 : {str(e)}"
        )

@router.get("/reservation/pay_ready")
async def reservation_pay_ready_endpoint():
    try:
        result = await reservation_pay_ready_service()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))