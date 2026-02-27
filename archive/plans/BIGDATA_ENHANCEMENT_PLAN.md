# 🚀 银航宝大数据技术深化方案

## 📊 项目现状评估

### 当前数据资产
- ✅ **MongoDB AIS数据**: 2,001,600条轨迹记录
- ✅ **PostgreSQL**: 12张表，完整的金融风控数据
- ✅ **Spark环境**: 云服务器 1.15.225.134 已部署
- ⚠️ **待处理**: vessel_statistics和ais_anomalies集合为空

### 技术栈现状
```
前端: HTML5 + JavaScript + Leaflet.js
后端: FastAPI + Python 3.12
数据库: PostgreSQL 14.20 + MongoDB 7.0.29
大数据: Spark 3.5.1 + Hadoop 3.3.6（云端）
```

---

## 🎯 专业化提升方案（三大方向）

### 方案一：实时流式计算 + 智能异常检测 ⭐⭐⭐⭐⭐

**核心价值**: 展示Spark Streaming + 机器学习的工业级应用

#### 1.1 实时轨迹异常检测系统

**技术架构**:
```
MongoDB → Spark Structured Streaming → 异常检测模型 → 实时告警
```

**实现功能**:
- **速度异常检测**: 识别突然加速/减速（可能的碰撞、故障）
- **航向异常检测**: 频繁转向（可能的走私、规避监管）
- **区域异常检测**: 进入高风险水域（海盗区、制裁区）
- **停泊异常检测**: 异常停泊时长和位置（可能的非法活动）

**技术亮点**:
```python
# 滑动窗口聚合
df.groupBy(
    window("timestamp", "10 minutes", "5 minutes"),
    "imo_number"
).agg(
    avg("speed").alias("avg_speed"),
    stddev("speed").alias("speed_stddev"),
    count("*").alias("point_count")
)

# 异常评分（Z-Score）
anomaly_score = abs(speed - avg_speed) / speed_stddev
```

#### 1.2 基于DBSCAN的航线聚类分析

**功能**:
- 识别常见航线模式（上海-新加坡、宁波-洛杉矶等）
- 检测异常绕航行为
- 航线优化建议

**技术实现**:
```python
from pyspark.ml.clustering import DBSCAN

# 对轨迹点进行密度聚类
dbscan = DBSCAN(
    eps=0.1,  # 经纬度距离阈值
    minPts=50,  # 最小点数
    distanceMeasure="haversine"  # 地球表面距离
)
```

#### 1.3 时间序列预测（ETA预测）

**功能**:
- 基于历史轨迹预测到达时间
- 考虑天气、海况、港口拥堵等因素
- 动态更新预测

**技术实现**:
```python
from pyspark.ml.regression import GBTRegressor
from pyspark.ml.feature import VectorAssembler

# 特征工程
features = [
    "current_speed", "avg_speed_last_24h",
    "distance_to_destination", "weather_index",
    "port_congestion_level", "day_of_week"
]

# 梯度提升树回归
gbt = GBTRegressor(
    featuresCol="features",
    labelCol="actual_arrival_time",
    maxIter=100
)
```

---

### 方案二：Lambda架构 + 数据湖 ⭐⭐⭐⭐

**核心价值**: 展示大数据架构设计能力

#### 2.1 Lambda架构实现

```
┌─────────────────────────────────────────────────────┐
│                   数据源层                           │
│  MongoDB (AIS) + PostgreSQL (金融) + 外部API        │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌──────────────────┐          ┌──────────────────┐
│   批处理层        │          │   实时层          │
│  (Batch Layer)   │          │  (Speed Layer)   │
│                  │          │                  │
│  Spark Batch     │          │  Spark Streaming │
│  ↓               │          │  ↓               │
│  HDFS (Parquet)  │          │  MongoDB         │
└──────────────────┘          └──────────────────┘
        │                               │
        └───────────────┬───────────────┘
                        ↓
        ┌─────────────────────────────┐
        │       服务层                 │
        │    (Serving Layer)          │
        │                             │
        │  FastAPI + Redis Cache      │
        └─────────────────────────────┘
```

#### 2.2 数据分层存储策略

**热数据（近7天）**:
- 存储: MongoDB
- 查询延迟: <100ms
- 用途: 实时监控、告警
- 数据量: ~1GB

**温数据（7-90天）**:
- 存储: MongoDB + Parquet (HDFS)
- 查询延迟: <1s
- 用途: 趋势分析、报表
- 数据量: ~10GB

**冷数据（>90天）**:
- 存储: HDFS (Parquet分区表)
- 查询延迟: <1min
- 用途: 历史回溯、模型训练
- 数据量: ~100GB+

#### 2.3 增量ETL管道

**每日调度任务**:
```python
# spark_jobs/daily_etl.py

1. 数据采集 (00:00-01:00)
   - 从MongoDB读取昨日新增数据
   - 数据质量检查

2. 数据清洗 (01:00-02:00)
   - 去重、填充缺失值
   - 异常值处理

3. 特征工程 (02:00-03:00)
   - 计算衍生特征
   - 时间窗口聚合

4. 数据归档 (03:00-04:00)
   - 写入HDFS分区表
   - 更新元数据

5. 索引更新 (04:00-05:00)
   - 更新Hive元数据
   - 刷新查询缓存
```

