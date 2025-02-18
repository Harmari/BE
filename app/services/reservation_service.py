import logging
from fastapi import Request
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pytz
from dateutil.relativedelta import relativedelta
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

from bson import ObjectId

from app.core.config import settings
from app.schemas.reservation_schema import DayList, ReservationListRequest, ReservationListResponse, \
    ReservationCreateResponse, ReservationCreateRequest, ReservationDetail, ReservationSimple, GoogleMeetLinkResponse
from app.db.session import get_database
from app.services.google_service import add_event_to_user_calendar, update_event_with_meet_link, delete_google_calendar_event

db = get_database()
collection = db["reservations"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_time_str = settings.CURRENT_DATETIME

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
        "reservation_date_time": {"$gte": now_str, "$lte": three_months_ahead_str},
        "del_yn": "N",
        "status": "예약완료"
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


async def reservation_create_service(request: ReservationCreateRequest, login_user: Dict) -> ReservationCreateResponse:
    dt_str = request.reservation_date_time.strip()
    now_kst = datetime.now(kst)

    # 날짜 형식 검증
    try:
        dt_obj = datetime.strptime(dt_str, "%Y%m%d%H%M")
        dt_obj = kst.localize(dt_obj)  # 시간대 정보 추가
    except Exception as e:
        logger.error(f"reservation_date_time 파싱 오류: {dt_str} - {e}")
        raise ValueError("reservation_date_time 형식이 올바르지 않습니다.")

    # 예약 시간이 현재시간+30분 이후여야 함
    if dt_obj <= now_kst + timedelta(minutes=30):
        logger.error(f"예약 시간이 현재보다 이전 : {dt_str}")
        raise ValueError("예약 시간은 현재 시간에서 최소 30분 이후여야 합니다.")

    # 예약은 최대 3개월 이내로 제한
    if dt_obj > now_kst + relativedelta(months=3):
        logger.error(f"예약 시간이 3개월 이상임 : {dt_str}")
        raise ValueError("예약은 3개월 이내로 가능합니다.")

    # 30분 단위 검증
    minute_part = dt_str[-2:]
    if minute_part not in ("00", "30"):
        logger.error(f"reservation_date_time 분 단위 오류: {dt_str}")
        raise ValueError("reservation_date_time의 분은 반드시 '00' 또는 '30'이어야 합니다.")

    # 시간 범위 체크 10:00 ~ 20:00 (20시인 경우 분은 00)
    try:
        hour_int = int(dt_str[8:10])
        minute_int = int(dt_str[10:12])
    except Exception as e:
        logger.error(f"시간 부분 파싱 오류: {dt_str} - {e}")
        raise ValueError("reservation_date_time의 시간 부분이 올바르지 않습니다.")

    if hour_int < 10 or hour_int > 20:
        logger.error(f"예약 가능한 시간 범위 오류: {dt_str}")
        raise ValueError("예약 시간은 10시부터 20시 사이여야 합니다.")
    if hour_int == 20 and minute_int != 0:
        logger.error(f"예약 시간 오류 (20시까지만 허용): {dt_str}")
        raise ValueError("예약 시간은 20시까지만 가능합니다.")

    # 예약 상태 검증
    valid_statuses = ["예약완료", "결제대기", "예약취소"]
    if request.status not in valid_statuses:
        logger.error(f"올바르지 않은 예약 상태: {request.status}")
        raise ValueError(f"status는 {valid_statuses} 중 하나여야 합니다.")

    # consulting_fee 정수형 변환
    try:
        fee = int(request.consulting_fee)
    except Exception as e:
        logger.error(f"Invalid consulting_fee: {request.consulting_fee} - {e}")
        raise ValueError("consulting_fee는 정수 값이어야 합니다.")

    try:
        designer_obj_id = ObjectId(request.designer_id)
    except Exception as e:
        logger.error(f"Invalid designer_id: {request.designer_id} - {e}")
        raise ValueError("designer_id가 올바르지 않습니다.")

    designer = await db["designers"].find_one({"_id": designer_obj_id})
    if not designer:
        logger.error(f"디자이너를 찾을 수 없음: {request.designer_id}")
        raise ValueError("해당 designer_id에 해당하는 디자이너가 존재하지 않습니다.")
    
    try:
        user_obj_id = ObjectId(request.user_id)
    except Exception as e:
        logger.error(f"Invalid user_id: {request.user_id} - {e}")
        raise ValueError("user_id가 올바르지 않습니다.")


    user = await db["users"].find_one({"_id": user_obj_id})
    if not user:
        logger.error(f"사용자를 찾을 수 없음: {request.user_id}")
        raise ValueError("해당 user_id에 해당하는 사용자가 존재하지 않습니다.")

    # 디자이너 정보 조회

    # 디자이너 정보 조회
    designer_name = designer.get("name")
    designer_introduction = designer.get("introduction")
    designer_region = designer.get("region")
    designer_specialist = designer.get("specialties")
    designer_shop_address = designer.get("shop_address")

    # 예약 데이터 업데이트/삽입 시 사용할 데이터 준비
    update_data = {
        "designer_id": designer_obj_id,
        "user_id": user_obj_id,
        "reservation_date_time": dt_str,
        "consulting_fee": fee,
        "google_meet_link": request.google_meet_link.strip() if request.google_meet_link.strip() else None,
        "mode": request.mode,
        "status": request.status,
        "update_at": current_time_str,
        "del_yn": "N"
    }

    if request.reservation_id:
        # reservation_id가 제공된 경우, 우선 임시예약인지 확인하면서 업데이트 시도
        result = await collection.find_one_and_update(
            {
                "_id": ObjectId(request.reservation_id),
                "status": "임시예약"
            },
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        if result:
            new_id = result["_id"]
        else:
            # 만약 해당 _id가 없거나 임시예약이 아니라면 새 예약을 생성
            update_data["create_at"] = current_time_str
            try:
                insert_result = await collection.insert_one(update_data)
            except DuplicateKeyError as e:
                logger.error(f"동일 예약 중복 에러: {dt_str} - {e}")
                raise ValueError("해당 일시에 이미 예약이 존재합니다.")
            new_id = insert_result.inserted_id
    else:
        # reservation_id가 제공되지 않은 경우, 중복 예약 여부 체크 후 새 예약 삽입
        existing = await collection.find_one({
            "designer_id": designer_obj_id,
            "reservation_date_time": dt_str,
        })
        if existing:
            logger.error(f"동일 예약 존재: {dt_str}")
            raise ValueError("해당 일시에 이미 예약이 존재합니다.")
        update_data["create_at"] = current_time_str
        try:
            insert_result = await collection.insert_one(update_data)
        except DuplicateKeyError as e:
            logger.error(f"동일 예약 중복 에러: {dt_str} - {e}")
            raise ValueError("해당 일시에 이미 예약이 존재합니다.")
        new_id = insert_result.inserted_id

    logger.info(f"Reservation created/updated with id: {new_id}")


    # 구글 캘린더에 이벤트 추가
    user_email = login_user.get("email")
    # user_email = "hsc0125@knou.ac.kr"
    logger.info(f"user_email::::::::::: {user_email}")

    event_id = None
    event_html_link = ""
    meet_link = ""

    if login_user:
        event_date = datetime.strptime(dt_str, "%Y%m%d%H%M")
        event_id, event_html_link, meet_link=await add_event_to_user_calendar(
            user_email,
            credentials=login_user.get("credentials"),
            event_date=event_date,
            designer_name=designer_name,
            designer_introduction=designer_introduction,
            designer_region=designer_region,
            designer_specialist=designer_specialist,
            designer_shop_address=designer_shop_address,
            mode=request.mode
        )

        if event_id is None or event_html_link is None or meet_link is None :
            raise ValueError("Google Calendar 이벤트 생성에 실패했습니다.")

        # 이벤트 ID를 데이터베이스에 저장
        await collection.update_one(
            {"_id": new_id},
            {
                "$set": {
                    "google_event_id": event_id,
                    "google_calendar_url": event_html_link,
                    "google_meet_link": meet_link
                }
            }
        )


    response = ReservationCreateResponse(
        reservation_id = str(new_id),
        designer_id=request.designer_id,
        user_id=request.user_id,
        reservation_date_time=dt_str,
        mode=request.mode,
        status=request.status,
        google_calendar_url=event_html_link,
        google_meet_link=meet_link
    )
    return response


async def get_reservations_list_by_user_id(user_id: str) -> List[ReservationSimple]:
    # 사용자 ID로 예약 리스트 조회
    reservations_cursor = collection.find({"user_id": ObjectId(user_id)}).sort("reservation_date_time", -1)
    reservations = await reservations_cursor.to_list(length=None)

    if not reservations:
        return []
    
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

    if not reservation:
        logger.error(f"예약을 찾을 수 없습니다. reservation_id: {reservation_id}")
        raise ValueError("예약을 찾을 수 없습니다.")
    

    if reservation:
        return ReservationDetail(
            **{
                **reservation,
                "id": str(reservation["_id"]),
                "user_id": str(reservation["user_id"]),
                "designer_id": str(reservation["designer_id"]),
            }
        )


async def update_reservation_status(reservation_id: str, user: dict) -> Optional[ReservationDetail]:
    # 예약 ID로 예약 정보 조회
    reservation = await collection.find_one({"_id": ObjectId(reservation_id)})

    if not reservation :
        logger.error(f"예약을 찾을 수 없습니다. reservation_id: {reservation_id}")
        raise ValueError("예약을 찾을 수 없습니다.")
    

    new_status = "예약취소"
    # 상태 업데이트
    await collection.update_one(
        {"_id": ObjectId(reservation_id)},
        {
            "$set": {
                "status": new_status,
                "update_at": current_time_str,
            },
            "$unset": {"google_meet_link": ""}
        }
    )
    google_event_id = reservation.get("google_event_id")
    if google_event_id:
        delete_google_calendar_event(google_event_id, credentials=user.get("credentials"))
        

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
        logger.error(f"예약을 찾을 수 없습니다. reservation_id: {reservation_id}")
        raise ValueError("예약을 찾을 수 없습니다.")
    
    if reservation["mode"] != "비대면":
        logger.error(f"비대면 모드가 아닙니다. reservation_id: {reservation_id}")
        raise ValueError("비대면 모드가 아닙니다. Google Meet링크를 생성할 수 없습니다.")

    google_meet_link = reservation.get("google_meet_link")
    
    return GoogleMeetLinkResponse(google_meet_link=google_meet_link)


async def reservation_pay_ready_service() -> dict:
    new_id = ObjectId()

    await collection.update_one(
        {"_id": new_id},
        {"$set": {
            "status": "임시예약",
            "create_at": current_time_str,
            "update_at": current_time_str,
        }},
        upsert=True
    )

    logger.info(f"Reservation pay_ready created with id: {new_id}")
    return {"_id": str(new_id)}


async def update_just_status(reservation_id: str, reservation_status: str) -> Optional[ReservationDetail]:
    reservation = await collection.find_one({"_id": ObjectId(reservation_id)})

    if not reservation:
        logger.error(f"예약을 찾을 수 없습니다. reservation_id: {reservation_id}")
        raise ValueError("예약을 찾을 수 없습니다.")

    # 예약 상태 검증 (유효한 상태 목록)
    valid_statuses = ["예약완료", "결제대기", "예약취소", "이용완료"]
    if reservation_status not in valid_statuses:
        logger.error(f"올바르지 않은 예약 상태: {reservation_status}")
        raise ValueError(f"status는 {valid_statuses} 중 하나여야 합니다.")

    # 상태 업데이트
    await collection.update_one(
        {"_id": ObjectId(reservation_id)},
        {
            "$set": {
                "status": reservation_status,
                "update_at": current_time_str,
            },
            "$unset": {"google_meet_link": ""}
        }
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
