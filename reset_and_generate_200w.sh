#!/bin/bash
# 重置并生成200万条数据

echo "=========================================="
echo "重置并生成200万条AIS数据"
echo "=========================================="
echo ""

cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

# 1. 停止所有可能的数据生成进程
echo "1. 停止旧的数据生成进程..."
pkill -f "generate_ais_data.py" 2>/dev/null
sleep 2
echo "✅ 已停止旧进程"
echo ""

# 2. 清空MongoDB数据
echo "2. 清空MongoDB现有数据..."
python3 << 'PYTHON_EOF'
from pymongo import MongoClient
from app.config import settings
import time

mongo_uri = f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'

# 重试连接
for i in range(3):
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        db = client[settings.mongo_db]
        
        # 清空数据
        result1 = db['ais_tracks'].delete_many({})
        result2 = db['vessel_statistics'].delete_many({})
        result3 = db['ais_anomalies'].delete_many({})
        
        print(f'✅ 已删除 ais_tracks: {result1.deleted_count:,} 条')
        print(f'✅ 已删除 vessel_statistics: {result2.deleted_count:,} 条')
        print(f'✅ 已删除 ais_anomalies: {result3.deleted_count:,} 条')
        
        client.close()
        break
    except Exception as e:
        print(f'⚠️  连接失败 (尝试 {i+1}/3): {e}')
        if i < 2:
            time.sleep(5)
        else:
            print('❌ MongoDB连接失败，请检查网络')
            exit(1)
PYTHON_EOF

echo ""

# 3. 确认脚本已修改为200万
echo "3. 确认数据生成脚本配置..."
grep "target_records = 2_000_000" scripts/generate_ais_data.py > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ 脚本已配置为200万条"
else
    echo "❌ 脚本配置错误，请检查"
    exit 1
fi
echo ""

# 4. 开始生成200万条数据
echo "4. 开始生成200万条数据..."
echo "   预计耗时: 3-6分钟"
echo ""

nohup python3 scripts/generate_ais_data.py > data_generation_200w.log 2>&1 &
PID=$!

echo "✅ 数据生成任务已启动"
echo "   进程ID: $PID"
echo "   日志文件: data_generation_200w.log"
echo ""
echo "查看实时进度:"
echo "   tail -f data_generation_200w.log"
echo ""
echo "查看当前记录数:"
echo "   python3 -c \"from pymongo import MongoClient; from app.config import settings; client = MongoClient(f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'); count = client[settings.mongo_db]['ais_tracks'].count_documents({}); print(f'当前: {count:,} / 2,000,000 ({count/2000000*100:.1f}%)'); client.close()\""
echo ""
echo "=========================================="
