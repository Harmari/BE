from fastapi import APIRouter, HTTPException, status
from app.services.reservationRead_service import get_reservation_by_user_id

router = APIRouter()

@router.get("/get")
async def read_reservation(user_id: str):
    try:
        reservations = await get_reservation_by_user_id(user_id)
        return reservations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오류 : {str(e)}"
        )