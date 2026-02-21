# Phase 2 升级计划：MongoDB + 大数据技术深度集成

## 📋 项目背景

**课设要求**：需要处理非结构化数据
**现有资源**：
- MongoDB 7.0.29（IP: 1.15.225.134, 用户: admin, 密码: sun2137405）
- Hadoop 3.3.6 + Spark 3.5.1（已有2个Spark作业）
- PostgreSQL 14.20（已有12张表）

**核心目标**：将MongoDB与Hadoop/Spark深度集成，实现非结构化数据的大数据处理

---

## 🎯 MongoDB + 大数据技术结合方案

### 方案1：Spark + MongoDB Connector（推荐）

**技术栈**：
- **Spark MongoDB Connector**：`org.mongodb.spark:mongo-spark-connector_2.12:10.2.0`
- **读取MongoDB**：Spark DataFrame API直接读取MongoDB集合
- **写入MongoDB**：Spark处理后的结果写回MongoDB
- **优势**：
  - ✅ 原生支持，性能优秀
  - ✅ 支持分布式读写
  - ✅ 支持聚合管道下推
  - ✅ 与现有Spark作业无缝集成

**应用场景**：
1. **AIS轨迹数据分析**：从MongoDB读取百万级轨迹点，Spark聚合分析
2. **审计日志分析**：从MongoDB读取日志，Spark进行异常检测
3. **文本数据挖掘**：船舶事故报告、新闻舆情分析

### 方案2：Hadoop + MongoDB Connector

**技术栈**：
- **MongoDB Hadoop Connector**：`org.mongodb.mongo-hadoop:mongo-hadoop-core:2.0.2`
- **MapReduce作业**：直接在MongoDB上运行MapReduce
- **优势**：
  - ✅ 支持大规模数据处理
  - ✅ 与HDFS集成

**应用场景**：
1. **历史数据归档**：MongoDB → HDFS冷数据迁移
2. **数据湖构建**：MongoDB作为数据源之一

### 方案3：Flink + MongoDB Connector（实时流处理）

**技术栈**：
- **Flink MongoDB Connector**：`org.apache.bahir:flink-connector-mongodb_2.12:1.1.0`
- **实时写入**：Flink处理后的数据实时写入MongoDB
- **优势**：
  - ✅ 实时性强
  - ✅ 支持CDC

**应用场景**：
1. **实时风险预警**：PostgreSQL CDC → Flink → MongoDB
2. **实时轨迹追踪**：AIS数据流 → Flink → MongoDB

---

## 🚀 Phase 2 升级计划（MongoDB + Spark深度集成）

### 任务1：MongoDB集成与Spark连接器配置（优先级：最高）

**目标**：完成MongoDB Python驱动和Spark连接器的安装配置

**实施步骤**：

1. **安装Python驱动**（5分钟）
```bash
pip install pymongo motor
```

2. **配置MongoDB连接**（30分钟）
- 在`app/config.py`中添加MongoDB配置
- 在`app/database.py`中添加MongoDB连接池
- 测试连接是否正常

3. **下载Spark MongoDB Connector**（10分钟）
```bash
# 下载MongoDB Spark Connector JAR
wget https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.2.0/mongo-spark-connector_2.12-10.2.0.jar -P /usr/local/spark/jars/
```

4. **测试Spark读写MongoDB**（30分钟）
- 创建测试脚本验证Spark能否读写MongoDB

**预计工作量**：2小时

---

### 任务2：AIS轨迹数据生成与导入（优先级：高）

**目标**：生成模拟AIS轨迹数据并导入MongoDB

**数据集合设计**：

```javascript
// ais_tracks 集合
{
  _id: ObjectId("..."),
  imo_number: "IMO9876543",
  vessel_name: "COSCO SHIPPING UNIVERSE",
  mmsi: "413123456",
  timestamp: ISODate("2026-02-21T08:30:00Z"),
  position: {
    type: "Point",
    coordinates: [121.4737, 31.2304]  // [经度, 纬度]
  },
  speed: 12.5,  // 节
  course: 90,   // 度
  heading: 92,  // 度
  status: "underway using engine",
  destination: "SHANGHAI",
  eta: ISODate("2026-02-22T06:00:00Z"),
  draught: 12.5,  // 吃水深度（米）
  ship_type: "Container Ship",
  flag: "CN",
  created_at: ISODate("2026-02-21T08:30:00Z")
}

// 地理空间索引
db.ais_tracks.createIndex({ position: "2dsphere" })
db.ais_tracks.createIndex({ imo_number: 1, timestamp: -1 })
db.ais_tracks.createIndex({ timestamp: -1 })
```

**实施步骤**：

