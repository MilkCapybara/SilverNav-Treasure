#!/bin/bash
echo "=========================================="
echo "运行Spark AIS轨迹分析作业（结果写入MongoDB）"
echo "=========================================="
echo ""
echo "开始时间: $(date)"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PY_SCRIPT="$SCRIPT_DIR/ais_trajectory_analysis.py"

echo "项目根目录: $PROJECT_ROOT"
echo "Python脚本: $PY_SCRIPT"
echo ""

# 检查Python脚本是否存在
if [ ! -f "$PY_SCRIPT" ]; then
    echo "❌ 找不到Python脚本: $PY_SCRIPT"
    exit 1
fi

# 检查Spark
if ! command -v spark-submit &> /dev/null; then
    echo "❌ Spark未安装"
    exit 1
fi

echo "✅ Spark已安装: $(spark-submit --version 2>&1 | head -n 1)"
echo ""

INPUT_URI="mongodb://admin:sun2137405@1.15.225.134:27017/silvernav.ais_tracks?authSource=admin"
OUTPUT_URI="mongodb://admin:sun2137405@1.15.225.134:27017/silvernav.vessel_analysis?authSource=admin"

spark-submit \
  --master local[*] \
  --driver-memory 2g \
  --executor-memory 1g \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  --conf "spark.mongodb.input.uri=$INPUT_URI" \
  --conf "spark.mongodb.output.uri=$OUTPUT_URI" \
  "$PY_SCRIPT"

echo ""
echo "完成时间: $(date)"
echo "=========================================="