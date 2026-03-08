#!/bin/bash
# 启动银航宝应用

echo "=========================================="
echo "启动银航宝应用"
echo "=========================================="
echo ""

cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

# 检查Python环境
echo "1. 检查Python环境..."
python3 --version
echo ""

# 检查依赖
echo "2. 检查关键依赖..."
python3 -c "import fastapi; import pymongo; import psycopg2; print('✅ 依赖检查通过')"
echo ""

# 启动应用
echo "3. 启动应用..."
echo "   访问地址: http://localhost:8000"
echo "   大屏地址: http://localhost:8000/dashboard"
echo "   船舶行为分析: http://localhost:8000/behavior"
echo "   船舶画像: http://localhost:8000/profile"
echo "   数据血缘: http://localhost:8000/lineage"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
