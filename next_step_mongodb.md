# 下一步规划：船舶行为分析页面深度开发（MongoDB数据驱动）

## 📋 项目当前状态总结

### ✅ 已完成的核心功能

#### Phase 0 - MVP基础功能（100%完成）
- ✅ 用户认证系统（JWT Token + bcrypt加密）
- ✅ 数据大屏（8大核心板块）
- ✅ 多币种/多单位/多时间维度支持
- ✅ PostgreSQL数据库设计（12张表）
- ✅ FastAPI后端架构（31个API端点）
- ✅ Spark批处理作业（4个作业）

#### Phase 1 - 详情页面开发（100%完成）
- ✅ 8个详情页面全部完成
- ✅ 数据钻取功能完整
- ✅ 图表展示（环形图、折线图、柱状图）
- ✅ 表格渲染与多维度筛选

#### Phase 2 - 船舶行为分析页面（90%完成）
- ✅ 前端页面开发（behavior.html - 5.3KB）
- ✅ CSS样式设计（behavior.css - 5.0KB）
- ✅ JavaScript逻辑（behavior.js - 12KB）
- ✅ 后端API集成（5个端点）
- ✅ Leaflet.js地图集成
- ✅ Chart.js图表集成
- ✅ Spark分析作业（ais_trajectory_analysis.py）
- ⚠️ **MongoDB数据为空**（0条记录）

### 🚨 当前问题

**核心问题：MongoDB数据库为空**
```
当前数据量:
  ais_tracks: 0
  ais_anomalies: 0
  vessel_statistics: 0
```

**原因分析**：
1. 数据生成脚本可能未成功运行
2. 或者数据生成任务被中断
3. 需要重新生成2000万条AIS轨迹数据

---

## 🎯 下一步核心任务：MongoDB数据生成与分析

### 任务优先级

| 优先级 | 任务名称 | 预计工作量 | 状态 |
|--------|---------|-----------|------|
| 🔴 P0 | 生成200万条AIS轨迹数据 | 1-2小时 | 待执行 |
| 🔴 P0 | 运行Spark轨迹分析作业 | 30分钟 | 待执行 |
| 🟡 P1 | 验证behavior页面完整功能 | 1小时 | 待执行 |
| 🟡 P1 | 性能优化与索引调优 | 2-3小时 | 待执行 |
| 🟢 P2 | 功能增强（热力图、轨迹回放） | 1-2天 | 可选 |

---

## 📊 任务1：生成2000万条AIS轨迹数据（P0）

### 目标
生成2000万条AIS轨迹记录，覆盖100艘船舶，时间跨度900天（约2.5年）

### 数据规模
- **总记录数**：20,000,000条
- **船舶数量**：100艘
- **每艘船记录数**：200,000条
- **时间跨度**：900天（2022-08-01 至 2025-02-21）
- **预计数据大小**：约10GB
- **预计生成时间**：30-60分钟

### 数据结构
```javascript
// ais_tracks 集合
{
  _id: ObjectId("..."),
  imo_number: "IMO9000001",
  vessel_name: "COSCO SHIPPING GALAXY",
  ship_type: "Container Ship",
  timestamp: ISODate("2025-02-20T10:30:00Z"),
  position: {
    type: "Point",
    coordinates: [121.4737, 31.2304]  // [经度, 纬度]
  },
  latitude: 31.2304,
  longitude: 121.4737,
  speed: 12.5,        // 节（knots）
  course: 90.0,       // 度（0-360）
  heading: 92.0,      // 度（0-360）
  status: "underway using engine",
  destination: "SHANGHAI",
  eta: ISODate("2025-02-21T08:00:00Z"),
  draught: 12.5,      // 吃水深度（米）
  rot: 0.0            // 转向率（度/分钟）
}
```

### 执行步骤

#### 步骤1：检查数据生成脚本
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
cat scripts/generate_ais_data.py | head -20
```

**验证点**：
- 目标记录数是否为20,000,000
- MongoDB连接配置是否正确
- 批量写入大小是否合理（建议1000-5000条/批）

#### 步骤2：运行数据生成脚本
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
nohup python3 scripts/generate_ais_data.py > logs/generate_ais_data.log 2>&1 &
```

