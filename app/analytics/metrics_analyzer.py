from datetime import datetime, timedelta
from typing import Dict, List
from app.db.session import get_database

class MetricsAnalyzer:
    def __init__(self):
        self.db = get_database()
    
    async def get_conversion_rates(self, start_date: datetime, end_date: datetime) -> Dict:
        """결제 전환율 분석"""
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date, "$lte": end_date},
                    "endpoint_category": {"$in": ["payment", "reservation"]}
                }
            },
            {
                "$group": {
                    "_id": "$endpoint_category",
                    "total_requests": {"$sum": 1},
                    "successful_requests": {
                        "$sum": {"$cond": [{"$lt": ["$status_code", 400]}, 1, 0]}
                    }
                }
            }
        ]
        
        results = await self.db["metrics"].aggregate(pipeline).to_list(None)
        return {
            doc["_id"]: {
                "conversion_rate": doc["successful_requests"] / doc["total_requests"] if doc["total_requests"] > 0 else 0,
                "total_requests": doc["total_requests"],
                "successful_requests": doc["successful_requests"]
            }
            for doc in results
        }
    
    async def get_user_retention(self, days: int = 30) -> Dict:
        """사용자 이탈률 분석"""
        cutoff_date = datetime.now() - timedelta(days=days)
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": cutoff_date},
                    "endpoint_category": "auth"
                }
            },
            {
                "$group": {
                    "_id": "$client_info.ip",
                    "last_seen": {"$max": "$timestamp"},
                    "first_seen": {"$min": "$timestamp"},
                    "visit_count": {"$sum": 1}
                }
            }
        ]
        
        results = await self.db["metrics"].aggregate(pipeline).to_list(None)
        return {
            "total_users": len(results),
            "active_users": sum(1 for r in results if (datetime.now() - r["last_seen"]).days <= 7),
            "retention_rate": len([r for r in results if r["visit_count"] > 1]) / len(results) if results else 0
        }
    
    async def get_performance_metrics(self) -> Dict:
        """성능 메트릭스 분석"""
        pipeline = [
            {
                "$group": {
                    "_id": "$endpoint_category",
                    "avg_response_time": {"$avg": "$performance.total_time_ms"},
                    "max_response_time": {"$max": "$performance.total_time_ms"},
                    "error_rate": {
                        "$avg": {"$cond": [{"$gte": ["$status_code", 400]}, 1, 0]}
                    }
                }
            }
        ]
        
        results = await self.db["metrics"].aggregate(pipeline).to_list(None)
        return {doc["_id"]: doc for doc in results} 