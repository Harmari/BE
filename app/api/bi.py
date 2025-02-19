from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from app.analytics.metrics_analyzer import MetricsAnalyzer
from datetime import datetime, timedelta
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        analyzer = MetricsAnalyzer()
        stats = await analyzer.get_reservation_stats()
        context = {"request": request, "stats": stats}
        return templates.TemplateResponse("dashboard.html", context)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "error": str(e),
                "stats": {
                    "total_visitors": 0,
                    "total_reservation_attempts": 0,
                    "total_reservation_completed": 0,
                    "attempt_rate": 0,
                    "conversion_rate": 0,
                    "user_stats": []
                }
            }
        )

@router.get("/api/metrics/overall")
async def overall_metrics():
    analyzer = MetricsAnalyzer()
    data = await analyzer.get_overall_stats()
    logger.info(f"Sending overall_metrics data: {data}")
    return JSONResponse(content=jsonable_encoder(data))

@router.get("/api/metrics/conversion")
async def conversion_metrics(days: int = 30):
    analyzer = MetricsAnalyzer()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    data = await analyzer.get_conversion_rates(start_date, end_date)
    logger.info(f"Sending conversion_metrics data: {data}")
    return JSONResponse(content=jsonable_encoder(data))

@router.get("/api/metrics/retention")
async def retention_metrics(days: int = 30):
    analyzer = MetricsAnalyzer()
    data = await analyzer.get_user_retention(days)
    logger.info(f"Sending retention_metrics data: {data}")
    return JSONResponse(content=jsonable_encoder(data))

@router.get("/api/metrics/performance")
async def performance_metrics():
    analyzer = MetricsAnalyzer()
    data = await analyzer.get_performance_metrics()
    logger.info(f"Sending performance_metrics data: {data}")
    return JSONResponse(content=jsonable_encoder(data))
