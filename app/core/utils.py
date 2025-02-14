# app/middleware.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

class ClientOriginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        allowed_origins = [url.strip() for url in settings.FRONTEND_URL.split(",")]
        origin = request.headers.get("origin")
        request.state.client_origin = origin if origin in allowed_origins else allowed_origins[0]
        response = await call_next(request)
        return response