**监控命令**：
```bash
# 查看进度
tail -f logs/generate_ais_data.log

# 查看MongoDB数据量
python3 -c "from pymongo import MongoClient; from app.config import settings; client = MongoClient(f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'); count = client[settings.mongo_db]['ais_tracks'].count_documents({}); print(f'进度: {count:,} / 20,000,000 ({count/20000000*100:.2f}%)'); client.close()"
```

#### 步骤3：创建MongoDB索引
```bash
python3 << 'EOF'
from pymongo import MongoClient, ASCENDING, DESCENDING, GEOSPHERE
from app.config import settings

client = MongoClient(
    f'mongodb://{settings.mongo_user}:{settings.mongo_password}'
    f'@{settings.mongo_host}:{settings.mongo_port}'
    f'/{settings.mongo_db}?authSource={settings.mongo_auth_source}'
)
db = client[settings.mongo_db]

print("创建索引...")

# ais_tracks 集合索引
db.ais_tracks.create_index([("imo_number", ASCENDING), ("timestamp", ASCENDING)])
db.ais_tracks.create_index([("timestamp", DESCENDING)])
db.ais_tracks.create_index([("position", GEOSPHERE)])  # 地理空间索引
db.ais_tracks.create_index([("ship_type", ASCENDING)])

# ais_anomalies 集合索引
db.ais_anomalies.create_index([("imo_number", ASCENDING)])
db.ais_anomalies.create_index([("timestamp", DESCENDING)])
db.ais_anomalies.create_index([("anomaly_type", ASCENDING)])

# vessel_statistics 集合索引
db.vessel_statistics.create_index([("imo_number", ASCENDING)], unique=True)
db.vessel_statistics.create_index([("track_count", DESCENDING)])

print("索引创建完成！")
client.close()
EOF
```

### 预期结果
- ✅ ais_tracks集合：20,000,000条记录
- ✅ 索引创建完成（4个索引）
- ✅ 数据完整性验证通过

---

## 📊 任务2：运行Spark轨迹分析作业（P0）

### 目标
对2000万条AIS轨迹数据进行分布式分析，生成船舶统计和异常检测结果

### Spark作业功能

#### 作业1：ais_trajectory_analysis.py
**功能**：
1. 从MongoDB读取AIS轨迹数据
2. 按船舶分组统计：
   - 轨迹点数量
   - 平均速度
   - 最大速度
   - 总航行距离
   - 活跃天数
3. 异常停泊检测（停泊时间>24小时）
4. 结果写回MongoDB

**输出集合**：
- `vessel_statistics`：船舶统计数据
- `ais_anomalies`：异常停泊记录

#### 作业2：mongo_to_hdfs.py
**功能**：
1. 从MongoDB读取历史AIS数据（>90天）
2. 按月份分区存储到HDFS
3. 实现冷热数据分离

**输出路径**：
- `hdfs:///silvernav/ais_tracks/year=2024/month=11/`
- `hdfs:///silvernav/ais_tracks/year=2024/month=12/`

### 执行步骤

#### 步骤1：配置环境变量
```bash
export SILVERNAV_MONGO_HOST="1.15.225.134"
export SILVERNAV_MONGO_PORT="27017"
export SILVERNAV_MONGO_DB="silvernav"
export SILVERNAV_MONGO_USER="admin"
export SILVERNAV_MONGO_PASSWORD="sun2137405"
export SILVERNAV_MONGO_AUTH_SOURCE="admin"
```

#### 步骤2：运行Spark分析作业
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

# 运行轨迹分析
spark-submit \
  --master local[4] \
  --driver-memory 4g \
  --executor-memory 4g \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
  spark_jobs/ais_trajectory_analysis.py

# 查看结果
python3 -c "from pymongo import MongoClient; from app.config import settings; client = MongoClient(f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'); db = client[settings.mongo_db]; print(f'vessel_statistics: {db.vessel_statistics.count_documents({})}'); print(f'ais_anomalies: {db.ais_anomalies.count_documents({})}'); client.close()"
```

#### 步骤3：验证分析结果
```bash
# 查看船舶统计样例
python3 << 'EOF'
from pymongo import MongoClient
from app.config import settings