---

### 方案三：机器学习风险评分系统 ⭐⭐⭐⭐⭐

**核心价值**: 展示AI+大数据的综合能力

#### 3.1 多维度风险评分模型

**特征工程**:
```python
# 轨迹行为特征（20+维度）
trajectory_features = {
    # 速度特征
    "avg_speed": 平均速度,
    "speed_variance": 速度方差,
    "max_speed": 最大速度,
    "speed_change_rate": 速度变化率,

    # 航向特征
    "course_variance": 航向方差,
    "turn_frequency": 转向频率,
    "zigzag_index": 之字形指数,

    # 停泊特征
    "anchor_count": 停泊次数,
    "avg_anchor_duration": 平均停泊时长,
    "night_anchor_ratio": 夜间停泊比例,

    # 地理特征
    "high_risk_area_time": 高风险区域停留时间,
    "port_visit_frequency": 港口访问频率,
    "route_deviation": 航线偏离度,

    # 时间特征
    "night_sailing_ratio": 夜间航行比例,
    "weekend_activity": 周末活动度,
    "irregular_schedule": 不规律性指数
}

# 金融特征（15+维度）
financial_features = {
    "credit_score": 信用评分,
    "debt_ratio": 负债率,
    "overdue_count": 逾期次数,
    "asset_quality": 资产质量,
    ...
}
```

**模型训练**:
```python
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator

# 梯度提升树分类器
gbt = GBTClassifier(
    featuresCol="features",
    labelCol="is_high_risk",
    maxIter=100,
    maxDepth=5,
    stepSize=0.1
)

# 交叉验证
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

paramGrid = ParamGridBuilder() \
    .addGrid(gbt.maxDepth, [3, 5, 7]) \
    .addGrid(gbt.maxIter, [50, 100, 150]) \
    .build()

cv = CrossValidator(
    estimator=gbt,
    estimatorParamMaps=paramGrid,
    evaluator=BinaryClassificationEvaluator(),
    numFolds=5
)

model = cv.fit(train_data)
```

#### 3.2 SHAP可解释性分析

**功能**:
- 为每个风险评分提供解释
- 识别关键风险因素
- 可视化特征贡献度

**实现**:
```python
import shap

# 计算SHAP值
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# 存储到MongoDB
{
    "imo_number": "IMO9000001",
    "risk_score": 75.3,
    "risk_level": "high",
    "shap_values": {
        "avg_speed": -2.3,
        "anchor_count": 5.7,
        "high_risk_area_time": 8.9,
        "credit_score": -3.2,
        ...
    },
    "top_risk_factors": [
        {"factor": "high_risk_area_time", "contribution": 8.9},
        {"factor": "anchor_count", "contribution": 5.7},
        {"factor": "debt_ratio", "contribution": 4.2}
    ]
}
```

#### 3.3 在线学习与模型更新

**模型版本管理**:
```python
# 模型版本表
model_versions = {
    "version": "v1.2.3",
    "train_date": "2026-02-22",
    "metrics": {
        "auc": 0.89,
        "precision": 0.85,
        "recall": 0.82,
        "f1": 0.83
    },
    "feature_importance": {...},
    "model_path": "hdfs:///models/risk_scoring/v1.2.3"
}
```

---

## 🔧 立即执行计划

### 阶段1: 运行现有Spark分析（1小时）

**目标**: 生成vessel_statistics和ais_anomalies

**执行步骤**:
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

# 方式1: 使用本地Spark
./run_spark_analysis_local.sh

# 方式2: 使用云端Spark（推荐）
ssh user@1.15.225.134
cd /path/to/project
./run_spark_analysis.sh
```

**预期结果**:
- vessel_statistics: 100条记录
- ais_anomalies: 500-1000条记录

---

### 阶段2: 开发实时异常检测（2-3天）

**任务清单**:
1. ✅ 创建Spark Streaming作业
2. ✅ 实现滑动窗口聚合
3. ✅ 开发异常检测算法
4. ✅ 集成实时告警

**代码框架**:
```python
# spark_jobs/streaming_anomaly_detection.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import window, avg, stddev

spark = SparkSession.builder \
    .appName("RealTimeAnomalyDetection") \
    .config("spark.mongodb.input.uri", mongo_uri) \
    .getOrCreate()

# 读取流数据
stream_df = spark.readStream \
    .format("mongodb") \
    .option("collection", "ais_tracks") \
    .load()

# 滑动窗口聚合
windowed_df = stream_df \
    .groupBy(
        window("timestamp", "10 minutes", "5 minutes"),
        "imo_number"
    ) \
    .agg(
        avg("speed").alias("avg_speed"),
        stddev("speed").alias("speed_stddev")
    )

# 异常检测
anomaly_df = windowed_df.filter(
    "speed_stddev > 5.0 OR avg_speed < 1.0"
)

