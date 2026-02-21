# 🔄 数据量调整完成指南

## 📋 当前状态

- ✅ 数据生成脚本已修改：2000万 → 200万
- ✅ 旧的数据生成进程已停止
- ✅ 创建了一键重置脚本
- ✅ 创建了进度检查脚本

---

## 🚀 快速执行（推荐）

### 方法1：使用一键脚本（最简单）

```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
./reset_and_generate_200w.sh
```

这个脚本会自动：
1. 停止旧的数据生成进程
2. 清空MongoDB现有数据
3. 确认脚本配置为200万
4. 开始生成200万条数据

### 方法2：手动执行（分步骤）

#### Step 1: 停止旧进程
```bash
pkill -f "generate_ais_data.py"
```

#### Step 2: 清空MongoDB数据
```bash
python3 << 'EOF'
from pymongo import MongoClient
from app.config import settings

mongo_uri = f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'
client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
db = client[settings.mongo_db]

# 清空数据
db['ais_tracks'].delete_many({})
db['vessel_statistics'].delete_many({})
db['ais_anomalies'].delete_many({})
print('✅ 数据已清空')

client.close()
EOF
```

#### Step 3: 生成200万条数据
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
nohup python3 scripts/generate_ais_data.py > data_generation_200w.log 2>&1 &
```

---

## 📊 查看进度

### 方法1：使用进度检查脚本
```bash
./check_progress.sh
```

### 方法2：查看日志
```bash
tail -f data_generation_200w.log
```

### 方法3：查询MongoDB
```bash
python3 -c "from pymongo import MongoClient; from app.config import settings; client = MongoClient(f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}', serverSelectionTimeoutMS=10000); count = client[settings.mongo_db]['ais_tracks'].count_documents({}); print(f'进度: {count:,} / 2,000,000 ({count/2000000*100:.1f}%)'); client.close()"
```

---

## ⏱️ 预期时间

### 200万条数据
- **生成时间**: 3-6分钟
- **数据大小**: ~1GB
- **船舶数量**: 100艘
- **时间跨度**: 90天

### 对比2000万条
| 指标 | 200万 | 2000万 | 差异 |
|------|-------|--------|------|
| 记录数 | 200万 | 2000万 | 10倍 |
| 生成时间 | 3-6分钟 | 30-60分钟 | 10倍 |
| 数据大小 | ~1GB | ~10GB | 10倍 |
| 时间跨度 | 90天 | 900天 | 10倍 |

---

## ✅ 完成后的步骤

### 1. 验证数据
```bash
python3 << 'EOF'
from pymongo import MongoClient
from app.config import settings

mongo_uri = f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'
client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
db = client[settings.mongo_db]

count = db['ais_tracks'].count_documents({})
vessel_count = len(db['ais_tracks'].distinct('imo_number'))

print(f'✅ 总记录数: {count:,}')
print(f'✅ 船舶数量: {vessel_count}')

# 时间范围
oldest = db['ais_tracks'].find_one(sort=[('timestamp', 1)])
newest = db['ais_tracks'].find_one(sort=[('timestamp', -1)])
if oldest and newest:
    days = (newest['timestamp'] - oldest['timestamp']).days
    print(f'✅ 时间跨度: {days} 天')

client.close()
EOF
```

### 2. 运行Spark分析
```bash
./run_spark_analysis.sh
```

### 3. 启动服务测试
```bash
./start_server.sh
```

访问：http://localhost:8000/behavior

---

## 🎯 为什么选择200万？

### 优势
✅ **生成速度快**：3-6分钟 vs 30-60分钟
✅ **测试方便**：快速迭代和测试
✅ **演示流畅**：数据加载和查询更快
✅ **仍是大数据**：百万级数据量
✅ **满足课设**：足够展示技术能力

### 功能完整性
- ✅ 所有功能都能正常展示
- ✅ 地图可视化效果一样
- ✅ Spark分析能力一样
- ✅ 课设价值点不变

---

## 🔧 故障排查

### 问题1：MongoDB连接超时
**症状**：`ServerSelectionTimeoutError`

**解决方案**：
```bash
# 测试网络连接
ping 1.15.225.134

# 等待几秒后重试
sleep 10
python3 -c "from pymongo import MongoClient; from app.config import settings; client = MongoClient(f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}', serverSelectionTimeoutMS=30000); print('连接成功'); client.close()"
```

### 问题2：进程没有停止
**症状**：`pkill`后进程仍在运行

**解决方案**：
```bash
# 强制停止
pkill -9 -f "generate_ais_data.py"

# 或者找到PID手动停止
ps aux | grep generate_ais_data
kill -9 <PID>
```

### 问题3：数据没有清空
**症状**：重新生成后数据量不对

**解决方案**：
```bash
# 手动清空
python3 << 'EOF'
from pymongo import MongoClient
from app.config import settings
mongo_uri = f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'
client = MongoClient(mongo_uri, serverSelectionTimeoutMS=30000)
db = client[settings.mongo_db]
db['ais_tracks'].drop()  # 直接删除集合
print('✅ 集合已删除')
client.close()
EOF
```

---

## 📝 执行清单

- [ ] 停止旧的数据生成进程
- [ ] 清空MongoDB现有数据
- [ ] 确认脚本配置为200万
- [ ] 启动新的数据生成任务
- [ ] 监控生成进度
- [ ] 验证数据完整性
- [ ] 运行Spark分析
- [ ] 测试页面功能

---

## 🚀 立即开始

```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
./reset_and_generate_200w.sh
```

然后查看进度：
```bash
./check_progress.sh
```

或实时监控：
```bash
tail -f data_generation_200w.log
```

---

**创建时间**: 2026-02-21
**状态**: 已准备就绪
**预计完成**: 3-6分钟后
