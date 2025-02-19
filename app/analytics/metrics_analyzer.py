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

    async def get_designer_stats(self) -> list:
        pipeline = [
            {
                "$facet": {
                    "views": [
                        {
                            "$match": {
                                "endpoint_category": "designers",
                                "path": { "$regex": "^/designers/([a-f0-9]+)$" }
                            }
                        },
                        {
                            "$addFields": {
                                "designer_id": { "$arrayElemAt": [ { "$split": [ "$path", "/" ] }, 2 ] }
                            }
                        },
                        {
                            "$group": {
                                "_id": "$designer_id",
                                "viewCount": { "$sum": 1 }
                            }
                        }
                    ],
                    "reservations": [
                        {
                            "$match": {
                                "endpoint_category": "reservation",
                                "path": "/reservation/create",
                                "status_code": 200
                            }
                        },
                        {
                            "$project": {
                                "designer_id": "$request_details.body.designer_id"
                            }
                        },
                        { "$match": { "designer_id": { "$ne": None } } },
                        {
                            "$group": {
                                "_id": "$designer_id",
                                "reservationCount": { "$sum": 1 }
                            }
                        }
                    ]
                }
            },
            {
                "$project": {
                    "combined": {
                        "$map": {
                            "input": "$views",
                            "as": "v",
                            "in": {
                                "designer_id": "$$v._id",
                                "viewCount": "$$v.viewCount",
                                "reservationCount": {
                                    "$reduce": {
                                        "input": {
                                            "$filter": {
                                                "input": "$reservations",
                                                "as": "r",
                                                "cond": { "$eq": [ "$$r._id", "$$v._id" ] }
                                            }
                                        },
                                        "initialValue": 0,
                                        "in": { "$add": [ "$$value", "$$this.reservationCount" ] }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            { "$unwind": "$combined" },
            {
                "$project": {
                    "designer_id": "$combined.designer_id",
                    "viewCount": "$combined.viewCount",
                    "reservationCount": "$combined.reservationCount",
                    "reservationRate": {
                        "$cond": [
                            { "$gt": [ "$combined.viewCount", 0 ] },
                            { "$multiply": [ { "$divide": [ "$combined.reservationCount", "$combined.viewCount" ] }, 100 ] },
                            0
                        ]
                    }
                }
            },
            {
                "$lookup": {
                    "from": "designers",
                    "let": { "designerId": { "$toObjectId": "$designer_id" } },
                    "pipeline": [
                        { "$match": { "$expr": { "$eq": [ "$_id", "$$designerId" ] } } },
                        { "$project": { "name": 1, "_id": 0 } }
                    ],
                    "as": "designer_info"
                }
            },
            {
                "$addFields": {
                    "designer_name": { "$arrayElemAt": [ "$designer_info.name", 0 ] }
                }
            },
            {
                "$project": {
                    "designer_name": 1,
                    "viewCount": 1,
                    "reservationCount": 1,
                    "reservationRate": 1
                }
            }
        ]
        result = await self.db["metrics"].aggregate(pipeline).to_list(None)
        return result