# 写入结果
query = anomaly_df.writeStream \
    .format("mongodb") \
    .option("collection", "realtime_anomalies") \
    .outputMode("append") \
    .start()

query.awaitTermination()
```

---

### 阶段3: 实现数据分层存储（1-2天）

**任务清单**:
1. ✅ 配置HDFS连接
2. ✅ 开发数据归档作业
3. ✅ 实现冷热分离策略
4. ✅ 创建Hive外部表

**代码框架**:
```python
# spark_jobs/data_tiering.py

# 归档90天前的数据到HDFS
old_data = spark.read \
    .format("mongodb") \
    .option("collection", "ais_tracks") \
    .load() \
    .filter("timestamp < date_sub(current_date(), 90)")

# 按月分区写入HDFS
old_data.write \
    .partitionBy("year", "month") \
    .mode("append") \
    .parquet("hdfs:///silvernav/ais_tracks_archive")

# 从MongoDB删除已归档数据
# (保留最近90天)
```

---

### 阶段4: 开发ML风险评分系统（3-4天）

**任务清单**:
1. ✅ 特征工程（20+维度）
2. ✅ 模型训练（GBT/RandomForest）
3. ✅ SHAP可解释性分析
4. ✅ 模型部署与API集成

**代码框架**:
```python
# spark_jobs/ml_risk_scoring.py

# 特征工程
feature_df = spark.sql("""
    SELECT
        imo_number,
        AVG(speed) as avg_speed,
        STDDEV(speed) as speed_variance,
        COUNT(CASE WHEN speed < 1 THEN 1 END) as anchor_count,
        SUM(CASE WHEN hour(timestamp) BETWEEN 18 AND 6 THEN 1 ELSE 0 END) / COUNT(*) as night_ratio,
        ...
    FROM ais_tracks
    GROUP BY imo_number
""")

# 合并金融特征
final_df = feature_df.join(financial_df, "imo_number")

# 训练模型
from pyspark.ml.classification import GBTClassifier

gbt = GBTClassifier(
    featuresCol="features",
    labelCol="is_high_risk",
    maxIter=100
)

model = gbt.fit(train_data)

# 保存模型
model.save("hdfs:///models/risk_scoring/v1.0.0")
```

---

## 📊 技术亮点总结

### 大数据技术栈
1. **Spark Batch**: 批处理分析（已实现）
2. **Spark Streaming**: 实时流式计算（待开发）
3. **Spark MLlib**: 机器学习（待开发）
4. **HDFS**: 数据湖存储（待集成）
5. **Parquet**: 列式存储格式
6. **Hive**: 数据仓库（可选）

### 算法与模型
1. **DBSCAN**: 密度聚类（航线识别）
2. **KMeans**: K均值聚类（行为分组）
3. **GBT**: 梯度提升树（风险评分）
4. **RandomForest**: 随机森林（分类）
5. **ARIMA**: 时间序列预测（ETA）
6. **SHAP**: 模型可解释性

### 架构模式
1. **Lambda架构**: 批处理+实时处理
2. **数据分层**: 热温冷三层存储
3. **增量ETL**: 每日增量处理
4. **模型版本管理**: MLOps实践

---

## 🎯 项目专业性提升

### 技术深度
- ✅ 从单一批处理 → 批流一体
- ✅ 从简单统计 → 机器学习
- ✅ 从单一存储 → 数据湖架构
- ✅ 从黑盒模型 → 可解释AI

### 工程能力
- ✅ 大规模数据处理（200万+记录）
- ✅ 实时计算（秒级延迟）
- ✅ 分布式存储（HDFS）
- ✅ 模型训练与部署

### 业务价值
- ✅ 实时异常检测（降低风险）
- ✅ 智能风险评分（辅助决策）
- ✅ 航线优化建议（降低成本）
- ✅ ETA预测（提升效率）

---

## 📅 时间规划

| 阶段 | 任务 | 工作量 | 优先级 |
|------|------|--------|--------|
| 1 | 运行现有Spark分析 | 1小时 | P0 |
| 2 | 实时异常检测系统 | 2-3天 | P1 |
| 3 | 数据分层存储 | 1-2天 | P1 |
| 4 | ML风险评分系统 | 3-4天 | P2 |
| 5 | 前端可视化增强 | 1-2天 | P2 |

**总计**: 1-2周完成核心功能

---

## 🚀 立即开始

### 第一步: 运行Spark分析
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
./run_spark_analysis_local.sh
```

### 第二步: 验证结果
```bash
python3 -c "
from pymongo import MongoClient
from app.config import settings
client = MongoClient(f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}')
db = client[settings.mongo_db]
print(f'vessel_statistics: {db.vessel_statistics.count_documents()}')
print(f'ais_anomalies: {db.ais_anomalies.count_documents({})}')
"
```

### 第三步: 启动服务测试
```bash
python3 main.py
# 访问: http://localhost:8000/behavior
```

---

**创建时间**: 2026-02-22
**作者**: 孙帆（Sunstar）
**项目**: 银航宝·航运金融数智风控平台
**版本**: v2.0 - 大数据深化方案
