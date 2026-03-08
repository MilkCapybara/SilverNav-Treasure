#!/bin/bash
# 快速启动合同风险分析系统

echo "=========================================="
echo "  银航宝 - 合同风险分析系统启动脚本"
echo "=========================================="
echo ""

# 检查MongoDB连接
echo "1. 检查MongoDB连接..."
python3 -c "
from pymongo import MongoClient
from app.config import settings

try:
    mongo_uri = f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client[settings.mongo_db]
    collection = db['contracts']
    total = collection.count_documents({})
    print(f'✅ MongoDB连接成功')
    print(f'✅ 已分析合同数: {total}')
    client.close()
except Exception as e:
    print(f'❌ MongoDB连接失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ MongoDB连接失败，请检查配置"
    exit 1
fi

echo ""
echo "2. 启动FastAPI服务..."
echo "   访问地址: http://localhost:8000"
echo "   合同风险分析: http://localhost:8000/contract-risk"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动FastAPI
python3 main.py
