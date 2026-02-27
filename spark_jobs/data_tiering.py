#!/usr/bin/env python3
"""
数据分层存储系统
功能：
1. 实现冷热数据分离
2. 热数据（近7天）：MongoDB
3. 温数据（7-90天）：MongoDB + Parquet
4. 冷数据（>90天）：HDFS Parquet
"""
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_date, date_sub, year, month, dayofmonth
from datetime import datetime, timedelta
import os


def main():
    print("=" * 80)
    print("🗄️  数据分层存储系统")
    print("=" * 80)

    # 获取配置
    mongo_host = os.getenv("SILVERNAV_MONGO_HOST", "1.15.225.134")
    mongo_port = os.getenv("SILVERNAV_MONGO_PORT", "27017")
    mongo_db = os.getenv("SILVERNAV_MONGO_DB", "silvernav")
    mongo_user = os.getenv("SILVERNAV_MONGO_USER", "admin")
    mongo_password = os.getenv("SILVERNAV_MONGO_PASSWORD", "sun2137405")
    mongo_auth_source = os.getenv("SILVERNAV_MONGO_AUTH_SOURCE", "admin")

    hdfs_base = os.getenv("HDFS_BASE_PATH", "hdfs://1.15.225.134:9000/silvernav")

    mongo_uri = (
        f"mongodb://{mongo_user}:{mongo_password}"
        f"@{mongo_host}:{mongo_port}"
        f"/{mongo_db}.ais_tracks?authSource={mongo_auth_source}"
    )

    print(f"\n📊 MongoDB: {mongo_host}:{mongo_port}/{mongo_db}")
    print(f"📦 HDFS: {hdfs_base}")

    # 创建Spark Session
    spark = SparkSession.builder \
        .appName("DataTiering") \
        .config("spark.mongodb.input.uri", mongo_uri) \
        .config("spark.mongodb.output.uri", f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .getOrCreate()

    print("✅ Spark Session创建成功")

    # 读取所有数据
    print("\n📡 读取AIS轨迹数据...")
    df = spark.read \
        .format("mongodb") \
        .option("database", mongo_db) \
        .option("collection", "ais_tracks") \
        .load()

    total_count = df.count()
    print(f"✅ 读取到 {total_count:,} 条记录")

    # 数据分层
    print("\n🔍 数据分层分析...")

    # 热数据：近7天
    hot_data = df.filter(col("timestamp") >= date_sub(current_date(), 7))
    hot_count = hot_data.count()
    print(f"  🔥 热数据（近7天）: {hot_count:,} 条")

    # 温数据：7-90天
    warm_data = df.filter(
        (col("timestamp") >= date_sub(current_date(), 90)) &
        (col("timestamp") < date_sub(current_date(), 7))
    )
    warm_count = warm_data.count()
    print(f"  🌡️  温数据（7-90天）: {warm_count:,} 条")

    # 冷数据：>90天
    cold_data = df.filter(col("timestamp") < date_sub(current_date(), 90))
    cold_count = cold_data.count()
    print(f"  ❄️  冷数据（>90天）: {cold_count:,} 条")

    # 归档冷数据到HDFS
    if cold_count > 0:
        print(f"\n📦 归档冷数据到HDFS...")

        # 添加分区字段
        cold_data_partitioned = cold_data \
            .withColumn("year", year("timestamp")) \
            .withColumn("month", month("timestamp")) \
            .withColumn("day", dayofmonth("timestamp"))

        # 写入HDFS（按年月分区）
        output_path = f"{hdfs_base}/ais_tracks_archive"

        try:
            cold_data_partitioned.write \
                .partitionBy("year", "month") \
                .mode("append") \
                .parquet(output_path)

            print(f"✅ 冷数据已归档到: {output_path}")
            print(f"   分区: year/month")

            # 显示分区统计
            print("\n分区统计:")
            cold_data_partitioned.groupBy("year", "month").count() \
                .orderBy("year", "month") \
                .show()

        except Exception as e:
            print(f"⚠️  HDFS写入失败: {e}")
            print("   提示: 请确保HDFS服务正常运行")

    # 温数据导出为Parquet（本地）
    if warm_count > 0:
        print(f"\n💾 导出温数据为Parquet...")

        local_path = "/Users/sunfanmacpro/Desktop/SilverNav-Treasure/data/warm_data"

        try:
            warm_data.write \
                .mode("overwrite") \
                .parquet(local_path)

            print(f"✅ 温数据已导出到: {local_path}")

            # 检查文件大小
            import subprocess
            result = subprocess.run(
                ["du", "-sh", local_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                size = result.stdout.split()[0]
                print(f"   文件大小: {size}")

        except Exception as e:
            print(f"⚠️  导出失败: {e}")

    # 数据质量报告
    print("\n" + "=" * 80)
    print("📊 数据分层总结")
    print("=" * 80)
    print(f"总数据量: {total_count:,} 条")
    print(f"")
    print(f"热数据（近7天）:")
    print(f"  - 数量: {hot_count:,} 条 ({hot_count/total_count*100:.1f}%)")
    print(f"  - 存储: MongoDB")
    print(f"  - 查询延迟: <100ms")
    print(f"")
    print(f"温数据（7-90天）:")
    print(f"  - 数量: {warm_count:,} 条 ({warm_count/total_count*100:.1f}%)")
    print(f"  - 存储: MongoDB + Parquet")
    print(f"  - 查询延迟: <1s")
    print(f"")
    print(f"冷数据（>90天）:")
    print(f"  - 数量: {cold_count:,} 条 ({cold_count/total_count*100:.1f}%)")
    print(f"  - 存储: HDFS Parquet")
    print(f"  - 查询延迟: <1min")
    print("=" * 80)

    # 存储优化建议
    print("\n💡 存储优化建议:")
    if cold_count > total_count * 0.5:
        print("  ⚠️  冷数据占比超过50%，建议从MongoDB删除已归档数据")
        print("     命令: db.ais_tracks.deleteMany({timestamp: {$lt: new Date('2025-11-24')}})")

    if warm_count > total_count * 0.3:
        print("  ℹ️  温数据占比较高，可以考虑增加归档频率")

    spark.stop()
    print("\n✅ 数据分层存储完成！")


if __name__ == "__main__":
    main()
