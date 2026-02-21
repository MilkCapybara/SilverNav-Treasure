# Phase 2 执行计划：2000万条AIS数据 + 完整集成

## 📋 升级概述

**目标**：将MongoDB数据量从200万升级到2000万，完成Phase 2所有功能

**升级内容**：
1. ✅ 修改数据生成脚本（200万 → 2000万）
2. ✅ 集成behavior_api到main.py
3. 🔄 生成2000万条AIS轨迹数据
4. 🔄 运行Spark分析作业
5. 🔄 测试API端点
6. 📋 前端页面开发（可选）

---

## 🎯 数据规模设计

### 原方案（200万条）
- 船舶数量：100艘
- 每艘船记录数：20,000条
- 时间跨度：90天
- 每条航线：72小时（72个点）
- 每艘船航线数：278条
- 预计数据大小：~1GB

### 新方案（2000万条）
- 船舶数量：100艘
- 每艘船记录数：200,000条
- 时间跨度：900天（约2.5年）
- 每条航线：72小时（72个点）
- 每艘船航线数：2,778条
- 预计数据大小：~10GB

**优势**：
- ✅ 真正的大数据规模（千万级）
- ✅ 更长的历史数据（2.5年）
- ✅ 更能体现Spark/MongoDB的性能优势
- ✅ 满足课设对大数据处理的要求

---

## 📊 技术架构

```
数据生成层
    ↓
  Python脚本
  generate_ais_data.py
    ↓
MongoDB存储层
  ├─ ais_tracks (2000万条)
  ├─ vessel_statistics (Spark生成)
  └─ ais_anomalies (Spark生成)
    ↓
Spark分析层
  ├─ ais_trajectory_analysis.py
  │   ├─ 轨迹聚合统计
  │   ├─ 异常停泊检测
  │   └─ 多维度分析
  └─ mongo_to_hdfs.py
      └─ 历史数据归档
    ↓
FastAPI服务层
  └─ behavior_api.py
      ├─ /api/behavior/tracks
      ├─ /api/behavior/anomalies
      ├─ /api/behavior/geofence
      ├─ /api/behavior/statistics
      └─ /api/behavior/summary
    ↓
前端展示层（可选）
  └─ behavior.html
      └─ Leaflet.js地图
```

---

## 🚀 执行步骤

### Step 1: 生成2000万条AIS数据（预计30-60分钟）

```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
python3 scripts/generate_ais_data.py
```

**预期输出**：
```
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
  已插入 20,000 条记录 (0.2%)
  ...
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
```

**注意事项**：
- 数据生成过程较长（30-60分钟），建议后台运行
- 确保MongoDB有足够磁盘空间（至少15GB）
- 可以使用`nohup`或`screen`后台运行

---

### Step 2: 运行Spark轨迹分析作业（预计10-20分钟）

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

**预期输出**：
```
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
+------------+-------------+---------------+-----+-----------+---------+---------+---------+
|imo_number  |vessel_name  |ship_type      |flag |track_count|avg_speed|max_speed|min_speed|
+------------+-------------+---------------+-----+-----------+---------+---------+---------+
|IMO9000001  |VESSEL_001   |Container Ship |CN   |199500     |12.5     |18.0     |0.0      |
...

💾 写入统计结果到MongoDB...
✅ 统计结果已写入 vessel_statistics 集合

🔍 异常停泊检测...
✅ 检测到 1,234 次异常停泊

前10次异常停泊：
+------------+-------------+-------------------+----------+-----+--------+---------------+
|imo_number  |vessel_name  |timestamp          |position  |speed|status  |time_diff_hours|
+------------+-------------+-------------------+----------+-----+--------+---------------+
...

💾 写入异常停泊记录到MongoDB...
✅ 异常停泊记录已写入 ais_anomalies 集合

📊 按船舶类型统计...
📊 按国旗统计...
⚓ 按状态统计...

✅ Spark作业执行完成！
```

---

### Step 3: 运行MongoDB → HDFS归档作业（可选）

```bash
# 设置HDFS环境变量
export HDFS_BASE=hdfs:///silvernav/archive

# 运行归档作业
spark-submit \
  --master local[*] \
  --driver-memory 4g \
  --executor-memory 4g \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
  spark_jobs/mongo_to_hdfs.py
```

**功能**：
- 将超过90天的历史数据归档到HDFS
- Parquet列式存储格式
- 按日期分区（year/month/day）

---

### Step 4: 测试API端点

```bash
# 启动FastAPI服务
python3 main.py
```

**测试API**：

