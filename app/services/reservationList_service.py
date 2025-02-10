import logging
from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta

from bson import ObjectId

from app.schemas.reservationList_schema import DayList, ReservationListRequest, ReservationListResponse
from app.db.session import get_database

db = get_database()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

kst = pytz.timezone("Asia/Seoul")

async def reservation_list_service(request: ReservationListRequest) -> ReservationListResponse:

    try:
        designer_obj_id = ObjectId(request.designer_id)
    except Exception as e:
        logger.error(f"Invalid designer_id: {request.designer_id}")
        raise ValueError("designer_id 없는뎅?")

    # 3개월 이내 예약 내역만 조회
    now_kst = datetime.now(kst)
    three_months_ahead_kst = now_kst + relativedelta(months=3)
    now_str = now_kst.strftime("%Y%m%d") + "0000"
    three_months_ahead_str = three_months_ahead_kst.strftime("%Y%m%d") + "2359"

    reservations_cursor = db["reservations"].find({
        "designer_id": designer_obj_id,
        "reservationDateTime": {"$gte": now_str, "$lte": three_months_ahead_str}
    })
    
    reservations = await reservations_cursor.to_list(length=None)
    logger.info(f"해당 디자이너에 대한 예약리스트 조회 완료: {len(reservations)} 건")

    # 결과를 담아보자
    result = []
    for reservation in reservations:
        res_dt_str = reservation.get("reservationDateTime", "")
        day_item = DayList(
            reservationDateTime=res_dt_str,
            consultingFee=reservation.get("consultingFee", 0),
            mode=reservation.get("mode", ""),
            status=reservation.get("status", "")
        )
        result.append(day_item)

    response = ReservationListResponse(designer_id=request.designer_id, reservation_list=result)
    return response





