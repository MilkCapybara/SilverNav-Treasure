# Phase 2 快速启动指南

## 🚀 立即开始

你已经完成了所有准备工作！现在可以开始执行了。

---

## ✅ 准备工作检查清单

- ✅ 数据生成脚本已修改（200万 → 2000万）
- ✅ MongoDB连接正常（1.15.225.134:27017）
- ✅ Spark作业已开发完成
- ✅ behavior_api已集成到main.py
- ✅ 执行脚本已创建
- ✅ 文档已完善

---

## 📋 三步执行流程

### Step 1: 生成2000万条AIS数据（30-60分钟）

**后台运行（推荐）**:
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
nohup python3 scripts/generate_ais_data.py > data_generation.log 2>&1 &
echo "数据生成任务已启动，进程ID: $!"
```

**监控进度**:
```bash
# 实时查看日志
tail -f data_generation.log

# 或者每10秒检查一次数据量
watch -n 10 'python3 -c "from pymongo import MongoClient; from app.config import settings; client = MongoClient(f\"mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}\"); count = client[settings.mongo_db][\"ais_tracks\"].count_documents({}); print(f\"进度: {count:,} / 20,000,000 ({count/20000000*100:.2f}%)\"); client.close()"'
```

---

### Step 2: 运行Spark分析（10-20分钟）

**等待Step 1完成后执行**:
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

**如果Spark未安装**:
```bash
# macOS
brew install apache-spark

# 或下载安装包
# https://spark.apache.org/downloads.html
```

---

### Step 3: 启动API服务并测试

```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
python3 main.py
```

**测试API（另开终端）**:
```bash
# 1. 获取总览
curl -X GET http://localhost:8000/api/behavior/summary | jq

# 2. 获取船舶轨迹
curl -X POST http://localhost:8000/api/behavior/tracks \
  -H "Content-Type: application/json" \
  -d '{"imo_number": "IMO9000001", "limit": 100}' | jq

# 3. 获取异常停泊
curl -X POST http://localhost:8000/api/behavior/anomalies \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}' | jq
```

---

## 📊 当前状态

**数据生成任务**: 🔄 正在后台运行（任务ID: bd60131）

**查看实时进度**:
```bash
# 方法1: 查看日志
tail -f /private/tmp/claude-501/-Users-sunfanmacpro-Desktop-SilverNav-Treasure/tasks/bd60131.output

# 方法2: 查看MongoDB数据量
python3 -c "from pymongo import MongoClient; from app.config import settings; client = MongoClient(f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'); count = client[settings.mongo_db]['ais_tracks'].count_documents({}); print(f'当前: {count:,} / 20,000,000 ({count/20000000*100:.2f}%)'); client.close()"
```

---

## 📈 预期时间线

| 阶段 | 耗时 | 状态 |
|------|------|------|
| 数据生成 | 30-60分钟 | 🔄 进行中 |
| Spark分析 | 10-20分钟 | ⏳ 等待中 |
| API测试 | 5分钟 | ⏳ 等待中 |
| **总计** | **45-85分钟** | - |

---

## 🎯 完成标准

### 数据层
- [ ] MongoDB有20,000,000条AIS记录
- [ ] 100艘船舶都有数据
- [ ] 时间跨度约2.5年
- [ ] 数据大小约10GB

### 处理层
- [ ] Spark生成vessel_statistics集合
- [ ] Spark生成ais_anomalies集合
- [ ] 检测出异常停泊记录

### 服务层
- [ ] 5个API端点全部可用
- [ ] API响应时间<500ms

---

## 📞 需要帮助？

查看详细文档：
- `PHASE2_COMPLETE_GUIDE.md` - 完整执行指南
- `PHASE2_EXECUTION_PLAN.md` - 详细执行计划
- `PHASE2_PROGRESS_TRACKER.md` - 进度跟踪

联系方式：
- 邮箱: fandesunstar@outlook.com
- 微信: +86 18601657185

---

**更新时间**: 2026-02-21
**当前任务**: 生成2000万条AIS数据（进行中）
