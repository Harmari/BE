from fastapi import APIRouter, HTTPException
from app.services.reservationRead_service import get_reservations_list_by_user_id, get_reservation_by_id

router = APIRouter()

# 예약 리스트
@router.get("/list")
async def read_reservations(user_id: str):
    reservations = await get_reservations_list_by_user_id(user_id)
    if not reservations:
        raise HTTPException(status_code=404, detail="Reservations not found")
    return reservations


@router.get("/{reservation_id}")
async def read_reservation(reservation_id: str):
    reservations = await get_reservation_by_id(reservation_id)
    if not reservations:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservations

