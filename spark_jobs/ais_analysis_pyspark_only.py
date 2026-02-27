#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIS轨迹分析 - 纯PySpark版本（无需spark-submit）
适用于Mac本地环境，只需要安装pyspark包
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import DoubleType
from pyspark.sql.window import Window
import math
import os
os.environ["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@17"

# ==================== 配置参数 ====================
MONGO_HOST = "1.15.225.134"
MONGO_PORT = 27017
MONGO_USER = "admin"
MONGO_PASSWORD = "sun2137405"
MONGO_DATABASE = "silvernav"
MONGO_AUTH_SOURCE = "admin"

# MongoDB连接URI
INPUT_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}.ais_tracks?authSource={MONGO_AUTH_SOURCE}"
OUTPUT_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}.vessel_analysis?authSource={MONGO_AUTH_SOURCE}"

# Spark配置（适配Mac本地环境）
DRIVER_MEMORY = "4g"           # Mac通常有更多内存，可以设置大一点
EXECUTOR_MEMORY = "4g"
SHUFFLE_PARTITIONS = 8         # Mac性能更好，可以多一些分区
# ==================================================

print("=" * 80)
print("AIS轨迹分析 - 纯PySpark版本")
print("=" * 80)
print(f"\n配置信息:")
print(f"  MongoDB: {MONGO_HOST}:{MONGO_PORT}")
print(f"  数据库: {MONGO_DATABASE}")
print(f"  Driver内存: {DRIVER_MEMORY}")
print(f"  Executor内存: {EXECUTOR_MEMORY}")
print(f"  Shuffle分区数: {SHUFFLE_PARTITIONS}")
print()

# ========== 创建 SparkSession ==========
print("正在创建SparkSession...")
spark = SparkSession.builder \
    .appName("AIS Trajectory Analysis - PySpark Only") \
    .master("local[*]") \
    .config("spark.driver.memory", DRIVER_MEMORY) \
    .config("spark.executor.memory", EXECUTOR_MEMORY) \
    .config("spark.sql.shuffle.partitions", str(SHUFFLE_PARTITIONS)) \
    .config("spark.mongodb.input.uri", INPUT_URI) \
    .config("spark.mongodb.output.uri", OUTPUT_URI) \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
    .getOrCreate()

print("✅ SparkSession创建成功")
print(f"   Spark版本: {spark.version}")
print()

# ========== 读取数据 ==========
print("正在从MongoDB读取数据...")
print(f"连接URI: mongodb://{MONGO_USER}:***@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}.ais_tracks")
try:
    df = spark.read.format("mongodb") \
        .option("connection.uri", INPUT_URI) \
        .option("database", MONGO_DATABASE) \
        .option("collection", "ais_tracks") \
        .load()

    total_records = df.count()
    print(f"✅ 读取到 {total_records:,} 条轨迹记录")
except Exception as e:
    print(f"❌ 读取数据失败: {e}")
    print("\n可能的原因:")
    print("  1. MongoDB连接失败（检查网络和认证信息）")
    print("  2. mongo-spark-connector下载失败（首次运行需要下载jar包）")
    print("  3. 集合不存在或为空")
    spark.stop()
    exit(1)

# ========== Haversine 距离函数 ==========
def haversine(lon1, lat1, lon2, lat2):
    """计算两点间的球面距离（海里）"""
    # 处理NULL值
    if lon1 is None or lat1 is None or lon2 is None or lat2 is None:
        return 0.0

    R = 3440.065  # 地球半径（海里）
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

haversine_udf = udf(haversine, DoubleType())

# ========== 计算分段距离 ==========
print("正在计算分段距离...")
window_spec = Window.partitionBy("imo_number").orderBy("timestamp")
df_with_prev = df.withColumn("prev_longitude", lag("longitude", 1).over(window_spec)) \
                 .withColumn("prev_latitude", lag("latitude", 1).over(window_spec))

df_with_dist = df_with_prev.withColumn(
    "segment_distance",
    when(
        (col("prev_longitude").isNotNull()) & (col("prev_latitude").isNotNull()),
        haversine_udf(col("longitude"), col("latitude"), col("prev_longitude"), col("prev_latitude"))
    ).otherwise(0.0)
)

# ========== 聚合统计 ==========
print("正在聚合统计...")
stats = df_with_dist.groupBy("imo_number", "vessel_name", "ship_type", "flag") \
    .agg(
        count("*").alias("point_count"),
        min("timestamp").alias("first_seen"),
        max("timestamp").alias("last_seen"),
        avg("speed").alias("avg_speed"),
        max("speed").alias("max_speed"),
        stddev("speed").alias("stddev_speed"),
        sum("segment_distance").alias("total_distance_nm"),
        sum(expr("CASE WHEN speed > 30 OR speed < 0 OR course > 360 THEN 1 ELSE 0 END")).alias("anomaly_count")
    ) \
    .withColumn(
        "duration_hours",
        (col("last_seen").cast("long") - col("first_seen").cast("long")) / 3600
    )

print("\n=== 分析结果样例 ===")
stats.show(5, truncate=False)

# ========== 写入 MongoDB ==========
print("\n正在写入结果到 MongoDB...")
print(f"写入URI: mongodb://{MONGO_USER}:***@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}.vessel_analysis")
try:
    stats.write.format("mongodb") \
        .option("connection.uri", OUTPUT_URI) \
        .option("database", MONGO_DATABASE) \
        .option("collection", "vessel_analysis") \
        .mode("overwrite") \
        .save()

    print(f"✅ 分析结果已成功写入 MongoDB ({MONGO_DATABASE}.vessel_analysis)")
except Exception as e:
    print(f"❌ 写入失败: {e}")
    spark.stop()
    exit(1)

# ========== 统计信息 ==========
print("\n" + "=" * 80)
print("分析完成！统计信息:")
print("=" * 80)
result_count = stats.count()
print(f"  分析船舶数: {result_count}")
print(f"  输入记录数: {total_records:,}")
print(f"  输出集合: {MONGO_DATABASE}.vessel_analysis")
print("=" * 80)

spark.stop()
print("\n✅ 作业完成，SparkSession已关闭")
