import os
import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from app.db.session import get_database
from app.core.config import settings

router = APIRouter()
db = get_database()

class ClickEvent(BaseModel):
    event_type: str
    button_location: str
    user_agent: Optional[str] = None
    referrer: Optional[str] = None

@router.get("/", response_class=HTMLResponse)
async def introduce():
    # templates 폴더에서 introduce.html 파일 경로 설정
    html_path = os.path.join(os.getcwd(), "app", "templates", "introduce.html")
    
    # HTML 파일이 존재하는지 확인
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return html_content
    else:
        # 파일이 없는 경우 오류 메시지 제공
        return """
        <html>
            <head>
                <title>소개 페이지</title>
            </head>
            <body>
                <h1>오류 발생</h1>
                <p>introduce.html 파일을 찾을 수 없습니다.</p>
            </body>
        </html>
        """

@router.post("/click-event")
async def record_click_event(request: Request, event: ClickEvent):
    # MongoDB에 저장할 데이터
    click_data = {
        "event_type": event.event_type,
        "button_location": event.button_location,
        "user_agent": event.user_agent,
        "referrer": event.referrer,
        "ip_address": request.client.host if request.client else None,
        "timestamp": settings.CURRENT_DATETIME,  # 기존 프로젝트 패턴과 동일하게 settings에서 시간 가져오기
        "url": str(request.url)
    }
    
    # MongoDB에 데이터 저장
    try:
        db["click_events"].insert_one(click_data)
        return JSONResponse({"status": "success"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})