1. **编写数据生成脚本**（2小时）
```python
# scripts/generate_ais_data.py
import random
from datetime import datetime, timedelta
from pymongo import MongoClient

def generate_ais_tracks(vessel_count=100, days=30):
    """生成模拟AIS轨迹数据"""
    # 从PostgreSQL读取船舶列表
    # 为每艘船生成30天的轨迹（每小时1个点）
    # 模拟航线：上海 → 宁波 → 深圳 → 新加坡
    pass
```

2. **批量导入MongoDB**（30分钟）
```python
# 使用bulk_write批量插入
collection.bulk_write(operations)
```

3. **创建地理空间索引**（10分钟）
```python
collection.create_index([("position", "2dsphere")])
collection.create_index([("imo_number", 1), ("timestamp", -1)])
```

**数据量**：
- 100艘船舶 × 30天 × 24小时 = 72,000条轨迹记录
- 每条记录约500字节 = 36MB数据

**预计工作量**：3小时

---

### 任务3：Spark作业 - AIS轨迹数据分析（优先级：高）

**目标**：使用Spark分析MongoDB中的AIS轨迹数据

**Spark作业1：轨迹聚合分析**（`spark_jobs/ais_trajectory_analysis.py`）

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, max, min

def main():
    spark = SparkSession.builder \
        .appName("AIS-Trajectory-Analysis") \
        .config("spark.mongodb.read.connection.uri",
                "mongodb://admin:sun2137405@1.15.225.134:27017/silvernav.ais_tracks?authSource=admin") \
        .config("spark.mongodb.write.connection.uri",
                "mongodb://admin:sun2137405@1.15.225.134:27017/silvernav.ais_analysis?authSource=admin") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .getOrCreate()

    # 1. 读取MongoDB中的AIS轨迹数据
    ais_df = spark.read.format("mongodb").load()

    # 2. 数据清洗：过滤异常数据
    clean_df = ais_df.filter(
        (col("speed") >= 0) & (col("speed") <= 30) &
        (col("position.coordinates").isNotNull())
    )

    # 3. 按船舶聚合统计
    vessel_stats = clean_df.groupBy("imo_number", "vessel_name").agg(
        count("*").alias("track_count"),
        avg("speed").alias("avg_speed"),
        max("speed").alias("max_speed"),
        min("timestamp").alias("first_seen"),
        max("timestamp").alias("last_seen")
    )

    # 4. 写回MongoDB
    vessel_stats.write.format("mongodb") \
        .mode("overwrite") \
        .option("collection", "vessel_statistics") \
        .save()

    spark.stop()
```

**Spark作业2：异常停泊检测**（`spark_jobs/ais_anomaly_detection.py`）

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, unix_timestamp
from pyspark.sql.window import Window

def detect_long_stay():
    """检测异常停泊（停留超过24小时）"""
    spark = SparkSession.builder \
        .appName("AIS-Anomaly-Detection") \
        .config("spark.mongodb.read.connection.uri",
                "mongodb://admin:sun2137405@1.15.225.134:27017/silvernav.ais_tracks?authSource=admin") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .getOrCreate()

    ais_df = spark.read.format("mongodb").load()

    # 按船舶和时间排序
    window = Window.partitionBy("imo_number").orderBy("timestamp")

    # 计算相邻两点的时间差和距离
    df_with_lag = ais_df.withColumn("prev_timestamp", lag("timestamp").over(window)) \
                         .withColumn("prev_position", lag("position").over(window))

    # 检测停泊（速度<1节且持续时间>24小时）
    anomalies = df_with_lag.filter(
        (col("speed") < 1) &
        ((unix_timestamp("timestamp") - unix_timestamp("prev_timestamp")) > 86400)
    )

    # 写回MongoDB
    anomalies.write.format("mongodb") \
        .mode("overwrite") \
        .option("collection", "ais_anomalies") \
        .save()

    spark.stop()
```

**预计工作量**：4小时

---

### 任务4：审计日志存储与分析（优先级：中）

**目标**：将用户操作日志存储到MongoDB，并使用Spark进行分析

**数据集合设计**：

```javascript
// audit_logs 集合
{
  _id: ObjectId("..."),
  user_id: 1,
  username: "root",
  action: "login",
  resource: "/api/login",
  method: "POST",
  ip_address: "192.168.1.100",
  user_agent: "Mozilla/5.0...",
  status: "success",
  error_message: null,
  request_body: { "username": "root" },
  response_code: 200,
  duration_ms: 150,
  timestamp: ISODate("2026-02-21T08:30:00Z")
}

// 索引
db.audit_logs.createIndex({ user_id: 1, timestamp: -1 })
db.audit_logs.createIndex({ action: 1, timestamp: -1 })
db.audit_logs.createIndex({ timestamp: -1 })
```

**实施步骤**：

