#!/bin/bash
# 运行Spark轨迹分析作业
# 预计耗时：10-20分钟

echo "=========================================="
echo "运行Spark AIS轨迹分析作业"
echo "=========================================="
echo ""
echo "开始时间: $(date)"
echo ""

cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

# 设置环境变量
export SILVERNAV_MONGO_HOST=1.15.225.134
export SILVERNAV_MONGO_PORT=27017
export SILVERNAV_MONGO_DB=silvernav
export SILVERNAV_MONGO_USER=admin
export SILVERNAV_MONGO_PASSWORD=sun2137405
export SILVERNAV_MONGO_AUTH_SOURCE=admin

# 检查Spark是否安装
if ! command -v spark-submit &> /dev/null; then
    echo "❌ Spark未安装或未配置到PATH"
    echo "请先安装Spark 3.5.1或配置SPARK_HOME环境变量"
    exit 1
fi

echo "✅ Spark已安装: $(spark-submit --version 2>&1 | head -n 1)"
echo ""

# 运行Spark作业
spark-submit \
  --master local[*] \
  --driver-memory 4g \
  --executor-memory 4g \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
  spark_jobs/ais_trajectory_analysis.py

echo ""
echo "完成时间: $(date)"
echo "=========================================="
