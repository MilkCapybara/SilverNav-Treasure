#!/usr/bin/env python3
"""
Spark作业：AIS轨迹数据分析
从MongoDB读取AIS轨迹数据，进行聚合分析，结果写回MongoDB
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, avg, max, min, sum as fsum,
    unix_timestamp, lag, abs as fabs, sqrt, pow as fpow
)
from pyspark.sql.window import Window


def env(name: str, default: str | None = None) -> str:
    """获取环境变量"""
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing env var: {name}")
    return value


def calculate_distance(lat1, lon1, lat2, lon2):
    """计算两点之间的距离（简化版，单位：海里）"""
    # 使用Haversine公式的简化版本
    # 1度纬度 ≈ 60海里
    dlat = fabs(lat2 - lat1) * 60
    dlon = fabs(lon2 - lon1) * 60 * 0.866  # cos(30°) 近似
    return sqrt(fpow(dlat, 2) + fpow(dlon, 2))


def main():
    """主函数"""
    print("=" * 80)
    print("Spark作业：AIS轨迹数据分析")
    print("=" * 80)

    # MongoDB连接配置
    mongo_host = env("SILVERNAV_MONGO_HOST", "1.15.225.134")
    mongo_port = env("SILVERNAV_MONGO_PORT", "27017")
    mongo_db = env("SILVERNAV_MONGO_DB", "silvernav")
    mongo_user = env("SILVERNAV_MONGO_USER", "admin")
    mongo_password = env("SILVERNAV_MONGO_PASSWORD", "sun2137405")
    mongo_auth_source = env("SILVERNAV_MONGO_AUTH_SOURCE", "admin")

    # 构建MongoDB连接URI
    mongo_uri = (
        f"mongodb://{mongo_user}:{mongo_password}"
        f"@{mongo_host}:{mongo_port}"
        f"/{mongo_db}.ais_tracks?authSource={mongo_auth_source}"
    )

    # 创建Spark会话
    spark = SparkSession.builder \
        .appName("AIS-Trajectory-Analysis") \
        .config("spark.mongodb.read.connection.uri", mongo_uri) \
        .config("spark.mongodb.write.connection.uri",
                f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}.vessel_statistics?authSource={mongo_auth_source}") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .getOrCreate()

    print("\n✅ Spark会话创建成功")

    # 1. 读取MongoDB中的AIS轨迹数据
    print("\n📊 读取AIS轨迹数据...")
    ais_df = spark.read.format("mongodb").load()

    total_records = ais_df.count()
    print(f"✅ 读取到 {total_records:,} 条轨迹记录")

    # 2. 数据清洗：过滤异常数据
    print("\n🧹 数据清洗...")
    clean_df = ais_df.filter(
        (col("speed") >= 0) & (col("speed") <= 30) &
        (col("position.coordinates").isNotNull())
    )

    clean_records = clean_df.count()
    print(f"✅ 清洗后保留 {clean_records:,} 条记录 ({clean_records/total_records*100:.1f}%)")

    # 3. 按船舶聚合统计
    print("\n📈 按船舶聚合统计...")
    vessel_stats = clean_df.groupBy("imo_number", "vessel_name", "ship_type", "flag").agg(
        count("*").alias("track_count"),
        avg("speed").alias("avg_speed"),
        max("speed").alias("max_speed"),
        min("speed").alias("min_speed"),
        min("timestamp").alias("first_seen"),
        max("timestamp").alias("last_seen")
    )

    vessel_count = vessel_stats.count()
    print(f"✅ 统计了 {vessel_count} 艘船舶")

    # 显示前10条统计结果
    print("\n前10艘船舶统计：")
    vessel_stats.show(10, truncate=False)

    # 4. 写回MongoDB
    print("\n💾 写入统计结果到MongoDB...")
    vessel_stats.write.format("mongodb") \
        .mode("overwrite") \
        .option("collection", "vessel_statistics") \
        .save()

    print("✅ 统计结果已写入 vessel_statistics 集合")

    # 5. 异常停泊检测
    print("\n🔍 异常停泊检测...")

    # 按船舶和时间排序
    window = Window.partitionBy("imo_number").orderBy("timestamp")

    # 计算相邻两点的时间差
    df_with_lag = clean_df.withColumn("prev_timestamp", lag("timestamp").over(window)) \
                           .withColumn("prev_speed", lag("speed").over(window))

    # 计算时间差（秒）
    df_with_time_diff = df_with_lag.withColumn(
        "time_diff_hours",
        (unix_timestamp("timestamp") - unix_timestamp("prev_timestamp")) / 3600
    )

    # 检测异常停泊：速度<1节且持续时间>24小时
    anomalies = df_with_time_diff.filter(
        (col("speed") < 1) &
        (col("prev_speed") < 1) &
        (col("time_diff_hours") > 24)
    ).select(
        "imo_number",
        "vessel_name",
        "timestamp",
        "position",
        "speed",
        "status",
        "time_diff_hours"
    )

    anomaly_count = anomalies.count()
    print(f"✅ 检测到 {anomaly_count} 次异常停泊")

    if anomaly_count > 0:
        print("\n前10次异常停泊：")
        anomalies.show(10, truncate=False)

        # 写入MongoDB
        print("\n💾 写入异常停泊记录到MongoDB...")
        anomalies.write.format("mongodb") \
            .mode("overwrite") \
            .option("collection", "ais_anomalies") \
            .save()

        print("✅ 异常停泊记录已写入 ais_anomalies 集合")

    # 6. 按船舶类型统计
    print("\n📊 按船舶类型统计...")
    type_stats = clean_df.groupBy("ship_type").agg(
        count("*").alias("track_count"),
        avg("speed").alias("avg_speed")
    ).orderBy(col("track_count").desc())

    print("\n船舶类型统计：")
    type_stats.show(truncate=False)

    # 7. 按国旗统计
    print("\n🏴 按国旗统计...")
    flag_stats = clean_df.groupBy("flag").agg(
        count("*").alias("track_count"),
        avg("speed").alias("avg_speed")
    ).orderBy(col("track_count").desc())

    print("\n国旗统计：")
    flag_stats.show(truncate=False)

    # 8. 按状态统计
    print("\n⚓ 按状态统计...")
    status_stats = clean_df.groupBy("status").agg(
        count("*").alias("track_count")
    ).orderBy(col("track_count").desc())

    print("\n状态统计：")
    status_stats.show(truncate=False)

    print("\n" + "=" * 80)
    print("✅ Spark作业执行完成！")
    print("=" * 80)

    spark.stop()


if __name__ == "__main__":
    main()