client = MongoClient(
    f'mongodb://{settings.mongo_user}:{settings.mongo_password}'
    f'@{settings.mongo_host}:{settings.mongo_port}'
    f'/{settings.mongo_db}?authSource={settings.mongo_auth_source}'
)
db = client[settings.mongo_db]

print("=== 船舶统计样例 ===")
for doc in db.vessel_statistics.find().limit(5):
    print(f"IMO: {doc['imo_number']}, 轨迹点: {doc['track_count']}, 平均速度: {doc['avg_speed']:.2f}节")

print("\n=== 异常停泊样例 ===")
for doc in db.ais_anomalies.find().limit(5):
    print(f"IMO: {doc['imo_number']}, 停泊时长: {doc['duration_hours']:.1f}小时, 位置: ({doc['latitude']:.4f}, {doc['longitude']:.4f})")

client.close()
EOF
```

### 预期结果
- ✅ vessel_statistics集合：100条记录（每艘船1条）
- ✅ ais_anomalies集合：约500-1000条异常记录
- ✅ Spark作业执行时间：10-20分钟

---

## 📊 任务3：验证behavior页面完整功能（P1）

### 测试场景

#### 场景1：数据概览加载
**测试步骤**：
1. 访问 http://localhost:8000/behavior
2. 检查左侧数据概览卡片
3. 验证数据：
   - 总轨迹点数：20,000,000
   - 船舶数量：100
   - 异常停泊数：500-1000
   - 数据时间跨度：2022-08-01 至 2025-02-21

**预期结果**：
- ✅ 数据正确加载
- ✅ 船舶类型分布图显示
- ✅ 无错误提示

#### 场景2：船舶轨迹查询
**测试步骤**：
1. 输入IMO编号：`IMO9000001`
2. 选择时间范围：`近30天`
3. 点击"🔍 查询轨迹"
4. 观察地图显示

**预期结果**：
- ✅ 地图显示轨迹线（蓝色折线）
- ✅ 起点标记（绿色）
- ✅ 终点标记（红色）
- ✅ 中间点标记（根据速度着色）
- ✅ 点击标记显示详细信息
- ✅ 地图自动适应边界

#### 场景3：异常停泊查看
**测试步骤**：
1. 查看右侧异常列表
2. 点击任意异常记录
3. 观察地图定位

**预期结果**：
- ✅ 异常列表显示（按时间倒序）
- ✅ 点击后地图定位到异常位置
- ✅ 显示停泊时长和详细信息

#### 场景4：地理围栏查询
**测试步骤**：
1. 选择预设区域：`上海港周边`
2. 点击"🔍 查询区域船舶"
3. 观察地图显示

**预期结果**：
- ✅ 地图显示区域边界（矩形）
- ✅ 显示区域内所有船舶位置
- ✅ 显示船舶数量统计

#### 场景5：速度分布图
**测试步骤**：
1. 查询任意船舶轨迹
2. 查看右侧速度分布图

**预期结果**：
- ✅ 柱状图显示速度分布
- ✅ X轴：速度区间（0-5, 5-10, 10-15, 15-20, 20+节）
- ✅ Y轴：轨迹点数量

### 性能指标

| 指标 | 目标值 | 测试方法 |
|------|--------|---------|
| 页面加载时间 | < 2秒 | 浏览器开发者工具 |
| API响应时间 | < 500ms | Network面板 |
| 地图渲染时间 | < 1秒 | 视觉观察 |
| 轨迹查询时间 | < 3秒 | Network面板 |
| 地理围栏查询 | < 2秒 | Network面板 |

---

## 📊 任务4：性能优化与索引调优（P1）

### 优化目标
- 查询响应时间 < 500ms
- 地图渲染流畅（60fps）
- 支持并发查询（10+用户）

### 优化策略

#### 1. MongoDB索引优化
```javascript
// 复合索引优化
db.ais_tracks.createIndex(
  { imo_number: 1, timestamp: 1 },
  { name: "idx_imo_time" }
)

// 地理空间索引
db.ais_tracks.createIndex(
  { position: "2dsphere" },
  { name: "idx_position" }
)

