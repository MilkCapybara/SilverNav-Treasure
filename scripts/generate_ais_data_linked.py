#!/usr/bin/env python3
"""
生成AIS轨迹数据（与PostgreSQL船舶数据关联）
目标：200万条轨迹记录，使用PostgreSQL中的真实船舶数据
包含异常值（位置漂移、速度异常、航向突变等）用于Spark分析
"""
import argparse
import random
import sys
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient, ASCENDING, DESCENDING

# ==================== 配置参数（请根据实际情况调整）====================
# PostgreSQL 连接信息
PG_HOST = "1.15.225.134"
PG_PORT = 5432
PG_DATABASE = "silvernav_db"          # 请替换为实际数据库名
PG_USER = "postgres"
PG_PASSWORD = "sun2137405"

# MongoDB 连接信息
MONGO_HOST = "1.15.225.134"
MONGO_PORT = 27017
MONGO_DATABASE = "silvernav"
MONGO_USER = "admin"
MONGO_PASSWORD = "sun2137405"
MONGO_AUTH_SOURCE = "admin"        # 认证数据库

# 目标记录数
TARGET_RECORDS = 2_000_000

# 异常值注入概率 (0~1)
ABNORMAL_PROB = 0.02                # 2% 的点被注入异常
# ====================================================================

# 航线模板（与原始脚本一致）
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

VESSEL_STATUS = [
    "underway using engine",
    "at anchor",
    "not under command",
    "restricted manoeuvrability",
    "moored"
]


def interpolate_position(start, end, ratio):
    """在两个坐标点之间线性插值"""
    lng1, lat1 = start
    lng2, lat2 = end
    lng = lng1 + (lng2 - lng1) * ratio
    lat = lat1 + (lat2 - lat1) * ratio
    return (lng, lat)


def inject_anomaly(track_point):
    """
    对单个轨迹点注入异常值（直接修改传入的字典）
    异常类型包括：
      - 位置漂移（离群点）
      - 速度异常（极高/负值）
      - 航向异常（突变或超出0-360）
      - 状态字符串异常
      - 时间戳跳跃（后面整体处理）
    """
    r = random.random()
    if r < 0.25:  # 位置漂移：将坐标偏移到远离航线的地方
        track_point["longitude"] += random.uniform(-5, 5)
        track_point["latitude"] += random.uniform(-5, 5)
        # 更新 GeoJSON 坐标
        track_point["position"]["coordinates"] = [track_point["longitude"], track_point["latitude"]]
    elif r < 0.5:  # 速度异常
        if random.random() < 0.5:
            track_point["speed"] = random.uniform(30, 50)   # 超高速
        else:
            track_point["speed"] = random.uniform(-5, -1)   # 负速度
    elif r < 0.75:  # 航向异常
        track_point["course"] = random.uniform(400, 720)    # 超出正常范围
        track_point["heading"] = track_point["course"] + random.uniform(-10, 10)
    else:  # 状态异常
        track_point["status"] = "abnormal status " + str(random.randint(1, 100))


