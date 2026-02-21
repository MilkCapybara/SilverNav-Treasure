#!/usr/bin/env python3
"""
Spark作业：MongoDB → HDFS数据归档
将MongoDB中超过90天的历史AIS数据归档到HDFS
"""
import os
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, dayofmonth


def env(name: str, default: str | None = None) -> str:
    """获取环境变量"""
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing env var: {name}")
    return value


def main():
    """主函数"""
    print("=" * 80)
    print("Spark作业：MongoDB → HDFS数据归档")
    print("=" * 80)

    # MongoDB连接配置
    mongo_host = env("SILVERNAV_MONGO_HOST", "1.15.225.134")
    mongo_port = env("SILVERNAV_MONGO_PORT", "27017")
    mongo_db = env("SILVERNAV_MONGO_DB", "silvernav")
    mongo_user = env("SILVERNAV_MONGO_USER", "admin")
    mongo_password = env("SILVERNAV_MONGO_PASSWORD", "sun2137405")
    mongo_auth_source = env("SILVERNAV_MONGO_AUTH_SOURCE", "admin")

    # HDFS配置
    hdfs_base = env("HDFS_BASE", "hdfs:///silvernav/archive")

    # 构建MongoDB连接URI
    mongo_uri = (
        f"mongodb://{mongo_user}:{mongo_password}"
        f"@{mongo_host}:{mongo_port}"
        f"/{mongo_db}.ais_tracks?authSource={mongo_auth_source}"
    )

    # 创建Spark会话
    spark = SparkSession.builder \
        .appName("MongoDB-to-HDFS-Archive") \
        .config("spark.mongodb.read.connection.uri", mongo_uri) \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .getOrCreate()

    print("\n✅ Spark会话创建成功")

    # 计算截止日期（90天前）
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    print(f"\n📅 归档截止日期: {cutoff_date}")

    # 读取MongoDB中的AIS轨迹数据
    print("\n📊 读取AIS轨迹数据...")
    ais_df = spark.read.format("mongodb").load()

    total_records = ais_df.count()
    print(f"✅ 读取到 {total_records:,} 条轨迹记录")

    # 过滤超过90天的历史数据
    print(f"\n🔍 筛选超过90天的历史数据...")
    old_data = ais_df.filter(col("timestamp") < cutoff_date)

    old_records = old_data.count()
    print(f"✅ 找到 {old_records:,} 条历史记录 ({old_records/total_records*100:.1f}%)")

    if old_records > 0:
        # 添加分区字段
        print("\n📁 添加分区字段...")
        partitioned_data = old_data \
            .withColumn("year", year("timestamp")) \
            .withColumn("month", month("timestamp")) \
            .withColumn("day", dayofmonth("timestamp"))

        # 写入HDFS（Parquet格式，按日期分区）
        print(f"\n💾 写入HDFS: {hdfs_base}/ais_tracks")
        partitioned_data.write \
            .partitionBy("year", "month", "day") \
            .mode("append") \
            .parquet(f"{hdfs_base}/ais_tracks")

        print("✅ 数据已归档到HDFS")

        # 显示分区信息
        print("\n📊 分区统计：")
        partition_stats = partitioned_data.groupBy("year", "month", "day").count() \
            .orderBy("year", "month", "day")
        partition_stats.show(20, truncate=False)

    else:
        print("\n⚠️  没有需要归档的历史数据")

    print("\n" + "=" * 80)
    print("✅ 归档作业执行完成！")
    print("=" * 80)

    spark.stop()


if __name__ == "__main__":
    main()
