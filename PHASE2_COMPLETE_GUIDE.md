# Phase 2 完整执行指南

## 📋 项目概述

**项目名称**: 银航宝 SilverNav Treasure - Phase 2 大数据升级
**目标**: 将MongoDB数据量从200万升级到2000万，完成非结构化数据处理与大数据技术集成
**当前状态**: 准备就绪，开始执行

---

## ✅ 已完成的准备工作

### 1. 代码修改
- ✅ 修改`scripts/generate_ais_data.py`：`target_records = 20_000_000`（2000万条）
- ✅ MongoDB集成完成（`app/config.py`, `app/database.py`）
- ✅ Spark作业开发完成（`spark_jobs/ais_trajectory_analysis.py`, `spark_jobs/mongo_to_hdfs.py`）
- ✅ 船舶行为分析API完成（`app/behavior_api.py`）
- ✅ main.py已集成behavior API（4个端点）

### 2. 环境验证
- ✅ MongoDB连接正常：`1.15.225.134:27017/silvernav`
- ✅ Python环境正常：`pymongo 4.16.0`, `motor 3.7.1`
- ✅ 现有数据：200万条（将被清空并重新生成）

### 3. 执行脚本
- ✅ `run_data_generation.sh` - 数据生成脚本
- ✅ `run_spark_analysis.sh` - Spark分析脚本
- ✅ `PHASE2_EXECUTION_PLAN.md` - 详细执行计划
- ✅ `PHASE2_PROGRESS_TRACKER.md` - 进度跟踪文档

---

## 🚀 执行步骤

### Step 1: 生成2000万条AIS轨迹数据

**方式1：前台运行（推荐用于测试）**
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
python3 scripts/generate_ais_data.py
```

**方式2：后台运行（推荐用于生产）**
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
nohup python3 scripts/generate_ais_data.py > data_generation.log 2>&1 &

# 查看进程ID
echo $!

# 实时监控日志
tail -f data_generation.log
```

**方式3：使用执行脚本**
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
./run_data_generation.sh
```

**预计耗时**: 30-60分钟

**进度监控**:
```bash
# 方法1：查看MongoDB数据量（每5秒刷新）
watch -n 5 'python3 -c "from pymongo import MongoClient; from app.config import settings; client = MongoClient(f\"mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}\"); count = client[settings.mongo_db][\"ais_tracks\"].count_documents({}); print(f\"当前记录数: {count:,} / 20,000,000 ({count/20000000*100:.2f}%)\"); client.close()"'

# 方法2：查看日志文件
tail -f data_generation.log

# 方法3：使用MongoDB Compass连接查看
# 连接字符串: mongodb://admin:sun2137405@1.15.225.134:27017/silvernav?authSource=admin
```

**预期输出**:
```
================================================================================
生成AIS轨迹数据并导入MongoDB
================================================================================

清空现有数据...

从PostgreSQL读取船舶列表...
✅ 读取到 100 艘船舶

数据生成计划：
  目标记录数: 20,000,000
  船舶数量: 100
  每艘船记录数: 200,000
  每艘船航线数: 2,778
  每条航线点数: 72

开始生成数据...

处理船舶 1/100: VESSEL_001
  已插入 10,000 条记录 (0.1%)
  已插入 20,000 条记录 (0.1%)
  已插入 30,000 条记录 (0.2%)
  ...
  已插入 200,000 条记录 (1.0%)

处理船舶 2/100: VESSEL_002
  已插入 210,000 条记录 (1.1%)
  ...

[继续处理剩余98艘船舶...]

处理船舶 100/100: VESSEL_100
  已插入 19,990,000 条记录 (99.9%)
  已插入 20,000,000 条记录 (100.0%)

✅ 数据生成完成！总计插入 20,000,000 条记录

创建索引...
  ✅ 地理空间索引: position (2dsphere)
  ✅ 复合索引: imo_number + timestamp
  ✅ 时间索引: timestamp
  ✅ 船名索引: vessel_name

数据统计：
  总记录数: 20,000,000
  船舶数量: 100
  时间范围: 2023-08-15 ~ 2026-02-21
  数据大小: 10,240.00 MB

================================================================================
✅ AIS轨迹数据生成完成！
================================================================================
```

---

### Step 2: 运行Spark轨迹分析作业

**前提条件**: Step 1完成，MongoDB中有2000万条记录

**检查Spark环境**:
```bash
# 检查Spark是否安装
spark-submit --version

# 如果未安装，请先安装Spark 3.5.1
# macOS: brew install apache-spark
# 或下载: https://spark.apache.org/downloads.html
```

**运行Spark作业**:
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

# 设置环境变量
export SILVERNAV_MONGO_HOST=1.15.225.134
export SILVERNAV_MONGO_PORT=27017
export SILVERNAV_MONGO_DB=silvernav
export SILVERNAV_MONGO_USER=admin
export SILVERNAV_MONGO_PASSWORD=sun2137405
export SILVERNAV_MONGO_AUTH_SOURCE=admin

# 运行Spark作业
spark-submit \
  --master local[*] \
  --driver-memory 4g \
  --executor-memory 4g \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
  spark_jobs/ais_trajectory_analysis.py
```

