from fastapi import APIRouter, HTTPException
from app.services.reservation_service import get_reservation_by_user_id

router = APIRouter()

@router.get("/reservations")
async def read_reservation(user_id: str):
    reservations = await get_reservation_by_user_id(user_id)
    if not reservations:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservations