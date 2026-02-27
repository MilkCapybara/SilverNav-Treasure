#!/bin/bash
# Mac本地运行脚本 - 纯PySpark版本
# 使用方法: bash spark_jobs/run_pyspark_local.sh

echo "=========================================="
echo "AIS轨迹分析 - Mac本地环境（纯PySpark）"
echo "=========================================="
echo ""
echo "开始时间: $(date)"
echo ""

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

echo "✅ Python3已安装: $(python3 --version)"

# 检查Java
if ! command -v java &> /dev/null; then
    echo "❌ Java未安装，Spark需要Java运行"
    echo "   请运行: brew install openjdk@11"
    exit 1
fi

echo "✅ Java已安装: $(java -version 2>&1 | head -n 1)"

# 检查pyspark
if ! python3 -c "import pyspark" 2>/dev/null; then
    echo "❌ PySpark未安装"
    echo "   请运行: pip3 install pyspark"
    exit 1
fi

PYSPARK_VERSION=$(python3 -c "import pyspark; print(pyspark.__version__)")
echo "✅ PySpark已安装: $PYSPARK_VERSION"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/ais_analysis_pyspark_only.py"

# 检查Python脚本是否存在
if [ ! -f "$PY_SCRIPT" ]; then
    echo "❌ 找不到Python脚本: $PY_SCRIPT"
    exit 1
fi

echo "Python脚本: $PY_SCRIPT"
echo ""
echo "开始执行分析..."
echo "=========================================="
echo ""

# 直接用Python运行，不需要spark-submit
python3 "$PY_SCRIPT"

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "完成时间: $(date)"
echo "退出码: $EXIT_CODE"
echo "=========================================="

exit $EXIT_CODE
