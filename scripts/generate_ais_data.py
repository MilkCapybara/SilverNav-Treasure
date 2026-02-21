#!/usr/bin/env python3
"""
生成模拟AIS轨迹数据并导入MongoDB
目标：200万条轨迹记录
"""
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

import random
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING
from app.config import settings
from app.database import db_conn, query_all

# 航线模板（主要航线）
ROUTES = [
    {
        "name": "上海-宁波",
        "waypoints": [
            (121.4737, 31.2304),  # 上海
            (121.5500, 30.8000),
            (121.8500, 30.0000),
            (121.5500, 29.8686)   # 宁波
        ]
    },
    {
        "name": "上海-深圳",
        "waypoints": [
            (121.4737, 31.2304),  # 上海
            (120.5000, 28.0000),
            (119.5000, 25.0000),
            (114.0579, 22.5431)   # 深圳
        ]
    },
    {
        "name": "上海-新加坡",
        "waypoints": [
            (121.4737, 31.2304),  # 上海
            (118.0000, 24.0000),
            (115.0000, 18.0000),
            (110.0000, 10.0000),
            (103.8198, 1.3521)    # 新加坡
        ]
    },
    {
        "name": "深圳-香港",
        "waypoints": [
            (114.0579, 22.5431),  # 深圳
            (114.1694, 22.3193)   # 香港
        ]
    },
    {
        "name": "宁波-釜山",
        "waypoints": [
            (121.5500, 29.8686),  # 宁波
            (125.0000, 32.0000),
            (129.0756, 35.1796)   # 釜山
        ]
    }
]

# 船舶状态
VESSEL_STATUS = [
    "underway using engine",
    "at anchor",
    "not under command",
    "restricted manoeuvrability",
    "moored"
]

# 船舶类型
SHIP_TYPES = [
    "Container Ship",
    "Bulk Carrier",
    "Oil Tanker",
    "LNG Carrier",
    "General Cargo"
]

# 国旗
FLAGS = ["CN", "HK", "SG", "JP", "KR", "PA", "LR", "MT"]


def interpolate_position(start, end, ratio):
    """在两个坐标点之间插值"""
    lng1, lat1 = start
    lng2, lat2 = end
    lng = lng1 + (lng2 - lng1) * ratio
    lat = lat1 + (lat2 - lat1) * ratio
    return (lng, lat)


def generate_vessel_track(vessel, route, start_time, hours=72):
    """为单艘船生成一条航线的轨迹"""
    tracks = []
    waypoints = route["waypoints"]

    # 计算总航程点数（每小时1个点）
    total_points = hours
    points_per_segment = total_points // (len(waypoints) - 1)

    current_time = start_time

    for i in range(len(waypoints) - 1):
        start_point = waypoints[i]
        end_point = waypoints[i + 1]

        for j in range(points_per_segment):
            ratio = j / points_per_segment
            lng, lat = interpolate_position(start_point, end_point, ratio)

            # 添加随机偏移（模拟真实航行）
            lng += random.uniform(-0.01, 0.01)
            lat += random.uniform(-0.01, 0.01)

            # 计算速度和航向
            speed = random.uniform(10, 18) if j < points_per_segment - 5 else random.uniform(2, 8)
            course = random.uniform(0, 360)
            heading = course + random.uniform(-5, 5)

            # 确定状态
            status = "underway using engine" if speed > 5 else random.choice(["at anchor", "moored"])

            track = {
                "imo_number": vessel["imo_number"],
                "vessel_name": vessel["vessel_name"],
                "mmsi": vessel["mmsi"],
                "timestamp": current_time,
                "position": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "speed": round(speed, 1),
                "course": round(course, 1),
                "heading": round(heading, 1),
                "status": status,
                "destination": route["waypoints"][-1],
                "draught": vessel["draught"],
                "ship_type": vessel["ship_type"],
                "flag": vessel["flag"],
                "created_at": datetime.utcnow()
            }

            tracks.append(track)
            current_time += timedelta(hours=1)

    return tracks


