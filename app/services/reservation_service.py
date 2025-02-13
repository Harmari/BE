import logging
from typing import List, Optional
from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta

from bson import ObjectId

from app.schemas.reservation_schema import DayList, ReservationListRequest, ReservationListResponse, \
    ReservationCreateResponse, ReservationCreateRequest, ReservationDetail, ReservationSimple, GoogleMeetLinkResponse
from app.db.session import get_database

db = get_database()
collection = db["reservations"]

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

    reservations_cursor = collection.find({
        "designer_id": designer_obj_id,
        "reservation_date_time": {"$gte": now_str, "$lte": three_months_ahead_str}
    })

    reservations = await reservations_cursor.to_list(length=None)
    logger.info(f"해당 디자이너에 대한 예약리스트 조회 완료: {len(reservations)} 건")

    # 결과를 담아보자
    result = []
    for reservation in reservations:
        res_dt_str = reservation.get("reservation_date_time", "")
        day_item = DayList(
            reservation_date_time=res_dt_str,
            consulting_fee=reservation.get("consulting_fee", 0),
            mode=reservation.get("mode", ""),
            status=reservation.get("status", "")
        )
        result.append(day_item)

    response = ReservationListResponse(designer_id=request.designer_id, reservation_list=result)
    return response


async def reservation_create_service(request: ReservationCreateRequest) -> ReservationCreateResponse:
    dt_str = request.reservation_date_time.strip()
    now_kst = datetime.now(kst)

    # 실제 존재할 수 있는 일자인지 검증
    try:
        dt_obj = datetime.strptime(dt_str, "%Y%m%d%H%M")
    except Exception as e:
        logger.error(f"reservation_date_time 파싱 오류: {dt_str} - {e}")
        raise ValueError("reservation_date_time 형식이 올바르지 않습니다.")

    # 예약 시간이 현재 이후인지
    if dt_obj <= now_kst:
        logger.error(f"예약 시간이 현재보다 이전입니다: {dt_str}")
        raise ValueError("예약 시간은 현재 시간 이후여야 합니다.")

    # 예약은 최대 3개월 이내로 제한
    if dt_obj > now_kst + relativedelta(months=3):
        logger.error(f"예약 시간이 3개월 이상 미래입니다: {dt_str}")
        raise ValueError("예약은 3개월 이내로 가능합니다.")

    # 30분 단위 인지 체크
    minute_part = dt_str[-2:]
    if minute_part not in ("00", "30"):
        logger.error(f"reservation_date_time 분 단위 오류: {dt_str}")
        raise ValueError("reservation_date_time의 분은 반드시 '00' 또는 '30'이어야 합니다.")

    # 시간 범위 체크 10:00 ~ 20:00
    try:
        hour_int = int(dt_str[8:10])
        minute_int = int(dt_str[10:12])
    except Exception as e:
        logger.error(f"시간 부분 파싱 오류: {dt_str} - {e}")
        raise ValueError("reservation_date_time의 시간 부분이 올바르지 않습니다.")

    if hour_int < 10 or hour_int > 20:
        logger.error(f"예약 가능한 시간 범위 오류: {dt_str}")
        raise ValueError("예약 시간은 10시부터 20시 사이여야 합니다.")
    # 오후 20시인 경우, 분이 반드시 00
    if hour_int == 20 and minute_int != 0:
        logger.error(f"예약 시간 오류 (20시까지만 허용): {dt_str}")
        raise ValueError("예약 시간은 20시까지만 가능합니다.")

    # consulting_fee 정수형 변환
    try:
        fee = int(request.consulting_fee)
    except Exception as e:
        logger.error(f"Invalid consulting_fee: {request.consulting_fee} - {e}")
        raise ValueError("consulting_fee는 정수 값이어야 합니다.")

    # designer_id 체크
    try:
        designer_obj_id = ObjectId(request.designer_id)
    except Exception as e:
        logger.error(f"Invalid designer_id: {request.designer_id} - {e}")
        raise ValueError("designer_id 없어.")

    # 유효한 designer_id 인지 조회
    designer = await db["designers"].find_one({"_id": designer_obj_id})
    if not designer:
        logger.error(f"디자이너를 찾을 수 없음: {request.designer_id}")
        raise ValueError("해당 designer_id에 해당하는 디자이너가 존재하지 않습니다.")

    # user_id 체크
    try:
        user_obj_id = ObjectId(request.user_id)
    except Exception as e:
        logger.error(f"Invalid user_id: {request.user_id} - {e}")
        raise ValueError("user_id 없어.")

    # user_id 실존 조회
    user = await db["users"].find_one({"_id": user_obj_id})
    if not user:
        logger.error(f"사용자를 찾을 수 없음: {request.user_id}")
        raise ValueError("해당 user_id에 해당하는 사용자가 존재하지 않습니다.")

    # 대면 예약인 경우 google_meet_link는 비워져 있어야 함
    if request.mode == "대면":
        if request.google_meet_link.strip():
            logger.error(f"대면 예약 시 google_meet_link 오류: {request.google_meet_link}")
            raise ValueError("대면 예약인 경우 google_meet_link가 빈값이여야 함.")
    elif request.mode == "비대면":
        # 비대면 예약인 경우 google_meet_link는 필수
        if not request.google_meet_link.strip():
            logger.error("비대면 예약 시 google_meet_link 누락")
            raise ValueError("비대면 예약인 경우 google_meet_link가 필수입니다.")
    else:
        logger.error(f"예약 mode 오류: {request.mode}")
        raise ValueError("예약 mode는 '대면' 또는 '비대면'이어야 합니다.")

    # 동일예약 확인
    existing = await collection.find_one({
        "designer_id": designer_obj_id,
        "reservation_date_time": dt_str
    })
    if existing:
        logger.error(f"동일 예약 존재: {dt_str}")
        raise ValueError("해당 일시에 이미 예약이 존재합니다.")

    reservation_doc = {
        "designer_id": designer_obj_id,
        "user_id": user_obj_id,
        "reservation_date_time": dt_str,
        "consulting_fee": fee,
        "google_meet_link": request.google_meet_link.strip() if request.google_meet_link.strip() else None,
        "mode": request.mode,
        "status": "예약완료",
        "create_at": settings.CURRENT_DATETIME,
        "update_at": settings.CURRENT_DATETIME
    }

    # 드디어 들어가는 데이터 1줄
    insert_result = await collection.insert_one(reservation_doc)
    logger.info(f"Reservation created with id: {insert_result.inserted_id}")

    response = ReservationCreateResponse(
        designer_id=request.designer_id,
        user_id=request.user_id,
        reservation_date_time=dt_str,
        google_meet_link=request.google_meet_link,
        mode=request.mode,
        status="예약완료"
    )
    return response



