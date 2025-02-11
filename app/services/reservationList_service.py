import logging
from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta

from bson import ObjectId

from app.schemas.reservationList_schema import DayList, ReservationListRequest, ReservationListResponse, ReservationCreateResponse, ReservationCreateRequest
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


async def reservation_create_service(request: ReservationCreateRequest) -> ReservationCreateResponse:

    dt_str = request.reservationDateTime.strip()

    # 실제 존재할 수 있는 일자인지 검증
    try:
        dt_obj = datetime.strptime(dt_str, "%Y%m%d%H%M")
    except Exception as e:
        logger.error(f"reservationDateTime 파싱 오류: {dt_str} - {e}")
        raise ValueError("reservationDateTime 형식이 올바르지 않습니다.")

    # 30분 단위 인지 체크
    minute_part = dt_str[-2:]
    if minute_part not in ("00", "30"):
        logger.error(f"reservationDateTime 분 단위 오류: {dt_str}")
        raise ValueError("reservationDateTime의 분은 반드시 '00' 또는 '30'이어야 합니다.")

    # 시간 범위 체크 10:00 ~ 20:00
    try:
        hour_int = int(dt_str[8:10])
        minute_int = int(dt_str[10:12])
    except Exception as e:
        logger.error(f"시간 부분 파싱 오류: {dt_str} - {e}")
        raise ValueError("reservationDateTime의 시간 부분이 올바르지 않습니다.")

    if hour_int < 10 or hour_int > 20:
        logger.error(f"예약 가능한 시간 범위 오류: {dt_str}")
        raise ValueError("예약 시간은 10시부터 20시 사이여야 합니다.")
    # 오후 20시인 경우, 분이 반드시 00
    if hour_int == 20 and minute_int != 0:
        logger.error(f"예약 시간 오류 (20시까지만 허용): {dt_str}")
        raise ValueError("예약 시간은 20시까지만 가능합니다.")

    # consultingFee 정수형 변환
    try:
        fee = int(request.consultingFee)
    except Exception as e:
        logger.error(f"Invalid consultingFee: {request.consultingFee} - {e}")
        raise ValueError("consultingFee는 정수 값이어야 합니다.")

    # designer_id, user_id 체크
    try:
        designer_obj_id = ObjectId(request.designer_id)
    except Exception as e:
        logger.error(f"Invalid designer_id: {request.designer_id} - {e}")
        raise ValueError("designer_id 없어.")
    try:
        user_obj_id = ObjectId(request.user_id)
    except Exception as e:
        logger.error(f"Invalid user_id: {request.user_id} - {e}")
        raise ValueError("user_id 없어.")

    # 대면 예약인 경우 googleMeetLink는 비워져 있어야 함
    if request.mode == "대면":
        if request.googleMeetLink.strip():
            logger.error(f"대면 예약 시 googleMeetLink 오류: {request.googleMeetLink}")
            raise ValueError("대면 예약인 경우 googleMeetLink가 빈값이여야 함.")
    elif request.mode == "비대면":
        # 비대면 예약인 경우 googleMeetLink는 필수
        if not request.googleMeetLink.strip():
            logger.error("비대면 예약 시 googleMeetLink 누락")
            raise ValueError("비대면 예약인 경우 googleMeetLink가 필수입니다.")
    else:
        logger.error(f"예약 mode 오류: {request.mode}")
        raise ValueError("예약 mode는 '대면' 또는 '비대면'이어야 합니다.")

    # 동일예약 확인
    existing = await db["reservations"].find_one({
        "designer_id": designer_obj_id,
        "reservationDateTime": dt_str
    })
    if existing:
        logger.error(f"동일 예약 존재: {dt_str}")
        raise ValueError("해당 일시에 이미 예약이 존재합니다.")

    # 오늘날짜 구해서 스트링해~
    now_kst = datetime.now(kst)
    created_at_str = now_kst.strftime("%Y%m%d%H%M")


    reservation_doc = {
        "designer_id": designer_obj_id,
        "user_id": user_obj_id,
        "reservationDateTime": dt_str,
        "consultingFee": fee,
        "googleMeetLink": request.googleMeetLink.strip() if request.googleMeetLink.strip() else None,
        "mode": request.mode,
        "status": "예약완료",
        "createAt": created_at_str,
        "updateAt": created_at_str
    }

    # 드디어 들어가는 데이터 1줄
    insert_result = await db["reservations"].insert_one(reservation_doc)
    logger.info(f"Reservation created with id: {insert_result.inserted_id}")

    response = ReservationCreateResponse(
        designer_id=request.designer_id,
        user_id=request.user_id,
        reservationDateTime=dt_str,
        googleMeetLink=request.googleMeetLink,
        mode=request.mode,
        status="예약완료"
    )
    return response
