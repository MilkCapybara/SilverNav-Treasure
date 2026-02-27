#!/usr/bin/env python3
"""
Spark Streaming实时异常检测系统
功能：
1. 实时监控船舶轨迹数据
2. 检测速度异常、航向异常、区域异常、停泊异常
3. 实时告警并存储到MongoDB
"""
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    window, avg, stddev, count, col, abs as spark_abs,
    when, lit, current_timestamp, udf
)
from pyspark.sql.types import StringType, DoubleType
import os

# 高风险区域定义（经纬度范围）
HIGH_RISK_AREAS = [
    {"name": "索马里海域", "min_lng": 40.0, "max_lng": 55.0, "min_lat": 0.0, "max_lat": 15.0},
    {"name": "马六甲海峡", "min_lng": 100.0, "max_lng": 105.0, "min_lat": 1.0, "max_lat": 6.0},
    {"name": "几内亚湾", "min_lng": -5.0, "max_lng": 10.0, "min_lat": -5.0, "max_lat": 5.0}
]


def check_high_risk_area(lng, lat):
    """检查是否在高风险区域"""
    for area in HIGH_RISK_AREAS:
        if (area["min_lng"] <= lng <= area["max_lng"] and
            area["min_lat"] <= lat <= area["max_lat"]):
            return area["name"]
    return "safe"