1. **在FastAPI中添加审计日志中间件**（1小时）
```python
# app/middleware.py
from fastapi import Request
from pymongo import MongoClient
import time

async def audit_log_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000

    # 记录到MongoDB
    mongo_client.silvernav.audit_logs.insert_one({
        "user_id": request.state.user_id,
        "action": request.url.path,
        "method": request.method,
        "ip_address": request.client.host,
        "status": "success" if response.status_code < 400 else "error",
        "response_code": response.status_code,
        "duration_ms": duration,
        "timestamp": datetime.utcnow()
    })

    return response
```

2. **Spark作业：审计日志分析**（2小时）
```python
# spark_jobs/audit_log_analysis.py
def analyze_audit_logs():
    """分析审计日志，检测异常行为"""
    spark = SparkSession.builder \
        .appName("Audit-Log-Analysis") \
        .config("spark.mongodb.read.connection.uri",
                "mongodb://admin:sun2137405@1.15.225.134:27017/silvernav.audit_logs?authSource=admin") \
        .getOrCreate()

    logs_df = spark.read.format("mongodb").load()

    # 1. 统计每个用户的操作频率
    user_activity = logs_df.groupBy("user_id", "action").count()

    # 2. 检测异常登录（同一用户短时间内多次失败登录）
    failed_logins = logs_df.filter(
        (col("action") == "login") & (col("status") == "error")
    ).groupBy("user_id", "ip_address").count()

    # 3. 检测慢查询（响应时间>5秒）
    slow_queries = logs_df.filter(col("duration_ms") > 5000)

    return user_activity, failed_logins, slow_queries
```

**预计工作量**：3小时

---

### 任务5：MongoDB → HDFS数据归档（优先级：中）

**目标**：将MongoDB中的历史数据归档到HDFS

**Spark作业：MongoDB → HDFS**（`spark_jobs/mongo_to_hdfs.py`）

```python
from pyspark.sql import SparkSession

def archive_to_hdfs():
    """将MongoDB历史数据归档到HDFS"""
    spark = SparkSession.builder \
        .appName("MongoDB-to-HDFS-Archive") \
        .config("spark.mongodb.read.connection.uri",
                "mongodb://admin:sun2137405@1.15.225.134:27017/silvernav.ais_tracks?authSource=admin") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .getOrCreate()

    # 读取MongoDB中超过90天的历史数据
    from datetime import datetime, timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=90)

    ais_df = spark.read.format("mongodb").load()
    old_data = ais_df.filter(col("timestamp") < cutoff_date)

    # 写入HDFS（Parquet格式，按日期分区）
    old_data.write.partitionBy("year", "month", "day") \
           .mode("append") \
           .parquet("hdfs:///silvernav/archive/ais_tracks")

    # 从MongoDB删除已归档数据（可选）
    # collection.delete_many({"timestamp": {"$lt": cutoff_date}})

    spark.stop()
```

**预计工作量**：2小时

---

### 任务6：船舶行为分析API开发（优先级：高）

**目标**：开发基于MongoDB的船舶行为分析API

**API端点**：

1. **获取船舶轨迹**（`/api/behavior/tracks`）
```python
@app.post("/api/behavior/tracks")
async def get_vessel_tracks(request: Request, payload: VesselTrackQuery):
    """获取指定船舶的历史轨迹"""
    session = get_session(request)

    # 从MongoDB查询
    tracks = mongo_client.silvernav.ais_tracks.find({
        "imo_number": payload.imo_number,
        "timestamp": {
            "$gte": payload.start_date,
            "$lte": payload.end_date
        }
    }).sort("timestamp", 1).limit(1000)

    return JSONResponse({
        "success": True,
        "tracks": list(tracks)
    })
```

2. **检测异常停泊**（`/api/behavior/anomalies`）
```python
@app.post("/api/behavior/anomalies")
async def get_anomalies(request: Request, payload: AnomalyQuery):
    """获取异常停泊记录"""
    session = get_session(request)

    # 从MongoDB查询Spark分析结果
    anomalies = mongo_client.silvernav.ais_anomalies.find({
        "imo_number": payload.imo_number
    }).sort("timestamp", -1).limit(50)

    return JSONResponse({
        "success": True,
        "anomalies": list(anomalies)
    })
```

3. **地理围栏查询**（`/api/behavior/geofence`）
```python
@app.post("/api/behavior/geofence")
async def geofence_query(request: Request, payload: GeofenceQuery):
    """查询指定区域内的船舶"""
    session = get_session(request)

    # 使用MongoDB地理空间查询
    vessels = mongo_client.silvernav.ais_tracks.find({
        "position": {
            "$geoWithin": {
                "$box": [
                    [payload.min_lng, payload.min_lat],
                    [payload.max_lng, payload.max_lat]
                ]
            }
        },
        "timestamp": {"$gte": payload.start_date}
    })

    return JSONResponse({
        "success": True,
        "vessels": list(vessels)
    })
```

