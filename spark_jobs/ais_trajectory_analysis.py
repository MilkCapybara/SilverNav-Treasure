#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import DoubleType
from pyspark.sql.window import Window
import math

# ========== 创建 SparkSession（URI 已通过 --conf 传入）==========
spark = SparkSession.builder \
    .appName("AIS Trajectory Analysis") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

# 调试：打印从 SparkConf 获取的 URI
print("=== Spark 作业启动 ===")
print("spark.mongodb.input.uri =", spark.conf.get("spark.mongodb.input.uri", "未设置"))
print("spark.mongodb.output.uri =", spark.conf.get("spark.mongodb.output.uri", "未设置"))

# ========== 读取数据：只指定 database 和 collection，URI 来自 SparkConf ==========
print("正在从 MongoDB 读取数据...")
df = spark.read.format("mongodb") \
    .option("database", "silvernav") \
    .option("collection", "ais_tracks") \
    .load()

total_records = df.count()
print(f"✅ 读取到 {total_records} 条轨迹记录")

# ========== Haversine 距离函数 ==========
def haversine(lon1, lat1, lon2, lat2):
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

# ========== 写入 MongoDB：只指定 database 和 collection，URI 来自 SparkConf ==========
print("正在写入结果到 MongoDB...")
stats.write.format("mongodb") \
    .option("database", "silvernav") \
    .option("collection", "vessel_analysis") \
    .mode("overwrite") \
    .save()

print("✅ 分析结果已成功写入 MongoDB（silvernav.vessel_analysis）")
spark.stop()