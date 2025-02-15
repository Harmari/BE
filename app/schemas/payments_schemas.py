from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# 결제 기본 스키마
class PaymentBase(BaseModel):
    reservation_id: str = Field(..., description="예약 ID")
    user_id: str = Field(..., description="사용자 ID")
    payment_method: str = Field(..., description="결제 방식 (카카오페이, 계좌이체)")
    amount: int = Field(..., description="결제 금액")
    status: str = Field(default="pending", description="결제 상태")

# 결제 생성 스키마
class PaymentCreate(PaymentBase):
    pass

# 결제 응답 스키마  
class PaymentResponse(PaymentBase):
    id: str = Field(..., description="Payment ObjectId")
    tid: Optional[str] = Field(None, description="카카오페이 결제 고유 번호")
    transaction_id: Optional[str] = Field(None, description="결제 거래 ID")
    payment_type: Optional[str] = Field(None, description="일반결제/정기결제")
    approved_at: Optional[datetime] = Field(None, description="결제 승인 시각")
    cancel_reason: Optional[str] = Field(None, description="결제 취소 사유")
    cancel_amount: Optional[int] = Field(None, description="취소 금액")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 결제 준비 응답 스키마
class PaymentReadyResponse(BaseModel):
    tid: str
    next_redirect_pc_url: str
    next_redirect_mobile_url: str
    created_at: datetime
    payment_id: str  # MongoDB의 _id를 저장할 필드 추가

# 결제 승인 요청 스키마
class PaymentApproveRequest(BaseModel):
    tid: str
    pg_token: str
    order_id: str
    

# 결제 취소 요청 스키마 추가
class PaymentCancelRequest(BaseModel):
    payment_id: str = Field(..., description="취소할 결제 ID")
    cancel_reason: str = Field(..., description="취소 사유")
    cancel_amount: Optional[int] = Field(None, description="부분 취소 금액 (전액 취소시 None)")



# 결제 목록 조회 응답 스키마
class PaymentListResponse(BaseModel):
    total: int = Field(..., description="전체 결제 수")
    payments: List[PaymentResponse] = Field(..., description="결제 목록")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기") 