# app/main.py
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api import test, reservation, auth, user, designer, bi
from app.core.config import settings
from app.db.session import get_database
# 결제
from app.api.payment.router import router as payment_router
from app.scheduler.schedulers import start_scheduler
from app.middleware.cors_middleware import CorsMiddleware
from app.middleware.metrics_middleware import MetricsMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# 스케줄러
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션 시작 시 실행
    start_scheduler()
    # logger.info("Scheduler started on application startup.")
    yield  # 이 시점 이후에 애플리케이션 실행
    # 애플리케이션 종료 시 실행
    # logger.info("Application shutdown.")


app = FastAPI(title="할머리?머리하실?", description="API Documentation", version="1.0.0", lifespan=lifespan)



db = get_database()

# 미들웨어 설정
app.add_middleware(CorsMiddleware) # type: ignore
app.add_middleware(MetricsMiddleware) # type: ignore

# 에러 로깅
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 에러 정보 생성
    error_info = {
        "path": request.url.path,
        "method": request.method,
        "headers": dict(request.headers),
        "error_message": str(exc),
        "timestamp": settings.CURRENT_DATETIME,
    }

    # MongoDB에 에러 저장
    try:
        db["error"].insert_one(error_info)
    except Exception as db_exc:
        logger.error("Failed to log error to MongoDB: %s", str(db_exc))

    # 시스템 콘솔에 로그 출력
    logger.error(
        "ERROR::::::::::: %s\nPath: %s\nMethod: %s\nHeaders: %s\nTimestamp: %s",
        str(exc),
        request.url.path,
        request.method,
        dict(request.headers),
        settings.CURRENT_DATETIME,
    )

    # 클라이언트로 응답
    return JSONResponse(
        status_code=500,
        content={
            "message": "로그테이블 확인요청"
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # 에러 정보 생성
    error_info = {
        "path": request.url.path,
        "method": request.method,
        "headers": dict(request.headers),
        "status_code": exc.status_code,
        "error_message": exc.detail,
        "timestamp": settings.CURRENT_DATETIME,
    }

    # MongoDB에 에러 저장
    try:
        db["error"].insert_one(error_info)
    except Exception as db_exc:
        logger.error("Failed to log HTTPException to MongoDB: %s", str(db_exc))

    # 시스템 콘솔에 로그 출력
    logger.error(
        "HTTPException ::::::::: %s\nPath: %s\nMethod: %s\nHeaders: %s\nStatus: %s\nTimestamp: %s",
        exc.detail,
        request.url.path,
        request.method,
        dict(request.headers),
        exc.status_code,
        settings.CURRENT_DATETIME,
    )

    # 클라이언트로 응답
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


# 디렉토리 경로
images_directory = os.path.join(os.getcwd(), "images")

# 디렉토리 생성
if not os.path.exists(images_directory):
    os.makedirs(images_directory)

# 외부에서 '/static'경로로 접근할 수 있음 -> images 폴더
app.mount("/static", StaticFiles(directory=os.path.join(os.getcwd(), "images")), name="static")

# endpoint 설정하는 부분 하단에 import 후 추가

app.include_router(test.router, prefix="/test", tags=["test"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(reservation.router,prefix="/reservation", tags=["reservation"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(designer.designer_router, prefix="/designers", tags=["designers"])
app.include_router(bi.router, prefix="/bi", tags=["BI"])

# 결제 
app.include_router(payment_router)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Home</title>
        </head>
        <body>
            <h1>Welcome!</h1>
            <p><a href="/docs">DOCS</a></p>
            <p><a href="/bi/dashboard">bi</a></p>
        </body>
    </html>
    """

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")
