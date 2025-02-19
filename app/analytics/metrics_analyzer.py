from typing import Dict
from app.db.session import get_database

class MetricsAnalyzer:
    def __init__(self):
        self.db = get_database()

    async def get_reservation_stats(self) -> Dict:
        pipeline = [
            {
                "$match": {
                    "request_details.cookies.email": {"$exists": True}
                }
            },
            {
                "$project": {
                    "email": "$request_details.cookies.email",
                    "isVisitor": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$path", "/auth/login"]},
                                    {"$eq": ["$business_metrics.is_success", True]}
                                ]
                            },
                            1,
                            0
                        ]
                    },
                    "isReservationAttempt": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$path", "/payments/ready"]},
                                    {"$eq": ["$business_metrics.is_success", True]}
                                ]
                            },
                            1,
                            0
                        ]
                    },
                    "isReservationCompleted": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$path", "/payments/approve"]},
                                    {"$eq": ["$business_metrics.is_success", True]}
                                ]
                            },
                            1,
                            0
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$email",
                    "totalVisitors": {"$sum": "$isVisitor"},
                    "totalReservationAttempts": {"$sum": "$isReservationAttempt"},
                    "totalReservationCompleted": {"$sum": "$isReservationCompleted"}
                }
            }
        ]
        results = await self.db["metrics"].aggregate(pipeline).to_list(None)
        overall = {
            "total_visitors": 0,
            "total_reservation_attempts": 0,
            "total_reservation_completed": 0,
            "user_stats": []
        }
        for doc in results:
            overall["total_visitors"] += doc.get("totalVisitors", 0)
            overall["total_reservation_attempts"] += doc.get("totalReservationAttempts", 0)
            overall["total_reservation_completed"] += doc.get("totalReservationCompleted", 0)
            overall["user_stats"].append({
                "email": doc["_id"],
                "visitors": doc.get("totalVisitors", 0),
                "reservation_attempts": doc.get("totalReservationAttempts", 0),
                "reservation_completed": doc.get("totalReservationCompleted", 0),
                "attempt_rate": (doc.get("totalReservationAttempts", 0) / doc.get("totalVisitors", 1)
                                 if doc.get("totalVisitors", 0) > 0 else 0),
                "conversion_rate": (doc.get("totalReservationCompleted", 0) / doc.get("totalVisitors", 1)
                                    if doc.get("totalVisitors", 0) > 0 else 0)
            })
        overall["attempt_rate"] = (overall["total_reservation_attempts"] / overall["total_visitors"]
                                   if overall["total_visitors"] > 0 else 0)
        overall["conversion_rate"] = (overall["total_reservation_completed"] / overall["total_visitors"]
                                      if overall["total_visitors"] > 0 else 0)
        return overall