import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

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