def main():
    print("=" * 80)
    print("🚀 Spark Streaming实时异常检测系统")
    print("=" * 80)

    # 获取MongoDB连接信息
    mongo_host = os.getenv("SILVERNAV_MONGO_HOST", "1.15.225.134")
    mongo_port = os.getenv("SILVERNAV_MONGO_PORT", "27017")
    mongo_db = os.getenv("SILVERNAV_MONGO_DB", "silvernav")
    mongo_user = os.getenv("SILVERNAV_MONGO_USER", "admin")
    mongo_password = os.getenv("SILVERNAV_MONGO_PASSWORD", "sun2137405")
    mongo_auth_source = os.getenv("SILVERNAV_MONGO_AUTH_SOURCE", "admin")

    mongo_uri = (
        f"mongodb://{mongo_user}:{mongo_password}"
        f"@{mongo_host}:{mongo_port}"
        f"/{mongo_db}.ais_tracks?authSource={mongo_auth_source}"
    )

    print(f"\n📊 MongoDB连接: {mongo_host}:{mongo_port}/{mongo_db}")

    # 创建Spark Session
    spark = SparkSession.builder \
        .appName("RealTimeAnomalyDetection") \
        .config("spark.mongodb.input.uri", mongo_uri) \
        .config("spark.mongodb.output.uri", f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .getOrCreate()

    print("✅ Spark Session创建成功")

    # 读取流数据（模拟：从MongoDB读取最近的数据）
    print("\n📡 读取AIS轨迹数据...")

    # 注意：真实的流式处理需要配置MongoDB Change Streams
    # 这里使用批处理模式演示异常检测逻辑
    df = spark.read \
        .format("mongodb") \
        .option("database", mongo_db) \
        .option("collection", "ais_tracks") \
        .load()

    print(f"✅ 读取到 {df.count():,} 条记录")

    # 注册UDF
    check_area_udf = udf(check_high_risk_area, StringType())

    # 1. 速度异常检测
    print("\n🔍 检测速度异常...")
    speed_anomalies = df.groupBy("imo_number", "vessel_name") \
        .agg(
            avg("speed").alias("avg_speed"),
            stddev("speed").alias("speed_stddev"),
            count("*").alias("point_count")
        ) \
        .withColumn(
            "speed_anomaly_score",
            when(col("speed_stddev") > 5.0, lit("high"))
            .when(col("speed_stddev") > 3.0, lit("medium"))
            .otherwise(lit("low"))
        ) \
        .filter(col("speed_anomaly_score") != "low")

    speed_anomaly_count = speed_anomalies.count()
    print(f"  发现 {speed_anomaly_count} 艘船舶存在速度异常")

    # 2. 停泊异常检测（速度<1节持续时间长）
    print("\n⚓ 检测停泊异常...")
    from pyspark.sql.window import Window
    from pyspark.sql.functions import lag, unix_timestamp

    window_spec = Window.partitionBy("imo_number").orderBy("timestamp")

    anchor_df = df.filter(col("speed") < 1.0) \
        .withColumn("prev_timestamp", lag("timestamp").over(window_spec)) \
        .withColumn(
            "time_diff_hours",
            (unix_timestamp("timestamp") - unix_timestamp("prev_timestamp")) / 3600
        ) \
        .filter(col("time_diff_hours") > 24)  # 停泊超过24小时

    anchor_anomaly_count = anchor_df.count()
    print(f"  发现 {anchor_anomaly_count} 次异常停泊（>24小时）")

    # 3. 高风险区域检测
    print("\n🌍 检测高风险区域...")

    # 提取经纬度
    df_with_coords = df.withColumn("longitude", col("position.coordinates").getItem(0)) \
        .withColumn("latitude", col("position.coordinates").getItem(1))

    # 检查高风险区域
    risk_area_df = df_with_coords.withColumn(
        "risk_area",
        check_area_udf(col("longitude"), col("latitude"))
    ).filter(col("risk_area") != "safe")

    risk_area_count = risk_area_df.count()
    print(f"  发现 {risk_area_count} 次进入高风险区域")

    # 4. 航向异常检测（频繁转向）
    print("\n🧭 检测航向异常...")
    course_anomalies = df.groupBy("imo_number", "vessel_name") \
        .agg(
            stddev("course").alias("course_stddev"),
            count("*").alias("point_count")
        ) \
        .withColumn(
            "course_anomaly_score",
            when(col("course_stddev") > 60.0, lit("high"))
            .when(col("course_stddev") > 40.0, lit("medium"))
            .otherwise(lit("low"))
        ) \
        .filter(col("course_anomaly_score") != "low")

    course_anomaly_count = course_anomalies.count()
    print(f"  发现 {course_anomaly_count} 艘船舶存在航向异常")

    # 5. 综合异常评分
    print("\n📊 生成综合异常报告...")

    # 合并所有异常
    comprehensive_anomalies = df.groupBy("imo_number", "vessel_name", "ship_type") \
        .agg(
            avg("speed").alias("avg_speed"),
            stddev("speed").alias("speed_stddev"),
            stddev("course").alias("course_stddev"),
            count("*").alias("total_points")
        ) \
        .withColumn(
            "anomaly_score",
            (
                when(col("speed_stddev") > 5.0, lit(30)).otherwise(lit(0)) +
                when(col("course_stddev") > 60.0, lit(30)).otherwise(lit(0)) +
                when(col("avg_speed") < 2.0, lit(20)).otherwise(lit(0))
            )
        ) \
        .withColumn(
            "risk_level",
            when(col("anomaly_score") >= 50, lit("high"))
            .when(col("anomaly_score") >= 30, lit("medium"))
            .otherwise(lit("low"))
        ) \
        .filter(col("anomaly_score") > 0) \
        .withColumn("detection_time", current_timestamp()) \
        .withColumn("anomaly_type", lit("综合异常"))

    # 显示异常统计
    print("\n异常统计:")
    comprehensive_anomalies.groupBy("risk_level").count().show()

    # 显示高风险船舶
    print("\n高风险船舶（Top 10）:")
    comprehensive_anomalies.filter(col("risk_level") == "high") \
        .orderBy(col("anomaly_score").desc()) \
        .select("vessel_name", "imo_number", "ship_type", "anomaly_score", "avg_speed", "speed_stddev") \
        .show(10, truncate=False)

    # 6. 保存异常记录到MongoDB
    print("\n💾 保存异常记录到MongoDB...")

    output_collection = "realtime_anomalies"

    try:
        comprehensive_anomalies.write \
            .format("mongodb") \
            .mode("append") \
            .option("database", mongo_db) \
            .option("collection", output_collection) \
            .save()

        print(f"✅ 异常记录已保存到 {output_collection} 集合")
    except Exception as e:
        print(f"⚠️  保存失败: {e}")

    # 统计总结
    print("\n" + "=" * 80)
    print("📊 异常检测总结")
    print("=" * 80)
    print(f"速度异常: {speed_anomaly_count} 艘船舶")
    print(f"停泊异常: {anchor_anomaly_count} 次")
    print(f"高风险区域: {risk_area_count} 次")
    print(f"航向异常: {course_anomaly_count} 艘船舶")
    print(f"综合异常: {comprehensive_anomalies.count()} 艘船舶")
    print("=" * 80)

    spark.stop()
    print("\n✅ 实时异常检测完成！")


if __name__ == "__main__":
    main()
