from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.analytics.metrics_analyzer import MetricsAnalyzer
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    analyzer = MetricsAnalyzer()
    
    # 최근 30일 데이터 분석
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # 각종 메트릭스 수집
    conversion_rates = await analyzer.get_conversion_rates(start_date, end_date)
    retention_data = await analyzer.get_user_retention(30)
    performance_data = await analyzer.get_performance_metrics()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "conversion_rates": conversion_rates,
            "retention_data": retention_data,
            "performance_data": performance_data
        }
    )

@router.get("/api/metrics/conversion")
async def get_conversion_metrics():
    analyzer = MetricsAnalyzer()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    return await analyzer.get_conversion_rates(start_date, end_date)

@router.get("/api/metrics/retention")
async def get_retention_metrics():
    analyzer = MetricsAnalyzer()
    return await analyzer.get_user_retention()

@router.get("/api/metrics/performance")
async def get_performance_metrics():
    analyzer = MetricsAnalyzer()
    return await analyzer.get_performance_metrics()