**或使用执行脚本**:
```bash
./run_spark_analysis.sh
```

**预计耗时**: 10-20分钟

**预期输出**:
```
================================================================================
Spark作业：AIS轨迹数据分析
================================================================================

✅ Spark会话创建成功

📊 读取AIS轨迹数据...
✅ 读取到 20,000,000 条轨迹记录

🧹 数据清洗...
✅ 清洗后保留 19,950,000 条记录 (99.8%)

📈 按船舶聚合统计...
✅ 统计了 100 艘船舶

前10艘船舶统计：
+------------+-------------+---------------+-----+-----------+---------+---------+---------+-------------------+-------------------+
|imo_number  |vessel_name  |ship_type      |flag |track_count|avg_speed|max_speed|min_speed|first_seen         |last_seen          |
+------------+-------------+---------------+-----+-----------+---------+---------+---------+-------------------+-------------------+
|IMO9000001  |VESSEL_001   |Container Ship |CN   |199500     |12.5     |18.0     |0.0      |2023-08-15 00:00:00|2026-02-21 23:00:00|
|IMO9000002  |VESSEL_002   |Bulk Carrier   |HK   |199500     |12.3     |17.8     |0.0      |2023-08-15 00:00:00|2026-02-21 23:00:00|
...

💾 写入统计结果到MongoDB...
✅ 统计结果已写入 vessel_statistics 集合

🔍 异常停泊检测...
✅ 检测到 1,234 次异常停泊

前10次异常停泊：
+------------+-------------+-------------------+----------+-----+--------+---------------+
|imo_number  |vessel_name  |timestamp          |position  |speed|status  |time_diff_hours|
+------------+-------------+-------------------+----------+-----+--------+---------------+
|IMO9000001  |VESSEL_001   |2023-09-15 12:00:00|...       |0.5  |at anchor|26.5          |
...

💾 写入异常停泊记录到MongoDB...
✅ 异常停泊记录已写入 ais_anomalies 集合

📊 按船舶类型统计...
船舶类型统计：
+---------------+-----------+---------+
|ship_type      |track_count|avg_speed|
+---------------+-----------+---------+
|Container Ship |4000000    |12.5     |
|Bulk Carrier   |4000000    |12.3     |
|Oil Tanker     |4000000    |11.8     |
|LNG Carrier    |4000000    |13.2     |
|General Cargo  |4000000    |11.5     |
+---------------+-----------+---------+

🏴 按国旗统计...
📊 按状态统计...

================================================================================
✅ Spark作业执行完成！
================================================================================
```

---

### Step 3: 启动API服务并测试

**启动FastAPI服务**:
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
python3 main.py
```

**预期输出**:
```
✅ MongoDB连接成功: 1.15.225.134:27017/silvernav
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**测试API端点**（另开终端）:

1. **获取行为分析总览**
```bash
curl -X GET http://localhost:8000/api/behavior/summary | jq
```

预期响应:
```json
{
  "success": true,
  "summary": {
    "total_tracks": 20000000,
    "vessel_count": 100,
    "anomaly_count": 1234,
    "time_range": {
      "start": "2023-08-15T00:00:00",
      "end": "2026-02-21T23:00:00"
    },
    "ship_type_distribution": [
      {"type": "Container Ship", "count": 4000000},
      {"type": "Bulk Carrier", "count": 4000000},
      ...
    ]
  }
}
```

2. **获取船舶轨迹**
```bash
curl -X POST http://localhost:8000/api/behavior/tracks \
  -H "Content-Type: application/json" \
  -d '{
    "imo_number": "IMO9000001",
    "start_date": "2025-11-01T00:00:00",
    "end_date": "2025-11-30T23:59:59",
    "limit": 100
  }' | jq
```

3. **获取异常停泊记录**
```bash
curl -X POST http://localhost:8000/api/behavior/anomalies \
  -H "Content-Type: application/json" \
  -d '{
    "imo_number": "IMO9000001",
    "limit": 10
  }' | jq
```

4. **地理围栏查询（上海周边）**
```bash
curl -X POST http://localhost:8000/api/behavior/geofence \
  -H "Content-Type: application/json" \
  -d '{
    "min_lng": 121.0,
    "max_lng": 122.0,
    "min_lat": 30.0,
    "max_lat": 32.0,
    "start_date": "2025-11-01T00:00:00",
    "limit": 50
  }' | jq
```

5. **获取船舶统计**
```bash
curl -X POST http://localhost:8000/api/behavior/statistics \
  -H "Content-Type: application/json" \
  -d '{
    "ship_type": "Container Ship",
    "limit": 10
  }' | jq
```

---

## 📊 数据验证

### 验证数据完整性

