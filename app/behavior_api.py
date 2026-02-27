#!/usr/bin/env python3
"""
船舶行为分析API
提供AIS轨迹查询、异常检测、地理围栏等功能
"""
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.database import get_mongo_db
from bson import ObjectId

router = APIRouter()


class VesselTrackQuery(BaseModel):
    """船舶轨迹查询参数"""
    imo_number: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 1000


class AnomalyQuery(BaseModel):
    """异常查询参数"""
    imo_number: Optional[str] = None
    limit: int = 50


class GeofenceQuery(BaseModel):
    """地理围栏查询参数"""
    min_lng: float
    max_lng: float
    min_lat: float
    max_lat: float
    start_date: Optional[str] = None
    limit: int = 100


class VesselStatisticsQuery(BaseModel):
    """船舶统计查询参数"""
    imo_number: Optional[str] = None
    ship_type: Optional[str] = None
    limit: int = 20


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


@router.post("/api/behavior/tracks")
async def get_vessel_tracks(request: Request, payload: VesselTrackQuery):
    """
    获取指定船舶的历史轨迹

    参数：
    - imo_number: IMO编号
    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）
    - limit: 返回记录数限制（默认1000）
    """
    try:
        db = get_mongo_db()
        collection = db["ais_tracks"]

        # 构建查询条件
        query = {"imo_number": payload.imo_number}

        # 添加时间范围过滤
        if payload.start_date or payload.end_date:
            time_filter = {}
            if payload.start_date:
                time_filter["$gte"] = datetime.fromisoformat(payload.start_date)
            if payload.end_date:
                time_filter["$lte"] = datetime.fromisoformat(payload.end_date)
            query["timestamp"] = time_filter

        # 查询轨迹数据
        tracks = list(collection.find(query)
                     .sort("timestamp", 1)
                     .limit(payload.limit))

        # 序列化结果
        tracks_serialized = serialize_mongo_doc(tracks)

        return JSONResponse({
            "success": True,
            "count": len(tracks_serialized),
            "imo_number": payload.imo_number,
            "tracks": tracks_serialized
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "msg": f"查询失败: {str(e)}"
        }, status_code=500)


@router.post("/api/behavior/anomalies")
async def get_anomalies(request: Request, payload: AnomalyQuery):
    """
    获取异常停泊记录

    参数：
    - imo_number: IMO编号（可选，不指定则返回所有）
    - limit: 返回记录数限制（默认50）
    """
    try:
        db = get_mongo_db()
        collection = db["ais_anomalies"]

        # 构建查询条件
        query = {}
        if payload.imo_number:
            query["imo_number"] = payload.imo_number

        # 查询异常记录
        anomalies = list(collection.find(query)
                        .sort("timestamp", -1)
                        .limit(payload.limit))

        # 序列化结果
        anomalies_serialized = serialize_mongo_doc(anomalies)

        return JSONResponse({
            "success": True,
            "count": len(anomalies_serialized),
            "anomalies": anomalies_serialized
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "msg": f"查询失败: {str(e)}"
        }, status_code=500)


@router.post("/api/behavior/geofence")
async def geofence_query(request: Request, payload: GeofenceQuery):
    """
    地理围栏查询：查询指定区域内的船舶

    参数：
    - min_lng: 最小经度
    - max_lng: 最大经度
    - min_lat: 最小纬度
    - max_lat: 最大纬度
    - start_date: 开始日期（可选）
    - limit: 返回记录数限制（默认100）
    """
    try:
        db = get_mongo_db()
        collection = db["ais_tracks"]

        # 构建地理围栏查询
        query = {
            "position": {
                "$geoWithin": {
                    "$box": [
                        [payload.min_lng, payload.min_lat],
                        [payload.max_lng, payload.max_lat]
                    ]
                }
            }
        }

        # 添加时间过滤
        if payload.start_date:
            query["timestamp"] = {"$gte": datetime.fromisoformat(payload.start_date)}

        # 查询船舶
        vessels = list(collection.find(query)
                      .sort("timestamp", -1)
                      .limit(payload.limit))

        # 序列化结果
        vessels_serialized = serialize_mongo_doc(vessels)

        return JSONResponse({
            "success": True,
            "count": len(vessels_serialized),
            "area": {
                "min_lng": payload.min_lng,
                "max_lng": payload.max_lng,
                "min_lat": payload.min_lat,
                "max_lat": payload.max_lat
            },
            "vessels": vessels_serialized
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "msg": f"查询失败: {str(e)}"
        }, status_code=500)


