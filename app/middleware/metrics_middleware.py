import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.session import get_database
from app.core.config import settings

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Gather additional details for detailed logging
        query_params = dict(request.query_params)
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")

        log_data = {
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "process_time": process_time,
            "query_params": query_params,
            "client_host": client_host,
            "user_agent": user_agent,
            "timestamp": settings.CURRENT_DATETIME,
        }

        db = get_database()
        try:
            db["log"].insert_one(log_data)
        except Exception as e:
            print("Failed to log metrics:", str(e))

        return response