async def get_reservations_list_by_user_id(user_id: str) -> List[ReservationSimple]:
    # 사용자 ID로 예약 리스트 조회
    reservations_cursor = collection.find({"user_id": ObjectId(user_id)}).sort("reservation_date_time", -1)
    reservations = await reservations_cursor.to_list(length=None)

    return [
        ReservationSimple(
            **{
                **reservation,
                "id": str(reservation["_id"]),
                "user_id": str(reservation["user_id"]),
                "designer_id": str(reservation["designer_id"]),
            }
        )
        for reservation in reservations
    ]


async def get_reservation_by_id(reservation_id: str) -> Optional[ReservationDetail]:
    # 아이디 기준으로 예약 정보 조회
    reservation = await collection.find_one({"_id": ObjectId(reservation_id)})

    if reservation:
        return ReservationDetail(
            **{
                **reservation,
                "id": str(reservation["_id"]),
                "user_id": str(reservation["user_id"]),
                "designer_id": str(reservation["designer_id"]),
            }
        )
    

async def update_reservation_status(reservation_id: str) -> Optional[ReservationDetail]:
    # 예약 ID로 예약 정보 조회
    reservation = await collection.find_one({"_id": ObjectId(reservation_id)})

    if not reservation:
        return None
    
    new_status = "예약취소" 
    # 상태 업데이트
    await collection.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"status": new_status}}
    )

    # 업데이트된 예약 정보 반환
    updated_reservation = await collection.find_one({"_id": ObjectId(reservation_id)})
    return ReservationDetail(
        **{
            **updated_reservation,
            "id": str(updated_reservation["_id"]),
            "user_id": str(updated_reservation["user_id"]),
            "designer_id": str(updated_reservation["designer_id"]),
        }
    )


async def generate_google_meet_link_service(reservation_id: str) -> GoogleMeetLinkResponse:
    reservation = await collection.find_one({"_id": ObjectId(reservation_id)})
    if not reservation:
        raise ValueError("Reservation not found")
    
    if reservation["mode"] != "비대면":
        raise ValueError("This user is not remote mode - not allowed to get google meet link")
    
    # 구글 밋 링크 생성 (목 데이터 사용)
    google_meet_link = "https://meet.google.com/mockdata"
    
    # 데이터베이스에 링크 저장
    await collection.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"google_meet_link": google_meet_link}}
    )
    
    return GoogleMeetLinkResponse(google_meet_link=google_meet_link)