def main():
    print("=" * 80)
    print("生成AIS轨迹数据并导入MongoDB")
    print("=" * 80)

    # 连接MongoDB
    mongo_uri = (
        f"mongodb://{settings.mongo_user}:{settings.mongo_password}"
        f"@{settings.mongo_host}:{settings.mongo_port}"
        f"/{settings.mongo_db}?authSource={settings.mongo_auth_source}"
    )
    client = MongoClient(mongo_uri)
    db = client[settings.mongo_db]
    collection = db["ais_tracks"]

    # 清空现有数据
    print("\n清空现有数据...")
    collection.delete_many({})

    # 从PostgreSQL读取船舶列表
    print("\n从PostgreSQL读取船舶列表...")
    try:
        with db_conn("readonly") as conn:
            vessels_pg = query_all(
                conn,
                """
                SELECT id, vessel_name, imo_number, vessel_type, flag_state
                FROM vessels
                WHERE is_active = TRUE
                ORDER BY id
                LIMIT 100
                """,
                ()
            )
    except Exception as e:
        print(f"❌ 读取PostgreSQL失败: {e}")
        print("使用模拟船舶数据...")
        vessels_pg = []
        for i in range(100):
            vessels_pg.append({
                "id": i + 1,
                "vessel_name": f"VESSEL_{i+1:03d}",
                "imo_number": f"IMO{9000000 + i}",
                "vessel_type": random.choice(SHIP_TYPES),
                "flag_state": random.choice(FLAGS)
            })

    print(f"✅ 读取到 {len(vessels_pg)} 艘船舶")

    # 准备船舶数据
    vessels = []
    for v in vessels_pg:
        vessel = {
            "imo_number": v["imo_number"],
            "vessel_name": v["vessel_name"],
            "mmsi": f"{413000000 + random.randint(1, 999999)}",
            "ship_type": v.get("vessel_type", random.choice(SHIP_TYPES)),
            "flag": v.get("flag_state", random.choice(FLAGS)),
            "draught": round(random.uniform(8.0, 15.0), 1)
        }
        vessels.append(vessel)

    # 计算需要生成的数据量
    target_records = 2_000_000  # 200万条
    vessels_count = len(vessels)

    # 每艘船需要生成的轨迹点数
    records_per_vessel = target_records // vessels_count

    # 计算需要多少条航线（每条航线72小时，72个点）
    points_per_route = 72
    routes_per_vessel = (records_per_vessel + points_per_route - 1) // points_per_route

    print(f"\n数据生成计划：")
    print(f"  目标记录数: {target_records:,}")
    print(f"  船舶数量: {vessels_count}")
    print(f"  每艘船记录数: {records_per_vessel:,}")
    print(f"  每艘船航线数: {routes_per_vessel}")
    print(f"  每条航线点数: {points_per_route}")

    # 生成数据
    print(f"\n开始生成数据...")
    batch_size = 10000
    batch = []
    total_inserted = 0

    start_date = datetime.utcnow() - timedelta(days=90)  # 从90天前开始

    for vessel_idx, vessel in enumerate(vessels):
        print(f"\n处理船舶 {vessel_idx + 1}/{vessels_count}: {vessel['vessel_name']}")

        current_time = start_date

        for route_idx in range(routes_per_vessel):
            # 随机选择一条航线
            route = random.choice(ROUTES)

            # 生成该航线的轨迹
            tracks = generate_vessel_track(vessel, route, current_time, hours=points_per_route)

            batch.extend(tracks)
            current_time = tracks[-1]["timestamp"] + timedelta(hours=1)

            # 批量插入
            if len(batch) >= batch_size:
                collection.insert_many(batch)
                total_inserted += len(batch)
                print(f"  已插入 {total_inserted:,} 条记录 ({total_inserted/target_records*100:.1f}%)")
                batch = []

    # 插入剩余数据
    if batch:
        collection.insert_many(batch)
        total_inserted += len(batch)

    print(f"\n✅ 数据生成完成！总计插入 {total_inserted:,} 条记录")

    # 创建索引
    print("\n创建索引...")
    collection.create_index([("position", "2dsphere")])
    print("  ✅ 地理空间索引: position (2dsphere)")

    collection.create_index([("imo_number", ASCENDING), ("timestamp", DESCENDING)])
    print("  ✅ 复合索引: imo_number + timestamp")

    collection.create_index([("timestamp", DESCENDING)])
    print("  ✅ 时间索引: timestamp")

    collection.create_index([("vessel_name", ASCENDING)])
    print("  ✅ 船名索引: vessel_name")

    # 统计信息
    print("\n数据统计：")
    total_count = collection.count_documents({})
    print(f"  总记录数: {total_count:,}")

    vessel_count = len(collection.distinct("imo_number"))
    print(f"  船舶数量: {vessel_count}")

    # 时间范围
    oldest = collection.find_one(sort=[("timestamp", ASCENDING)])
    newest = collection.find_one(sort=[("timestamp", DESCENDING)])
    if oldest and newest:
        print(f"  时间范围: {oldest['timestamp']} ~ {newest['timestamp']}")

    # 数据库大小
    stats = db.command("collstats", "ais_tracks")
    size_mb = stats["size"] / (1024 * 1024)
    print(f"  数据大小: {size_mb:.2f} MB")

    print("\n" + "=" * 80)
    print("✅ AIS轨迹数据生成完成！")
    print("=" * 80)

    client.close()


if __name__ == "__main__":
    main()
