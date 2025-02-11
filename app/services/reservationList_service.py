import logging
from datetime import datetime

from bson import ObjectId

from app.schemas.reservationList_schema import DayList, ReservationListRequest, ReservationListResponse
from app.db.session import get_database

db = get_database()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def reservation_list_service(request: ReservationListRequest) -> ReservationListResponse:

    try:
        designer_obj_id = ObjectId(request.designer_id)
    except Exception as e:
        logger.error(f"Invalid designer_id: {request.designer_id}")
        raise ValueError("designer_id 없는뎅?")

    reservations_cursor = db["reservations"].find({"designer_id": designer_obj_id})
    reservations = await reservations_cursor.to_list(length=None)
    logger.info(f"해당 디자이너에 대한 예약리스트 조회 완료: {len(reservations)}")

    result = []
    for reservation in reservations:
        res_dt = reservation.get("reservationDateTime")
        if res_dt:
            if isinstance(res_dt, datetime):
                dt_obj = res_dt
            else:
                try:
                    dt_obj = datetime.strptime(res_dt, "%Y-%m-%dT%H:%M:%SZ")
                except Exception as e:
                    logger.error(f"날짜 변환 오류: {res_dt} - {e}")
                    dt_obj = None
            if dt_obj:
                res_dt_str = dt_obj.strftime("%Y%m%d%H%M")
            else:
                res_dt_str = ""
        else:
            res_dt_str = ""

        day_item = DayList(
            reservationDateTime=res_dt_str,
            consultingFee=reservation.get("consultingFee", 0),
            mode=reservation.get("mode", ""),
            status=reservation.get("status", "")
        )
        result.append(day_item)

    response = ReservationListResponse(designer_id=request.designer_id, reservation_list=result)
    return response





