from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi import Request
from app.core.config import settings

class CombinedCorsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.allowed_origins = [url.strip() for url in settings.FRONTEND_URL.split(",")]
        self.allow_methods = "GET, POST, OPTIONS"
        self.allow_headers = "*"
        self.allow_credentials = "true"

    async def dispatch(self, request: Request, call_next):
        # Determine client origin from request headers
        origin = request.headers.get("origin")
        chosen_origin = origin if origin in self.allowed_origins else self.allowed_origins[0]
        request.state.client_origin = chosen_origin  # Store for app usage

        response = await call_next(request)

        # Set CORS headers on the response
        response.headers["Access-Control-Allow-Origin"] = chosen_origin
        response.headers["Access-Control-Allow-Methods"] = self.allow_methods
        response.headers["Access-Control-Allow-Headers"] = self.allow_headers
        response.headers["Access-Control-Allow-Credentials"] = self.allow_credentials

        # Handle preflight OPTIONS request if necessary
        if request.method == "OPTIONS":
            response.status_code = 200

        return response