// 覆盖索引（避免回表）
db.ais_tracks.createIndex(
  { imo_number: 1, timestamp: 1, latitude: 1, longitude: 1, speed: 1 },
  { name: "idx_track_query" }
)
```

#### 2. 查询优化
```python
# 使用投影减少数据传输
collection.find(
    {"imo_number": imo},
    {"_id": 0, "latitude": 1, "longitude": 1, "speed": 1, "timestamp": 1}
).limit(1000)

# 使用聚合管道优化复杂查询
pipeline = [
    {"$match": {"imo_number": imo}},
    {"$sort": {"timestamp": 1}},
    {"$limit": 1000},
    {"$project": {
        "_id": 0,
        "lat": "$latitude",
        "lng": "$longitude",
        "speed": 1,
        "time": "$timestamp"
    }}
]
```

#### 3. 前端优化
```javascript
// 地图点聚合（大量标记时）
const markers = L.markerClusterGroup();

// 轨迹简化（减少渲染点数）
function simplifyTrack(points, tolerance = 0.001) {
    // Douglas-Peucker算法
    return L.LineUtil.simplify(points, tolerance);
}

// 分页加载
async function loadTracksPaginated(imo, page = 1, pageSize = 1000) {
    const offset = (page - 1) * pageSize;
    // 请求API with offset & limit
}
```

#### 4. 缓存策略
```python
# Redis缓存热点数据
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

# 缓存船舶统计数据（TTL 1小时）
cache_key = f"vessel_stats:{imo_number}"
cached = cache.get(cache_key)
if cached:
    return json.loads(cached)
else:
    data = query_vessel_statistics(imo_number)
    cache.setex(cache_key, 3600, json.dumps(data))
    return data
```

### 性能测试

#### 测试工具
```bash
# Apache Bench压力测试
ab -n 1000 -c 10 http://localhost:8000/api/behavior/summary

# 查询性能测试
python3 << 'EOF'
import time
from pymongo import MongoClient
from app.config import settings

client = MongoClient(...)
db = client[settings.mongo_db]

# 测试查询性能
start = time.time()
result = list(db.ais_tracks.find({"imo_number": "IMO9000001"}).limit(1000))
elapsed = time.time() - start
print(f"查询耗时: {elapsed:.3f}秒, 记录数: {len(result)}")
EOF
```

---

## 🚀 任务5：功能增强（P2 - 可选）

### 增强功能列表

#### 1. 轨迹回放功能
**功能描述**：
- 时间轴控制器（播放/暂停/快进/慢放）
- 船舶图标沿轨迹移动
- 显示当前时间和速度
- 支持多船舶同时回放

**技术实现**：
```javascript
class TrackPlayer {
    constructor(map, tracks) {
        this.map = map;
        this.tracks = tracks;
        this.currentIndex = 0;
        this.isPlaying = false;
        this.speed = 1; // 1x, 2x, 5x, 10x
    }

    play() {
        this.isPlaying = true;
        this.animate();
    }

    animate() {
        if (!this.isPlaying) return;

        const point = this.tracks[this.currentIndex];
        this.updateMarker(point);

        this.currentIndex++;
        if (this.currentIndex < this.tracks.length) {
            setTimeout(() => this.animate(), 1000 / this.speed);
        }
    }
}
```

#### 2. 热力图展示
**功能描述**：
- 显示船舶密度分布
- 支持时间范围筛选
- 动态调整热力图强度

**技术实现**：
```javascript
// Leaflet.heat插件
const heatLayer = L.heatLayer(heatData, {
    radius: 25,
    blur: 15,
    maxZoom: 17,
    gradient: {
        0.0: 'blue',
        0.5: 'lime',
        1.0: 'red'
    }
}).addTo(map);
```

#### 3. 多船舶对比
**功能描述**：
- 同时显示多艘船舶轨迹
- 不同颜色区分
- 对比统计数据（速度、距离、时间）

#### 4. 轨迹预测
**功能描述**：
- 基于历史轨迹预测未来位置
- 显示预测轨迹（虚线）
- 预测到达时间（ETA）

**技术实现**：
```python
# 使用线性回归预测
from sklearn.linear_model import LinearRegression

