from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import Response
from fastapi import Request
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CombinedCorsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # 여러 URL이 있을 경우 쉼표로 구분하여 설정값을 읽음
        self.allowed_origins = [url.strip() for url in settings.FRONTEND_URL.split(",")]
        self.allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allow_headers = ["Content-Type", "Set-Cookie", "Authorization"]
        self.expose_headers = ["Content-Type", "Set-Cookie"]
        self.allow_credentials = True
        self.max_age = 3600

    async def dispatch(self, request: Request, call_next):
        # 클라이언트의 origin 헤더를 확인
        origin = request.headers.get("origin")
        chosen_origin = origin if origin in self.allowed_origins else self.allowed_origins[0]
        request.state.client_origin = chosen_origin  # 필요 시 앱에서 사용

        logger.info("Request cookies: %s", request.cookies)

        # preflight OPTIONS 요청인 경우, 빈 응답을 생성합니다.
        if request.method == "OPTIONS":
            response = Response(status_code=200)
        else:
            response = await call_next(request)

        # CORS 헤더 설정
        response.headers["Access-Control-Allow-Origin"] = chosen_origin
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
        response.headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()
        response.headers["Access-Control-Max-Age"] = str(self.max_age)

        return response
