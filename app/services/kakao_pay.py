from typing import Optional
import httpx
import ssl
from fastapi import HTTPException
from app.core.config import settings

class KakaoPayService:
    def __init__(self):
        self.api_host = "https://open-api.kakaopay.com" # 카카오페이 API 호스트
        self.headers = {
            "Authorization": f"KakaoAK {settings.KAKAO_PAY_SECRET_KEY_DEV}",
            "Content-Type": "application/json"
        }
        self.redirect_host = settings.FRONTEND_URL
        

    # 결제 준비 API    
    async def ready_to_pay(self, 
                          order_id: str,
                          user_id: str,
                          item_name: str,
                          quantity: int,
                          total_amount: int,
                          vat_amount: Optional[int] = None,
                          tax_free_amount: int = 0) -> dict:
        """결제 준비 API"""
        payload = {
            "cid": "TC0ONETIME",
            "partner_order_id": str(order_id),
            "partner_user_id": str(user_id),
            "item_name": str(item_name),
            "quantity": str(quantity),
            "total_amount": str(total_amount),
            "tax_free_amount": str(tax_free_amount),
            "approval_url": f"{self.redirect_host}/payment/success",
            "cancel_url": f"{self.redirect_host}/payment/cancel",
            "fail_url": f"{self.redirect_host}/payment/fail"
        }
        
        print("\n=== Request Debug Info ===")
        print("1. API URL:", f"{self.api_host}/online/v1/payment/ready")
        print("2. Headers:", {
            k: (v[:10] + "..." if k == "Authorization" else v) 
            for k, v in self.headers.items()
        })
        print("3. Payload:", payload)
        print("4. Environment:", {
            "FRONTEND_URL": settings.FRONTEND_URL,
            "API_HOST": self.api_host,
            "SECRET_KEY": settings.KAKAO_PAY_SECRET_KEY_DEV[:10] + "..."
        })
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_host}/online/v1/payment/ready",
                    json=payload,
                    headers=self.headers
                )
                
                if not response.is_success:
                    print("\n=== Error Debug Info ===")
                    print("Status Code:", response.status_code)
                    print("Response Headers:", dict(response.headers))
                    print("Response Body:", response.text)
                    print("=====================\n")
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print("Error Details:", str(e))
                raise HTTPException(status_code=400, detail=f"카카오페이 API 호출 실패: {str(e)}")



    # 결제 승인 API
    async def approve_payment(self, tid: str, pg_token: str, order_id: str, user_id: str) -> dict:
        """결제 승인 API"""
        try:
            payload = {
                "cid": "TC0ONETIME",
                "tid": tid,
                "partner_order_id": str(order_id),
                "partner_user_id": str(user_id),
                "pg_token": pg_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_host}/online/v1/payment/approve",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise


    # 결제 취소 API
    async def cancel_payment(
        self,
        tid: str,
        cancel_amount: int,
        cancel_tax_free_amount: int = 0,
        cancel_reason: str = "사용자 요청"
    ) -> dict:
        """결제 취소 API"""
        payload = {
            "cid": "TC0ONETIME",  # 테스트용 단건결제 코드
            "tid": tid,
            "cancel_amount": str(cancel_amount),
            "cancel_tax_free_amount": str(cancel_tax_free_amount),
            "cancel_reason": cancel_reason
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_host}/online/v1/payment/cancel",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(status_code=400, detail=f"카카오페이 결제 취소 실패: {str(e)}") 