def generate_vessel_track(vessel, route, start_time, hours=72):
    """为单艘船生成一条航线的轨迹，并随机注入异常"""
    tracks = []
    waypoints = route["waypoints"]

    total_points = hours
    points_per_segment = total_points // (len(waypoints) - 1)

    current_time = start_time

    for i in range(len(waypoints) - 1):
        start_point = waypoints[i]
        end_point = waypoints[i + 1]

        for j in range(points_per_segment):
            ratio = j / points_per_segment
            lng, lat = interpolate_position(start_point, end_point, ratio)

            # 添加随机微小偏移（模拟正常波动）
            lng += random.uniform(-0.01, 0.01)
            lat += random.uniform(-0.01, 0.01)

            # 计算速度和航向（正常范围）
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
                "latitude": lat,
                "longitude": lng,
                "speed": round(speed, 1),
                "course": round(course, 1),
                "heading": round(heading, 1),
                "status": status,
                "destination": route["name"].split("-")[-1],
                "draught": vessel["draught"],
                "ship_type": vessel["ship_type"],
                "flag": vessel["flag"],
                "created_at": datetime.utcnow()
            }

            # 以一定概率注入异常
            if random.random() < ABNORMAL_PROB:
                inject_anomaly(track)

            tracks.append(track)
            current_time += timedelta(hours=1)

    return tracks


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='生成AIS轨迹数据（与PostgreSQL关联）')
    parser.add_argument('--clear', action='store_true',
                        help='清空MongoDB中的现有数据（默认不清空）')
    args = parser.parse_args()

    print("=" * 80)
    print("生成AIS轨迹数据（与PostgreSQL关联）- 含异常值")
    print("=" * 80)

    # 连接MongoDB
    print("\n连接MongoDB...")
    mongo_uri = (
        f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}"
        f"@{MONGO_HOST}:{MONGO_PORT}"
        f"/{MONGO_DATABASE}?authSource={MONGO_AUTH_SOURCE}"
    )
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client[MONGO_DATABASE]
    collection = mongo_db["ais_tracks"]
    print(f"✅ MongoDB连接成功: {MONGO_HOST}:{MONGO_PORT}")

    # 连接PostgreSQL
    print("\n连接PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            cursor_factory=RealDictCursor
        )
        print(f"✅ PostgreSQL连接成功: {PG_HOST}:{PG_PORT}")

        # 读取船舶列表（请根据实际表结构调整字段名）
        print("\n从PostgreSQL读取船舶列表...")
        cursor = pg_conn.cursor()
        cursor.execute("""
            SELECT
                id,
                vessel_name,
                imo_number,
                vessel_type,
                flag_country,
                build_year
            FROM silvernav.vessels
            WHERE is_active = TRUE
            ORDER BY id
            LIMIT 200          -- 增加船舶数量以满足200万条记录
        """)
        vessels_pg = cursor.fetchall()
        cursor.close()
        pg_conn.close()

        print(f"✅ 读取到 {len(vessels_pg)} 艘船舶")

        # 显示前3艘船舶
        print("\n船舶样例:")
        for v in vessels_pg[:3]:
            print(f"  - {v['vessel_name']} ({v['imo_number']}) - {v['vessel_type']}")

    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        print("程序终止。请检查PostgreSQL连接配置。")
        return

    # 准备船舶数据（补充生成mmsi和draught）
    vessels = []
    for v in vessels_pg:
        vessel = {
            "imo_number": v["imo_number"],
            "vessel_name": v["vessel_name"],
            "mmsi": f"413{random.randint(100000, 999999)}",  # 生成9位MMSI
            "ship_type": v["vessel_type"],
            "flag": v["flag_country"] or "CN",
            "draught": round(random.uniform(8.0, 15.0), 1)
        }
        vessels.append(vessel)

    # 计算数据生成计划
    vessels_count = len(vessels)
    records_per_vessel = TARGET_RECORDS // vessels_count
    points_per_route = 72  # 每条航线生成72个点（3天每小时一个点）
    routes_per_vessel = (records_per_vessel + points_per_route - 1) // points_per_route

    print(f"\n数据生成计划：")
    print(f"  目标记录数: {TARGET_RECORDS:,}")
    print(f"  船舶数量: {vessels_count}")
    print(f"  每艘船记录数: {records_per_vessel:,}")
    print(f"  每艘船航线数: {routes_per_vessel}")
    print(f"  每条航线点数: {points_per_route}")
    print(f"  异常值注入概率: {ABNORMAL_PROB*100:.1f}%")

    # 处理现有数据
    existing_count = collection.count_documents({})
    print(f"\n当前MongoDB中已有 {existing_count:,} 条记录")

    if existing_count > 0:
        if args.clear:
            print("⚠️  检测到 --clear 参数，正在清空现有数据...")
            collection.delete_many({})
            print("✅ 数据已清空")
        else:
            print("⚠️  检测到现有数据，将追加新数据")
            print("   如需清空现有数据，请使用 --clear 参数运行")
            print("   示例: python3 generate_ais_data_linked.py --clear")

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
                print(f"  已插入 {total_inserted:,} 条记录 ({total_inserted/TARGET_RECORDS*100:.1f}%)")
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

    collection.create_index([("ship_type", ASCENDING)])
    print("  ✅ 船型索引: ship_type")

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
    stats = mongo_db.command("collstats", "ais_tracks")
    size_mb = stats["size"] / (1024 * 1024)
    print(f"  数据大小: {size_mb:.2f} MB")

    # 显示数据样例（含异常）
    print("\n数据样例（前5条，可能包含异常）:")
    for doc in collection.find().limit(5):
        print(f"  - {doc['vessel_name']} ({doc['imo_number']})")
        print(f"    时间: {doc['timestamp']}, 位置: ({doc['longitude']:.4f}, {doc['latitude']:.4f})")
        print(f"    速度: {doc['speed']}节, 航向: {doc['course']}, 状态: {doc['status']}")

    print("\n" + "=" * 80)
    print("✅ AIS轨迹数据生成完成！")
    print("=" * 80)
    print("\n下一步建议:")
    print("1. 在Spark环境中连接MongoDB进行数据分析")
    print("2. 可重点关注速度异常、位置离群、航向超范围等字段")
    print("3. 如有需要，可调整异常注入概率重新生成")

    mongo_client.close()


if __name__ == "__main__":
    main()