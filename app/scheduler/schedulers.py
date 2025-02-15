from datetime import datetime, timedelta
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings
from app.db.session import get_database

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = get_database()

async def delete_temp_reservations():

    # '임시예약' 상태이며 update_at이 현재로부터 1시간보다 이전인 예약 데이터 삭제처리
    logger.info("delete_temp_reservations start")

    # 현재 시간
    now = datetime.fromisoformat(settings.CURRENT_DATETIME)
    # 1시간 전 시간 계산
    threshold = now - timedelta(hours=1)
    threshold_str = threshold.isoformat()

    delete_filter = {
        "status": "임시예약",
        "update_at": {"$lt": threshold_str}
    }

    # 삭제 전 조건에 맞는 id조회
    matching_docs = await db["reservations"].find(delete_filter, {"_id": 1}).to_list(length=None)
    deleted_ids = [doc["_id"] for doc in matching_docs]
    logger.info(f"[{now.isoformat()}] 삭제할 _id들: {deleted_ids}")

    result = await db["reservations"].delete_many(delete_filter)
    logger.info(
        f"[{now.isoformat()}] {result.deleted_count}건 임시예약 데이터 삭제."
    )


async def delete_waiting_reservations():

    # '예약대기' 상태이며 update_at이 현재로부터 24시간 이전인 예약 데이터 삭제 처리

    logger.info("delete_waiting_reservations start")
    # 현재 시간
    now = datetime.fromisoformat(settings.CURRENT_DATETIME)
    # 24시간 전 시간 계산
    threshold = now - timedelta(hours=24)
    threshold_str = threshold.isoformat()

    delete_filter = {
        "status": "예약대기",
        "update_at": {"$lt": threshold_str},
        "del_yn": "N"
    }

    # 업데이트 전에 조건에 맞는 _id 조회
    matching_docs = await db["reservations"].find(delete_filter, {"_id": 1}).to_list(length=None)
    update_ids = [doc["_id"] for doc in matching_docs]
    logger.info(f"[{now.isoformat()}] 예약대기 _id: {update_ids}")

    # 조건에 맞는 문서들의 del_yn을 "Y"로 업데이트
    result = await db["reservations"].update_many(delete_filter, {"$set": {"del_yn": "Y"}})
    logger.info(f"[{now.isoformat()}] {result.modified_count}건 예약대기 데이터 삭제완료.")


# 스케줄러 설정
scheduler = AsyncIOScheduler()

# 스케줄 추가영역
scheduler.add_job(
    delete_temp_reservations,
    'interval',
    minutes=5,
    next_run_time=datetime.now()
)
scheduler.add_job(
    delete_waiting_reservations,
    'interval',
    minutes=5,
    next_run_time=datetime.now()
)

def start_scheduler():
    scheduler.start()
    logger.info("임시예약 삭제 Batch 시작.")