```bash
# 连接MongoDB并验证
python3 << 'EOF'
from pymongo import MongoClient
from app.config import settings

mongo_uri = f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'
client = MongoClient(mongo_uri)
db = client[settings.mongo_db]

print("=" * 80)
print("数据验证报告")
print("=" * 80)

# 1. AIS轨迹数据
ais_count = db['ais_tracks'].count_documents({})
print(f"\n1. AIS轨迹记录数: {ais_count:,}")
print(f"   目标: 20,000,000")
print(f"   完成度: {ais_count/20000000*100:.2f}%")

# 2. 船舶数量
vessel_count = len(db['ais_tracks'].distinct('imo_number'))
print(f"\n2. 船舶数量: {vessel_count}")
print(f"   目标: 100")

# 3. 时间范围
oldest = db['ais_tracks'].find_one(sort=[('timestamp', 1)])
newest = db['ais_tracks'].find_one(sort=[('timestamp', -1)])
if oldest and newest:
    print(f"\n3. 时间范围:")
    print(f"   最早: {oldest['timestamp']}")
    print(f"   最晚: {newest['timestamp']}")
    days = (newest['timestamp'] - oldest['timestamp']).days
    print(f"   跨度: {days} 天 ({days/365:.1f} 年)")

# 4. 索引
indexes = db['ais_tracks'].list_indexes()
print(f"\n4. 索引:")
for idx in indexes:
    print(f"   - {idx['name']}: {idx.get('key', {})}")

# 5. 数据大小
stats = db.command('collstats', 'ais_tracks')
size_mb = stats['size'] / (1024 * 1024)
print(f"\n5. 数据大小: {size_mb:.2f} MB ({size_mb/1024:.2f} GB)")

# 6. Spark分析结果
vessel_stats_count = db['vessel_statistics'].count_documents({})
anomaly_count = db['ais_anomalies'].count_documents({})
print(f"\n6. Spark分析结果:")
print(f"   - vessel_statistics: {vessel_stats_count} 条")
print(f"   - ais_anomalies: {anomaly_count} 条")

print("\n" + "=" * 80)
print("✅ 数据验证完成")
print("=" * 80)

client.close()
EOF
```

---

## 🎯 验收标准

### 数据层验收
- [ ] MongoDB存储20,000,000条AIS轨迹记录
- [ ] 100艘船舶都有数据
- [ ] 时间跨度覆盖约2.5年（900天）
- [ ] 地理空间索引创建成功
- [ ] 数据大小约10GB

### 处理层验收
- [ ] Spark成功读取2000万条记录
- [ ] 生成100艘船舶的统计信息
- [ ] 检测出异常停泊记录
- [ ] 结果写回MongoDB（vessel_statistics, ais_anomalies）

### 服务层验收
- [ ] 5个API端点全部可用
- [ ] API响应时间<500ms
- [ ] 支持分页和过滤
- [ ] 错误处理完善

---

## 🔧 故障排查

### 问题1: MongoDB连接失败
**症状**: `ConnectionFailure: [Errno 61] Connection refused`

**解决方案**:
```bash
# 检查MongoDB服务状态
ping 1.15.225.134

# 测试MongoDB连接
python3 -c "from pymongo import MongoClient; client = MongoClient('mongodb://admin:sun2137405@1.15.225.134:27017/silvernav?authSource=admin'); print('连接成功'); client.close()"
```

### 问题2: 数据生成速度慢
**症状**: 插入速度<1000条/秒

**解决方案**:
- 调整batch_size（当前10000，可尝试5000或20000）
- 检查网络延迟
- 考虑使用本地MongoDB

### 问题3: Spark作业失败
**症状**: `java.lang.ClassNotFoundException: com.mongodb.spark.sql.connector.MongoTableProvider`

**解决方案**:
```bash
# 确认Spark版本
spark-submit --version

# 确认MongoDB Connector版本匹配
# Spark 3.5.x 使用 mongo-spark-connector_2.12:10.2.0
```

### 问题4: 磁盘空间不足
**症状**: `No space left on device`

**解决方案**:
```bash
# 检查磁盘空间
df -h

# 清理MongoDB临时文件
# 或使用外部存储
```

---

## 📈 性能优化建议

### 数据生成优化
1. **批量大小**: 根据网络情况调整batch_size（5000-20000）
2. **并行生成**: 可以分批生成，多进程并行
3. **本地MongoDB**: 使用本地MongoDB可提升10倍速度

### Spark分析优化
1. **内存配置**: 增加driver-memory和executor-memory
2. **分区数**: 调整spark.sql.shuffle.partitions
3. **持久化**: 对频繁使用的DataFrame进行cache()

### API查询优化
1. **索引优化**: 确保查询字段都有索引
2. **分页查询**: 使用limit限制返回数量
3. **缓存**: 对热点数据使用Redis缓存

---

## 📞 技术支持

如遇到问题，请联系：
- **开发者**: 孙帆（Sunstar）
- **邮箱**: fandesunstar@outlook.com
- **微信**: +86 18601657185

或查看文档：
- `ROADMAP.md` - 项目路线图
- `PHASE2_PLAN.md` - Phase 2详细计划
- `PHASE2_EXECUTION_PLAN.md` - 执行计划
- `PHASE2_PROGRESS_TRACKER.md` - 进度跟踪

---

**最后更新**: 2026-02-21
**项目状态**: Phase 2 执行中
**当前任务**: 生成2000万条AIS数据
