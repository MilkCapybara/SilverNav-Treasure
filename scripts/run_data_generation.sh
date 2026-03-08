#!/bin/bash
# 生成2000万条AIS轨迹数据
# 预计耗时：30-60分钟

echo "=========================================="
echo "开始生成2000万条AIS轨迹数据"
echo "=========================================="
echo ""
echo "开始时间: $(date)"
echo ""

cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

# 运行数据生成脚本
python3 scripts/generate_ais_data.py

echo ""
echo "完成时间: $(date)"
echo "=========================================="
