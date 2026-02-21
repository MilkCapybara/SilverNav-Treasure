# 数据量调整说明

## 问题
- 原计划：2000万条数据
- 当前状态：数据生成进行中（约1.2%，23万条）
- 新需求：改回200万条数据

## 解决方案

### Step 1: 停止当前数据生成任务

如果有正在运行的进程，先停止它：

```bash
# 查找进程
ps aux | grep "generate_ais_data" | grep -v grep

# 停止进程（如果有）
pkill -f "generate_ais_data.py"

# 或者使用进程ID停止
kill <PID>
```

### Step 2: 清空MongoDB现有数据

```bash
python3 << 'EOF'
from pymongo import MongoClient
from app.config import settings

mongo_uri = f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'
client = MongoClient(mongo_uri)
db = client[settings.mongo_db]

# 清空ais_tracks集合
result = db['ais_tracks'].delete_many({})
print(f'✅ 已删除 {result.deleted_count:,} 条记录')

# 清空其他相关集合
db['vessel_statistics'].delete_many({})
db['ais_anomalies'].delete_many({})
print('✅ 已清空所有相关集合')

client.close()
EOF
```

### Step 3: 修改数据生成脚本

已修改 `scripts/generate_ais_data.py`：
- 从 `target_records = 20_000_000` 改为 `target_records = 2_000_000`

### Step 4: 重新生成200万条数据

```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

# 后台运行
nohup python3 scripts/generate_ais_data.py > data_generation_200w.log 2>&1 &

# 查看进度
tail -f data_generation_200w.log
```

## 数据规模对比

| 指标 | 200万方案 | 2000万方案 |
|------|----------|-----------|
| 记录数 | 2,000,000 | 20,000,000 |
| 船舶数 | 100艘 | 100艘 |
| 每艘船记录数 | 20,000 | 200,000 |
| 时间跨度 | 90天 | 900天 |
| 数据大小 | ~1GB | ~10GB |
| 生成时间 | 3-6分钟 | 30-60分钟 |

## 推荐方案

**建议使用200万条数据**，原因：
1. ✅ 生成速度快（3-6分钟）
2. ✅ 数据量足够展示功能
3. ✅ 测试和演示更方便
4. ✅ 仍然是大数据规模（百万级）
5. ✅ 满足课设要求

## 快速执行

```bash
# 一键执行（停止旧任务 + 清空数据 + 重新生成）
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

# 1. 停止旧任务
pkill -f "generate_ais_data.py"

# 2. 清空数据
python3 << 'EOF'
from pymongo import MongoClient
from app.config import settings
mongo_uri = f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'
client = MongoClient(mongo_uri)
db = client[settings.mongo_db]
db['ais_tracks'].delete_many({})
db['vessel_statistics'].delete_many({})
db['ais_anomalies'].delete_many({})
print('✅ 数据已清空')
client.close()
EOF

# 3. 重新生成200万条
nohup python3 scripts/generate_ais_data.py > data_generation_200w.log 2>&1 &
echo "✅ 数据生成任务已启动，查看进度: tail -f data_generation_200w.log"
```

---

**创建时间**: 2026-02-21
**状态**: 已修改回200万条
