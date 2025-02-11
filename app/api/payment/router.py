from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, List
from bson import ObjectId

from app.db.session import get_database
from app.services.kakao_pay import KakaoPayService
from ...schemas import payments_schemas

# 결제 API 라우터
router = APIRouter(prefix="/payments", tags=["payments"])

# 카카오페이 서비스 인스턴스 생성
kakao_pay_service = KakaoPayService()


# 결제 준비 API
@router.post("/ready", response_model=payments_schemas.PaymentReadyResponse)
async def ready_payment(
    payment: payments_schemas.PaymentCreate, 
    db: AsyncIOMotorClient = Depends(get_database) 
):
    """결제 준비 API"""
    try:
        # 결제 정보 생성
        payment_dict = payment.model_dump() 
        payment_dict.update({
            "created_at": datetime.utcnow(), # 생성 시간
            "updated_at": datetime.utcnow(), # 업데이트 시간
            "status": "ready" # 결제 상태
        })
        
        result = await db.payments.insert_one(payment_dict) # 결제 정보 생성
        payment_id = str(result.inserted_id) # 결제 ID

        # 카카오페이 결제 준비
        kakao_response = await kakao_pay_service.ready_to_pay(
            order_id=payment_id, # 주문 ID
            user_id=payment.user_id, # 사용자 ID
            item_name=f"예약 번호: {payment.reservation_id}", # 예약 번호
            quantity=1, # 예약 수량
            total_amount=payment.amount # 총 결제 금액
        )

        # 결제 정보 업데이트
        await db.payments.update_one(
            {"_id": result.inserted_id},
            {"$set": {
                "tid": kakao_response["tid"], # 카카오페이 결제 고유 번호
                "status": "ready" # 결제 상태
            }}
        )

        # 결제 준비 응답 반환
        return payments_schemas.PaymentReadyResponse(
            tid=kakao_response["tid"], # 카카오페이 결제 고유 번호
            next_redirect_pc_url=kakao_response["next_redirect_pc_url"], # 컴퓨터 리다이렉션 URL
            next_redirect_mobile_url=kakao_response["next_redirect_mobile_url"], # 모바일 리다이렉션 URL
            created_at=datetime.fromisoformat(kakao_response["created_at"]) # 생성 시간
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 결제 승인 API
@router.post("/approve", response_model=payments_schemas.PaymentResponse)
async def approve_payment(
    approve_data: payments_schemas.PaymentApproveRequest,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """결제 승인 API"""
    try:
        # ObjectId로 변환하여 조회
        payment = await db.payments.find_one({"_id": ObjectId(approve_data.order_id)})
        
        # 디버깅을 위한 로그 추가
        print(f"Looking for payment with order_id: {approve_data.order_id}")
        print(f"Found payment: {payment}")
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # 카카오페이 결제 승인 요청
        kakao_response = await kakao_pay_service.approve_payment(
            tid=approve_data.tid,
            pg_token=approve_data.pg_token,
            order_id=approve_data.order_id,
            user_id=payment["user_id"]
        )

        # 결제 정보 업데이트
        now = datetime.utcnow()
        update_data = {
            "status": "completed",
            "approved_at": now,
            "updated_at": now,
            "payment_type": "ONETIME",
            "transaction_id": kakao_response["aid"]
        }

        await db.payments.update_one(
            {"_id": ObjectId(approve_data.order_id)},
            {"$set": update_data}
        )

        # MongoDB의 _id를 id로 변환
        payment_response = {
            **payment,
            "id": str(payment["_id"]),  # _id를 id로 변환
        }
        del payment_response["_id"]  # _id 필드 제거
        
        payment_response.update(update_data)
        return payments_schemas.PaymentResponse(**payment_response)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# 결제 취소 API
@router.post("/cancel", response_model=payments_schemas.PaymentResponse)
async def cancel_payment(
    cancel_data: payments_schemas.PaymentCancelRequest,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """결제 취소 API"""
    try:
        # 결제 정보 조회
        payment = await db.payments.find_one({"_id": ObjectId(cancel_data.payment_id)})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
            
        # 이미 취소된 결제인지 확인
        if payment["status"] == "cancelled":
            raise HTTPException(status_code=400, detail="Payment already cancelled")
            
        # 취소 금액 설정 (None이면 전액 취소)
        cancel_amount = cancel_data.cancel_amount or payment["amount"]
        
        # 카카오페이 결제 취소 요청
        kakao_response = await kakao_pay_service.cancel_payment(
            tid=payment["tid"],
            cancel_amount=cancel_amount,
            cancel_reason=cancel_data.cancel_reason
        )
        
        # 결제 정보 업데이트
        now = datetime.utcnow()
        update_data = {
            "status": "cancelled",
            "cancel_reason": cancel_data.cancel_reason,
            "cancel_amount": cancel_amount,
            "updated_at": now
        }
        
        await db.payments.update_one(
            {"_id": ObjectId(cancel_data.payment_id)},
            {"$set": update_data}
        )
        
        # 응답 데이터 준비
        payment_response = {
            **payment,
            "id": str(payment["_id"]),
        }
        del payment_response["_id"]
        payment_response.update(update_data)
        
        return payments_schemas.PaymentResponse(**payment_response)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# 단일 결제 조회 API
@router.get("/{payment_id}", response_model=payments_schemas.PaymentResponse)
async def get_payment(
    payment_id: str,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """결제 상세 조회 API"""
    try:
        payment = await db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
            
        # 응답 데이터 준비
        payment_response = {
            **payment,
            "id": str(payment["_id"]),
        }
        del payment_response["_id"]
        
        return payments_schemas.PaymentResponse(**payment_response)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# 결제 목록 조회 API
@router.get("/", response_model=payments_schemas.PaymentListResponse)
async def list_payments(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    user_id: Optional[str] = Query(None, description="사용자 ID로 필터링"),
    status: Optional[str] = Query(None, description="결제 상태로 필터링"),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """결제 목록 조회 API"""
    try:
        # 필터 조건 설정
        filter_query = {}
        if user_id:
            filter_query["user_id"] = user_id
        if status:
            filter_query["status"] = status
            
        # 전체 결제 수 조회
        total = await db.payments.count_documents(filter_query)
        
        # 결제 목록 조회
        skip = (page - 1) * size
        cursor = db.payments.find(filter_query)
        cursor.sort("created_at", -1)  # 최신순 정렬
        cursor.skip(skip).limit(size)
        
        payments = []
        async for payment in cursor:
            payment_response = {
                **payment,
                "id": str(payment["_id"]),
            }
            del payment_response["_id"]
            payments.append(payment_response)
            
        return payments_schemas.PaymentListResponse(
            total=total,
            payments=payments,
            page=page,
            size=size
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 