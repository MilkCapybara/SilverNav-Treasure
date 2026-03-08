#!/bin/bash
# 检查数据生成进度

echo "=========================================="
echo "数据生成进度检查"
echo "=========================================="
echo ""

cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

# 检查进程
echo "1. 检查进程状态..."
if pgrep -f "generate_ais_data.py" > /dev/null; then
    PID=$(pgrep -f "generate_ais_data.py")
    echo "✅ 数据生成进程运行中 (PID: $PID)"
else
    echo "⚠️  没有运行中的数据生成进程"
fi
echo ""

# 检查数据量
echo "2. 检查MongoDB数据量..."
python3 << 'PYTHON_EOF'
from pymongo import MongoClient
from app.config import settings

mongo_uri = f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'

try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    db = client[settings.mongo_db]
    
    count = db['ais_tracks'].count_documents({})
    target = 2000000
    progress = count / target * 100
    
    print(f'当前记录数: {count:,}')
    print(f'目标记录数: {target:,}')
    print(f'完成进度: {progress:.1f}%')
    
    if count > 0:
        # 获取最新记录
        latest = db['ais_tracks'].find_one(sort=[('created_at', -1)])
        if latest:
            print(f'最新记录时间: {latest.get("created_at", "N/A")}')
    
    client.close()
except Exception as e:
    print(f'❌ 查询失败: {e}')
PYTHON_EOF

echo ""

# 检查日志
echo "3. 最新日志（最后10行）..."
if [ -f "data_generation_200w.log" ]; then
    tail -10 data_generation_200w.log
else
    echo "⚠️  日志文件不存在"
fi

echo ""
echo "=========================================="