def predict_trajectory(historical_points, hours_ahead=24):
    # 训练模型
    X = [[p['timestamp']] for p in historical_points]
    y_lat = [p['latitude'] for p in historical_points]
    y_lng = [p['longitude'] for p in historical_points]

    model_lat = LinearRegression().fit(X, y_lat)
    model_lng = LinearRegression().fit(X, y_lng)

    # 预测未来位置
    future_times = [last_time + i*3600 for i in range(1, hours_ahead+1)]
    predicted_lat = model_lat.predict([[t] for t in future_times])
    predicted_lng = model_lng.predict([[t] for t in future_times])

    return list(zip(predicted_lat, predicted_lng))
```

#### 5. 数据导出功能
**功能描述**：
- 导出轨迹数据（CSV/Excel）
- 导出异常报告（PDF）
- 导出统计图表（PNG）

---

## 📅 执行时间表

### 第1天（2-3小时）
- ✅ 运行数据生成脚本（1-2小时）
- ✅ 创建MongoDB索引（10分钟）
- ✅ 验证数据完整性（10分钟）
- ✅ 运行Spark分析作业（30分钟）

### 第2天（3-4小时）
- ✅ 完整功能测试（1小时）
- ✅ 性能测试与优化（2小时）
- ✅ 文档更新（1小时）

### 第3天（可选，4-6小时）
- ⭐ 功能增强开发（轨迹回放、热力图等）
- ⭐ UI/UX改进
- ⭐ 移动端适配

---

## 📊 成功标准

### 数据完整性
- ✅ ais_tracks：20,000,000条记录
- ✅ vessel_statistics：100条记录
- ✅ ais_anomalies：500-1000条记录
- ✅ 索引创建完成（7个索引）

### 功能完整性
- ✅ 数据概览正确显示
- ✅ 船舶轨迹查询正常
- ✅ 异常停泊列表显示
- ✅ 地理围栏查询正常
- ✅ 图表展示正确
- ✅ Spark分析可触发

### 性能指标
- ✅ API响应时间 < 500ms
- ✅ 页面加载时间 < 2秒
- ✅ 地图渲染流畅
- ✅ 支持并发查询

### 用户体验
- ✅ 界面美观（航运金融科技风格）
- ✅ 交互流畅（无卡顿）
- ✅ 错误提示友好
- ✅ 加载状态清晰

---

## 🔧 技术栈总结

### 前端技术
- **HTML5 + CSS3**：页面结构与样式
- **原生JavaScript**：业务逻辑
- **Leaflet.js**：地图可视化
- **Chart.js**：图表展示
- **Canvas API**：动画效果

### 后端技术
- **FastAPI**：RESTful API框架
- **Python 3.12**：编程语言
- **Motor**：MongoDB异步驱动
- **Pydantic**：数据校验

### 数据库技术
- **MongoDB 7.0**：非结构化数据存储
- **2dsphere索引**：地理空间查询
- **复合索引**：查询优化
- **聚合管道**：复杂查询

### 大数据技术
- **Spark 3.5**：分布式计算
- **MongoDB Connector**：Spark-MongoDB集成
- **PySpark**：Python API
- **Window函数**：时间序列分析

---

## 📞 技术支持

**开发者**：孙帆（Sunstar）
**邮箱**：fandesunstar@outlook.com
**微信**：+86 18601657185

**相关文档**：
- `BEHAVIOR_QUICK_START.md` - 快速使用指南
- `BEHAVIOR_PAGE_REPORT.md` - 页面开发报告
- `PHASE2_FINAL_SUMMARY.md` - Phase 2完成总结
- `ROADMAP.md` - 项目路线图

---

## 🎯 立即开始

### 第一步：生成数据
```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
nohup python3 scripts/generate_ais_data.py > logs/generate_ais_data.log 2>&1 &
```

### 第二步：监控进度
```bash
tail -f logs/generate_ais_data.log
```

### 第三步：运行Spark分析
```bash
./run_spark_analysis.sh
```

### 第四步：测试页面
```bash
./start_server.sh
# 访问 http://localhost:8000/behavior
```

---

**创建时间**：2026-02-21
**项目状态**：Phase 2 开发完成，等待数据生成
**下一步**：生成2000万条AIS数据 → 运行Spark分析 → 完整功能测试
