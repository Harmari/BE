from fastapi import APIRouter, HTTPException
from app.services.reservation_service import get_reservation_by_email

router = APIRouter()

@router.get("/reservations")
async def read_reservation(email: str):
    reservation = await get_reservation_by_email(email)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation