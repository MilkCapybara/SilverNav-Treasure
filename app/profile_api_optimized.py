#!/usr/bin/env python3
"""
船舶画像API - 优化版（使用ClickHouse）
提供船舶综合画像数据，包括基本信息、航行统计、风险评估等
"""
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.database import get_mongo_db, db_conn, query_all, query_one
from app.clickhouse_client import get_clickhouse_client
from bson import ObjectId

router = APIRouter()


def serialize_mongo_doc(doc):
    """序列化MongoDB文档"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_mongo_doc(d) for d in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = serialize_mongo_doc(value)
            elif isinstance(value, list):
                result[key] = serialize_mongo_doc(value)
            else:
                result[key] = value
        return result
    return doc


@router.get("/api/profile/overview")
async def get_profile_overview(request: Request, base_date: Optional[str] = None):
    """
    获取船舶画像总览（优化版 - 使用ClickHouse）

    参数：
    - base_date: 基准日期（可选，默认为今天）

    返回：
    - 船舶总数
    - 活跃船舶数
    - 船舶类型分布
    - 船旗国分布
    """
    try:
        # 尝试使用ClickHouse
        client = get_clickhouse_client()
        use_clickhouse = client is not None

        if use_clickhouse:
            # 使用ClickHouse查询（快速）
            print("📊 使用ClickHouse查询船舶画像总览")

            # 解析基准日期
            if base_date:
                target_date = datetime.fromisoformat(base_date).date()
            else:
                target_date = datetime.now().date()

            # 1. 统计船舶总数和活跃船舶
            vessel_stats = client.query("""
                SELECT
                    count(DISTINCT imo_number) as total_vessels,
                    countDistinctIf(imo_number, is_active = 1) as active_vessels
                FROM vessels FINAL
            """)

            total_vessels = int(vessel_stats.result_rows[0][0])
            active_vessels = int(vessel_stats.result_rows[0][1])

            # 2. 船舶类型分布（从vessels表）
            ship_type_dist = client.query("""
                SELECT vessel_type, count() as count
                FROM vessels FINAL
                WHERE is_active = 1 AND vessel_type IS NOT NULL
                GROUP BY vessel_type
                ORDER BY count DESC
                LIMIT 10
            """)

            # 3. 船旗国分布（从vessels表）
            flag_dist = client.query("""
                SELECT flag_country, count() as count
                FROM vessels FINAL
                WHERE is_active = 1 AND flag_country IS NOT NULL
                GROUP BY flag_country
                ORDER BY count DESC
                LIMIT 10
            """)

            return JSONResponse({
                "success": True,
                "data_source": "ClickHouse",
                "overview": {
                    "total_vessels": total_vessels,
                    "active_vessels": active_vessels,
                    "ship_type_distribution": [
                        {"type": row[0], "count": int(row[1])}
                        for row in ship_type_dist.result_rows
                    ],
                    "flag_distribution": [
                        {"flag": row[0], "count": int(row[1])}
                        for row in flag_dist.result_rows
                    ]
                }
            })

        else:
            # 降级到MongoDB（慢）
            print("⚠️ ClickHouse不可用，降级到MongoDB")
            db = get_mongo_db()
            tracks_collection = db["ais_tracks"]

            # 解析基准日期
            if base_date:
                target_date = datetime.fromisoformat(base_date)
            else:
                target_date = datetime.utcnow()

            # 统计船舶总数（使用缓存）
            total_vessels = len(tracks_collection.distinct("imo_number"))

            # 统计活跃船舶（最近7天有轨迹数据）
            seven_days_ago = target_date - timedelta(days=7)
            active_vessels = len(tracks_collection.distinct(
                "imo_number",
                {"timestamp": {"$gte": seven_days_ago, "$lte": target_date}}
            ))

            # 船舶类型分布
            ship_type_dist = list(tracks_collection.aggregate([
                {"$group": {"_id": "$ship_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))

            # 船旗国分布
            flag_dist = list(tracks_collection.aggregate([
                {"$group": {"_id": "$flag", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))

            return JSONResponse({
                "success": True,
                "data_source": "MongoDB",
                "overview": {
                    "total_vessels": total_vessels,
                    "active_vessels": active_vessels,
                    "ship_type_distribution": [
                        {"type": item["_id"], "count": item["count"]}
                        for item in ship_type_dist
                    ],
                    "flag_distribution": [
                        {"flag": item["_id"], "count": item["count"]}
                        for item in flag_dist
                    ]
                }
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "msg": f"查询失败: {str(e)}"
        }, status_code=500)


@router.get("/api/profile/vessel/{imo_number}")
async def get_vessel_profile(request: Request, imo_number: str, base_date: Optional[str] = None):
    """
    获取指定船舶的详细画像（优化版）

    参数：
    - imo_number: IMO编号
    - base_date: 基准日期（可选）

    返回：
    - 基本信息（从PostgreSQL vessels表）
    - 航行统计（从MongoDB ais_tracks）
    - 分析结果（从MongoDB vessel_analysis）
    """
    try:
        # 解析基准日期
        if base_date:
            target_date = datetime.fromisoformat(base_date)
        else:
            target_date = datetime.utcnow()

        # 优先从ClickHouse获取基本信息
        client = get_clickhouse_client()
        vessel_pg_info = None

        if client:
            try:
                result = client.query("""
                    SELECT *
                    FROM vessels FINAL
                    WHERE imo_number = {imo:String}
                    LIMIT 1
                """, parameters={'imo': imo_number})

                if result.result_rows:
                    columns = result.column_names
                    row = result.result_rows[0]
                    vessel_pg_info = {col: val for col, val in zip(columns, row)}
            except Exception as e:
                print(f"ClickHouse查询失败，降级到PostgreSQL: {e}")

        # 如果ClickHouse失败，从PostgreSQL获取
        if not vessel_pg_info:
            try:
                with db_conn("readonly") as conn:
                    vessel_pg_info = query_one(
                        conn,
                        "SELECT * FROM vessels WHERE imo_number = %s",
                        (imo_number,)
                    )
            except Exception as e:
                print(f"PostgreSQL查询失败: {e}")

        if not vessel_pg_info:
            return JSONResponse({
                "success": False,
                "msg": "未找到该船舶"
            }, status_code=404)

        # 从MongoDB获取航行数据
        db = get_mongo_db()
        tracks_collection = db["ais_tracks"]

        # 统计航行数据（最近30天）
        thirty_days_ago = target_date - timedelta(days=30)
        track_count = tracks_collection.count_documents({
            "imo_number": imo_number,
            "timestamp": {"$gte": thirty_days_ago, "$lte": target_date}
        })

        # 计算平均速度
        avg_speed_result = list(tracks_collection.aggregate([
            {
                "$match": {
                    "imo_number": imo_number,
                    "timestamp": {"$gte": thirty_days_ago, "$lte": target_date}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_speed": {"$avg": "$speed"},
                    "max_speed": {"$max": "$speed"}
                }
            }
        ]))

        avg_speed = avg_speed_result[0]["avg_speed"] if avg_speed_result else 0
        max_speed = avg_speed_result[0]["max_speed"] if avg_speed_result else 0

        # 获取最新位置
        latest_track = tracks_collection.find_one(
            {"imo_number": imo_number},
            sort=[("timestamp", -1)]
        )

        # 获取分析结果
        analysis_collection = db["vessel_analysis"]
        analysis_data = analysis_collection.find_one({"imo_number": imo_number})

        # 组装返回数据
        profile = {
            "imo_number": imo_number,
            "vessel_name": vessel_pg_info.get("vessel_name", "Unknown"),
            "vessel_type": vessel_pg_info.get("vessel_type", "Unknown"),
            "flag_country": vessel_pg_info.get("flag_country", "Unknown"),
            "build_year": vessel_pg_info.get("build_year"),
            "track_count_30d": track_count,
            "avg_speed": round(avg_speed, 2) if avg_speed else 0,
            "max_speed": round(max_speed, 2) if max_speed else 0,
            "latest_position": {
                "lng": latest_track["position"]["coordinates"][0] if latest_track and "position" in latest_track else None,
                "lat": latest_track["position"]["coordinates"][1] if latest_track and "position" in latest_track else None,
                "timestamp": latest_track["timestamp"].isoformat() if latest_track else None
            },
            "pg_info": vessel_pg_info,
            "analysis": serialize_mongo_doc(analysis_data) if analysis_data else None
        }

        return JSONResponse({
            "success": True,
            "profile": profile
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "msg": f"查询失败: {str(e)}"
        }, status_code=500)


@router.get("/api/profile/statistics")
async def get_profile_statistics(request: Request, base_date: Optional[str] = None):
    """
    获取船舶画像统计数据（优化版 - 使用ClickHouse）

    返回：
    - 航行里程Top10
    - 航行时长Top10
    - 平均速度分布
    - 船龄分布
    """
    try:
        # 尝试使用ClickHouse
        client = get_clickhouse_client()

        if client:
            print("📊 使用ClickHouse查询统计数据")

            # 船龄分布
            age_distribution = client.query("""
                SELECT
                    CASE
                        WHEN year(now()) - build_year < 5 THEN '0-5年'
                        WHEN year(now()) - build_year < 10 THEN '5-10年'
                        WHEN year(now()) - build_year < 15 THEN '10-15年'
                        WHEN year(now()) - build_year < 20 THEN '15-20年'
                        ELSE '20年以上'
                    END as age_range,
                    count() as count
                FROM vessels FINAL
                WHERE is_active = 1 AND build_year > 0
                GROUP BY age_range
                ORDER BY age_range
            """)

            # 风险评分分布
            risk_distribution = client.query("""
                SELECT
                    risk_level,
                    count() as count,
                    avg(asset_risk_score) as avg_score
                FROM vessels FINAL
                WHERE is_active = 1
                GROUP BY risk_level
                ORDER BY risk_level
            """)

            return JSONResponse({
                "success": True,
                "data_source": "ClickHouse",
                "statistics": {
                    "age_distribution": [
                        {"range": row[0], "count": int(row[1])}
                        for row in age_distribution.result_rows
                    ],
                    "risk_distribution": [
                        {
                            "risk_level": row[0],
                            "count": int(row[1]),
                            "avg_score": float(row[2]) if row[2] else 0.0
                        }
                        for row in risk_distribution.result_rows
                    ]
                }
            })

        else:
            # 降级到MongoDB
            print("⚠️ ClickHouse不可用，降级到MongoDB")

            if base_date:
                target_date = datetime.fromisoformat(base_date)
            else:
                target_date = datetime.utcnow()

            db = get_mongo_db()
            tracks_collection = db["ais_tracks"]

            # 计算每艘船的轨迹点数（作为活跃度指标）
            thirty_days_ago = target_date - timedelta(days=30)
            vessel_activity = list(tracks_collection.aggregate([
                {
                    "$match": {
                        "timestamp": {"$gte": thirty_days_ago, "$lte": target_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$imo_number",
                        "vessel_name": {"$first": "$vessel_name"},
                        "ship_type": {"$first": "$ship_type"},
                        "track_count": {"$sum": 1},
                        "avg_speed": {"$avg": "$speed"}
                    }
                },
                {"$sort": {"track_count": -1}},
                {"$limit": 10}
            ]))

            # 速度分布统计
            speed_distribution = list(tracks_collection.aggregate([
                {
                    "$match": {
                        "timestamp": {"$gte": thirty_days_ago, "$lte": target_date},
                        "speed": {"$gte": 0}
                    }
                },
                {
                    "$bucket": {
                        "groupBy": "$speed",
                        "boundaries": [0, 5, 10, 15, 20, 25, 30, 100],
                        "default": "Other",
                        "output": {
                            "count": {"$sum": 1}
                        }
                    }
                }
            ]))

            return JSONResponse({
                "success": True,
                "data_source": "MongoDB",
                "statistics": {
                    "vessel_activity_top10": [
                        {
                            "imo_number": v["_id"],
                            "vessel_name": v.get("vessel_name", "Unknown"),
                            "ship_type": v.get("ship_type", "Unknown"),
                            "track_count": v["track_count"],
                            "avg_speed": round(v.get("avg_speed", 0), 2)
                        }
                        for v in vessel_activity
                    ],
                    "speed_distribution": [
                        {
                            "range": f"{item['_id']}-{item['_id']+5}" if isinstance(item['_id'], int) else str(item['_id']),
                            "count": item["count"]
                        }
                        for item in speed_distribution
                    ]
                }
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "msg": f"查询失败: {str(e)}"
        }, status_code=500)


if __name__ == "__main__":
    print("船舶画像API（优化版）已加载")
    print("可用端点：")
    print("  GET /api/profile/overview - 获取船舶画像总览（使用ClickHouse）")
    print("  GET /api/profile/vessel/{imo_number} - 获取指定船舶画像")
    print("  GET /api/profile/statistics - 获取统计数据（使用ClickHouse）")
