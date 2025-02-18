import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.session import get_database
from app.core.config import settings
from typing import Optional
import json

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 요청 바디 캡처 (결제, 예약 등 중요 데이터)
        request_body: Optional[dict] = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                raw_body = await request.body()
                request_body = json.loads(raw_body)
            except:
                request_body = None
        
        # 응답 처리
        try:
            response = await call_next(request)
            response_status = response.status_code
        except Exception as e:
            response_status = 500
            raise e
        finally:
            process_time = time.time() - start_time
            
            # 상세 메트릭스 수집
            path_parts = request.url.path.split('/')
            endpoint_category = path_parts[1] if len(path_parts) > 1 else 'root'
            
            metrics_data = {
                # 기본 요청 정보
                "timestamp": settings.CURRENT_DATETIME,
                "path": request.url.path,
                "endpoint_category": endpoint_category,
                "method": request.method,
                "status_code": response_status,
                "process_time_ms": round(process_time * 1000, 2),
                
                # 클라이언트 정보
                "client_info": {
                    "ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "referer": request.headers.get("referer"),
                    "accept_language": request.headers.get("accept-language"),
                },
                
                # 요청 상세
                "request_details": {
                    "query_params": dict(request.query_params),
                    "headers": dict(request.headers),
                    "cookies": dict(request.cookies),
                    "body": request_body if request_body else None,
                },
                
                # 성능 메트릭스
                "performance": {
                    "total_time_ms": round(process_time * 1000, 2),
                    "time_of_day": settings.CURRENT_DATETIME.strftime("%H:%M"),
                    "day_of_week": settings.CURRENT_DATETIME.strftime("%A"),
                },
                
                # 비즈니스 메트릭스
                "business_metrics": {
                    "is_payment_endpoint": endpoint_category == "payment",
                    "is_reservation_endpoint": endpoint_category == "reservation",
                    "is_auth_endpoint": endpoint_category == "auth",
                    "is_error": response_status >= 400,
                    "is_success": 200 <= response_status < 300,
                }
            }
            
            # MongoDB에 저장
            db = get_database()
            try:
                db["metrics"].insert_one(metrics_data)
            except Exception as e:
                print(f"Failed to log metrics: {str(e)}")
                
        return response