@router.post("/api/behavior/statistics")
async def get_vessel_statistics(request: Request, payload: VesselStatisticsQuery):
    """
    获取船舶统计信息（Spark分析结果）

    参数：
    - imo_number: IMO编号（可选）
    - ship_type: 船舶类型（可选）
    - limit: 返回记录数限制（默认20）
    """
    try:
        db = get_mongo_db()
        collection = db["vessel_statistics"]

        # 构建查询条件
        query = {}
        if payload.imo_number:
            query["imo_number"] = payload.imo_number
        if payload.ship_type:
            query["ship_type"] = payload.ship_type

        # 查询统计数据
        statistics = list(collection.find(query)
                         .sort("track_count", -1)
                         .limit(payload.limit))

        # 序列化结果
        statistics_serialized = serialize_mongo_doc(statistics)

        return JSONResponse({
            "success": True,
            "count": len(statistics_serialized),
            "statistics": statistics_serialized
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "msg": f"查询失败: {str(e)}"
        }, status_code=500)


@router.get("/api/behavior/summary")
async def get_behavior_summary(request: Request):
    """
    获取行为分析总览

    返回：
    - 总轨迹点数
    - 总船舶数
    - 异常停泊次数
    - 数据时间范围
    """
    try:
        db = get_mongo_db()

        # 统计轨迹数据
        tracks_collection = db["ais_tracks"]
        total_tracks = tracks_collection.count_documents({})
        vessel_count = len(tracks_collection.distinct("imo_number"))

        # 获取时间范围
        oldest = tracks_collection.find_one(sort=[("timestamp", 1)])
        newest = tracks_collection.find_one(sort=[("timestamp", -1)])

        # 统计异常记录
        anomalies_collection = db["ais_anomalies"]
        anomaly_count = anomalies_collection.count_documents({})

        # 统计船舶类型分布
        ship_types = tracks_collection.aggregate([
            {"$group": {"_id": "$ship_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])

        return JSONResponse({
            "success": True,
            "summary": {
                "total_tracks": total_tracks,
                "vessel_count": vessel_count,
                "anomaly_count": anomaly_count,
                "time_range": {
                    "start": oldest["timestamp"].isoformat() if oldest else None,
                    "end": newest["timestamp"].isoformat() if newest else None
                },
                "ship_type_distribution": [
                    {"type": item["_id"], "count": item["count"]}
                    for item in ship_types
                ]
            }
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "msg": f"查询失败: {str(e)}"
        }, status_code=500)


@router.get("/api/behavior/vessels")
async def get_vessel_list(request: Request):
    """
    获取船舶列表（从MongoDB的ais_tracks集合中获取）

    返回：
    - 船舶列表（imo_number, vessel_name, ship_type）
    """
    try:
        db = get_mongo_db()
        tracks_collection = db["ais_tracks"]

        # 使用聚合管道获取不同的船舶
        vessels = list(tracks_collection.aggregate([
            {
                "$group": {
                    "_id": "$imo_number",
                    "vessel_name": {"$first": "$vessel_name"},
                    "ship_type": {"$first": "$ship_type"},
                    "flag": {"$first": "$flag"}
                }
            },
            {"$sort": {"vessel_name": 1}},
            {"$limit": 100}
        ]))

        # 格式化结果
        vessel_list = [
            {
                "imo_number": v["_id"],
                "vessel_name": v.get("vessel_name", "Unknown"),
                "ship_type": v.get("ship_type", "Unknown"),
                "flag": v.get("flag", "Unknown")
            }
            for v in vessels
        ]

        return JSONResponse({
            "success": True,
            "count": len(vessel_list),
            "vessels": vessel_list
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "msg": f"查询失败: {str(e)}"
        }, status_code=500)


if __name__ == "__main__":
    # 测试API
    import asyncio
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    print("船舶行为分析API已加载")
    print("可用端点：")
    print("  POST /api/behavior/tracks - 获取船舶轨迹")
    print("  POST /api/behavior/anomalies - 获取异常停泊记录")
    print("  POST /api/behavior/geofence - 地理围栏查询")
    print("  POST /api/behavior/statistics - 获取船舶统计")
    print("  GET  /api/behavior/summary - 获取行为分析总览")
    print("  GET  /api/behavior/vessels - 获取船舶列表")