1. **获取行为分析总览**
```bash
curl -X GET http://localhost:8000/api/behavior/summary
```

2. **获取船舶轨迹**
```bash
curl -X POST http://localhost:8000/api/behavior/tracks \
  -H "Content-Type: application/json" \
  -d '{
    "imo_number": "IMO9000001",
    "start_date": "2025-11-01T00:00:00",
    "end_date": "2025-11-30T23:59:59",
    "limit": 1000
  }'
```

3. **获取异常停泊记录**
```bash
curl -X POST http://localhost:8000/api/behavior/anomalies \
  -H "Content-Type: application/json" \
  -d '{
    "imo_number": "IMO9000001",
    "limit": 50
  }'
```

4. **地理围栏查询**
```bash
curl -X POST http://localhost:8000/api/behavior/geofence \
  -H "Content-Type: application/json" \
  -d '{
    "min_lng": 121.0,
    "max_lng": 122.0,
    "min_lat": 30.0,
    "max_lat": 32.0,
    "start_date": "2025-11-01T00:00:00",
    "limit": 100
  }'
```

5. **获取船舶统计**
```bash
curl -X POST http://localhost:8000/api/behavior/statistics \
  -H "Content-Type: application/json" \
  -d '{
    "ship_type": "Container Ship",
    "limit": 20
  }'
```

---

### Step 5: 前端页面开发（可选）

创建`templates/behavior.html`和`static/js/behavior.js`，使用Leaflet.js展示轨迹地图。

**功能**：
- 船舶轨迹地图展示
- 实时位置标注
- 异常停泊高亮
- 轨迹回放

---

## 📊 性能预估

### 数据生成性能
- 批量插入：10,000条/批次
- 插入速度：~10,000条/秒
- 总耗时：~30-60分钟

### Spark分析性能
- 读取速度：~1,000,000条/秒
- 聚合计算：~5-10分钟
- 异常检测：~5-10分钟
- 总耗时：~10-20分钟

### API查询性能
- 单船轨迹查询（1000条）：<500ms
- 地理围栏查询（100条）：<300ms
- 统计查询：<200ms

---

## 🎯 课设价值点

### 1. 大数据规模 ✅
- **2000万条记录**：真正的大数据规模
- **10GB数据量**：体现存储和处理能力
- **100艘船舶 × 2.5年历史**：真实业务场景

### 2. 非结构化数据处理 ✅
- **MongoDB存储**：非结构化AIS轨迹数据
- **GeoJSON格式**：地理空间数据
- **时间序列数据**：按时间排序的轨迹点

### 3. 大数据技术栈 ✅
- **Spark + MongoDB Connector**：分布式读写
- **Spark DataFrame API**：分布式计算
- **Window函数**：复杂分析
- **HDFS归档**：冷热数据分离

### 4. 完整的数据处理流程 ✅
- **采集**：Python生成模拟数据
- **存储**：MongoDB存储非结构化数据
- **处理**：Spark分析处理
- **归档**：HDFS冷数据存储
- **服务**：FastAPI提供查询接口

### 5. 技术深度 ✅
- **地理空间索引**：2dsphere索引
- **复合索引优化**：imo_number + timestamp
- **批量写入优化**：bulk_write
- **分区存储**：按日期分区
- **列式存储**：Parquet格式

---

## 📝 验收标准

### 数据层
- ✅ MongoDB存储2000万条AIS轨迹记录
- ✅ 数据时间跨度覆盖2.5年
- ✅ 地理空间索引创建成功
- ✅ 数据完整性验证通过

### 处理层
- ✅ Spark成功读取2000万条记录
- ✅ 聚合统计生成100艘船舶的统计信息
- ✅ 异常检测识别出异常停泊记录
- ✅ 结果写回MongoDB成功

### 服务层
- ✅ 5个API端点全部可用
- ✅ API响应时间<500ms
- ✅ 支持分页和过滤
- ✅ 错误处理完善

### 文档层
- ✅ 技术文档完整
- ✅ API文档清晰
- ✅ 执行步骤详细
- ✅ 性能数据真实

---

## 🚀 立即开始

准备好了吗？让我们开始执行！

**第一步**：生成2000万条AIS数据
```bash
python3 scripts/generate_ais_data.py
```

**第二步**：运行Spark分析作业
```bash
spark-submit --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 spark_jobs/ais_trajectory_analysis.py
```

**第三步**：启动API服务并测试
```bash
python3 main.py
```

---

**更新时间**：2026-02-21
**开发者**：Claude (Sonnet 4.5)
**项目状态**：Phase 2 执行中