**预计工作量**：3小时

---

## 📊 Phase 2 技术架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     数据源层                                  │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL (结构化)  │  MongoDB (非结构化)  │  HDFS (归档)  │
│  - 企业/船舶主数据    │  - AIS轨迹数据       │  - 历史数据   │
│  - 金融资产数据       │  - 审计日志          │  - 冷数据     │
│  - 风险评估数据       │  - 文本数据          │               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   大数据处理层                                │
├─────────────────────────────────────────────────────────────┤
│                    Spark 3.5.1                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PG → HDFS    │  │ Mongo → HDFS │  │ AIS分析      │      │
│  │ 数据迁移     │  │ 数据归档     │  │ 轨迹聚合     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 异常检测     │  │ 审计日志分析 │  │ Dashboard聚合│      │
│  │ 停泊检测     │  │ 用户行为分析 │  │ 风险计算     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   应用服务层                                  │
├─────────────────────────────────────────────────────────────┤
│                  FastAPI + Python                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Dashboard API│  │ 详情页API    │  │ 行为分析API  │      │
│  │ 18个端点     │  │ 8个端点      │  │ 3个端点      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   前端展示层                                  │
├─────────────────────────────────────────────────────────────┤
│  原生JavaScript + HTML5 + CSS3                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 数据大屏     │  │ 详情页面     │  │ 轨迹地图     │      │
│  │ 8大板块      │  │ 8个页面      │  │ Leaflet.js   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Phase 2 交付物清单

### 1. MongoDB集成
- ✅ MongoDB Python驱动（pymongo + motor）
- ✅ MongoDB连接池配置
- ✅ Spark MongoDB Connector配置

### 2. 数据集合
- ✅ `ais_tracks`：AIS轨迹数据（72,000条记录）
- ✅ `audit_logs`：审计日志
- ✅ `vessel_statistics`：船舶统计（Spark聚合结果）
- ✅ `ais_anomalies`：异常停泊记录（Spark分析结果）

### 3. Spark作业
- ✅ `ais_trajectory_analysis.py`：轨迹聚合分析
- ✅ `ais_anomaly_detection.py`：异常停泊检测
- ✅ `audit_log_analysis.py`：审计日志分析
- ✅ `mongo_to_hdfs.py`：MongoDB → HDFS归档

### 4. API端点
- ✅ `/api/behavior/tracks`：获取船舶轨迹
- ✅ `/api/behavior/anomalies`：获取异常记录
- ✅ `/api/behavior/geofence`：地理围栏查询

### 5. 数据生成脚本
- ✅ `scripts/generate_ais_data.py`：生成模拟AIS数据
- ✅ `scripts/import_to_mongo.py`：批量导入MongoDB

### 6. 文档
- ✅ MongoDB集成文档
- ✅ Spark作业使用文档
- ✅ API接口文档

---

## ⏱️ 开发时间表

| 任务 | 预计时间 | 优先级 |
|------|---------|--------|
| 任务1：MongoDB集成与Spark连接器配置 | 2小时 | 最高 |
| 任务2：AIS轨迹数据生成与导入 | 3小时 | 高 |
| 任务3：Spark作业 - AIS轨迹数据分析 | 4小时 | 高 |
| 任务4：审计日志存储与分析 | 3小时 | 中 |
| 任务5：MongoDB → HDFS数据归档 | 2小时 | 中 |
| 任务6：船舶行为分析API开发 | 3小时 | 高 |
| **总计** | **17小时** | **约2-3天** |

---

## 🎯 课设价值点

### 1. 非结构化数据处理 ✅
- MongoDB存储AIS轨迹、审计日志等非结构化数据
- 地理空间数据（GeoJSON）
- 时间序列数据

### 2. 大数据技术应用 ✅
- **Spark + MongoDB Connector**：分布式读写MongoDB
- **Spark批处理**：轨迹聚合、异常检测、日志分析
- **Hadoop HDFS**：历史数据归档

### 3. 数据处理流程 ✅
- **采集**：生成模拟AIS数据
- **存储**：MongoDB存储非结构化数据
- **处理**：Spark分析处理
- **归档**：HDFS冷数据存储
- **服务**：FastAPI提供查询接口

### 4. 技术深度 ✅
- MongoDB地理空间索引（2dsphere）
- Spark DataFrame API
- 分布式计算
- 数据分区与优化

---

## 🚀 立即开始

准备好了吗？我们现在开始Phase 2的开发！

**第一步**：安装MongoDB Python驱动和配置连接
**第二步**：生成AIS轨迹数据并导入MongoDB
**第三步**：开发Spark作业分析MongoDB数据
**第四步**：开发船舶行为分析API

你准备好了吗？我们从第一步开始！
