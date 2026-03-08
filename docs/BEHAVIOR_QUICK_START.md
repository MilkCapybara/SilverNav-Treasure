# 船舶行为分析页面 - 快速使用指南

## 🚀 立即开始

### 1. 启动服务

```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
python3 main.py
```

或使用启动脚本：
```bash
./start_server.sh
```

### 2. 访问页面

**登录页面**: http://localhost:8000/
- 账号: `root`
- 密码: `sunfannb0307SF?`

**船舶行为分析页面**: http://localhost:8000/behavior

---

## 📊 页面功能说明

### 左侧控制面板

#### 1. 数据概览
- **总轨迹点数**: 显示MongoDB中的AIS记录总数
- **船舶数量**: 显示不同船舶的数量
- **异常停泊**: 显示检测到的异常停泊次数
- **数据时间跨度**: 显示数据的起止时间

#### 2. 船舶查询
- **IMO编号**: 输入船舶的IMO编号（例如：IMO9000001）
- **时间范围**: 选择查询的时间范围（7天/30天/90天/180天/1年）
- **查询按钮**: 点击后在地图上显示该船舶的轨迹

#### 3. Spark分析
三个Spark作业按钮：

**🚀 运行轨迹分析**
- 功能：分析所有船舶的轨迹数据
- 输出：生成vessel_statistics集合
- 耗时：约10-20分钟

**🔍 异常停泊检测**
- 功能：检测速度<1节且持续>24小时的异常停泊
- 输出：生成ais_anomalies集合
- 耗时：约5-10分钟

**📦 数据归档HDFS**
- 功能：将90天前的数据归档到HDFS
- 输出：HDFS中的Parquet文件
- 耗时：约5-10分钟

**注意**: 当前Spark作业需要在服务器端手动运行，前端按钮仅用于演示。

#### 4. 船舶类型分布图
- 饼图展示不同船舶类型的数量分布
- 自动从MongoDB加载数据
- 每30秒自动刷新

### 中间地图区域

#### 地图功能
- **缩放**: 鼠标滚轮或双击
- **平移**: 鼠标拖拽
- **标记点击**: 显示详细信息

#### 地图控制按钮
- **🎯 适应边界**: 自动调整地图视野以显示所有轨迹
- **🗑️ 清除轨迹**: 清除地图上的所有轨迹和标记
- **🔥 热力图**: 显示船舶密度热力图（开发中）

#### 地图图例
- **绿色圆点**: 正常航行（速度>5节）
- **橙色圆点**: 低速航行（1-5节）
- **蓝色圆点**: 锚泊（速度<1节）
- **红色圆点**: 异常停泊（持续>24小时）

### 右侧信息面板

#### 1. 异常停泊列表
- 显示最近20条异常停泊记录
- 点击任意记录可在地图上定位
- 显示船名、时间、停泊时长

#### 2. 速度分布图
- 柱状图展示不同速度区间的船舶数量
- 区间：0-5节、5-10节、10-15节、15-20节、>20节

#### 3. 地理围栏查询
预设4个港口区域：
- **上海港周边**: 121.0-122.0°E, 30.5-31.5°N
- **宁波港周边**: 121.3-122.0°E, 29.5-30.2°N
- **深圳港周边**: 113.8-114.3°E, 22.3-22.7°N
- **新加坡周边**: 103.6-104.0°E, 1.2-1.5°N

选择区域后点击"查询区域船舶"，地图上会显示该区域内的所有船舶。

#### 4. 船舶信息
显示当前选中船舶的详细信息：
- 船名
- IMO编号
- 船舶类型
- 国旗
- 当前速度
- 航向
- 状态

---

## 🎯 使用场景示例

### 场景1: 查询单艘船舶轨迹

1. 在左侧"船舶查询"面板输入IMO编号：`IMO9000001`
2. 选择时间范围：`近30天`
3. 点击"🔍 查询轨迹"按钮
4. 地图上显示该船舶的轨迹线
5. 点击轨迹上的标记点查看详细信息
6. 右侧面板显示船舶详细信息

### 场景2: 查看异常停泊

1. 右侧"异常停泊列表"自动加载最近的异常记录
2. 点击任意异常记录
3. 地图自动定位到该异常位置
4. 显示异常停泊的详细信息（时间、时长、位置）

### 场景3: 地理围栏查询

1. 在右侧"地理围栏查询"面板选择区域：`上海港周边`
2. 地图上显示矩形区域边界
3. 点击"🔍 查询区域船舶"按钮
4. 地图上显示该区域内的所有船舶位置
5. 点击船舶标记查看详细信息

### 场景4: 运行Spark分析

1. 点击左侧"⚡ Spark分析"面板的"🚀 运行轨迹分析"按钮
2. 确认对话框中点击"确定"
3. 状态指示器变为"运行中"（橙色）
4. 等待分析完成（实际需要在服务器端运行）
5. 完成后状态变为"就绪"（绿色）
6. 数据概览和异常列表自动刷新

---

## 🔧 手动运行Spark作业

### 1. 运行轨迹分析

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

### 2. 查看分析结果

分析完成后，MongoDB中会生成两个新集合：

**vessel_statistics** - 船舶统计信息
```javascript
{
  imo_number: "IMO9000001",
  vessel_name: "VESSEL_001",
  ship_type: "Container Ship",
  flag: "CN",
  track_count: 199500,
  avg_speed: 12.5,
  max_speed: 18.0,
  min_speed: 0.0,
  first_seen: ISODate("2023-08-15T00:00:00Z"),
  last_seen: ISODate("2026-02-21T23:00:00Z")
}
```

**ais_anomalies** - 异常停泊记录
```javascript
{
  imo_number: "IMO9000001",
  vessel_name: "VESSEL_001",
  timestamp: ISODate("2023-09-15T12:00:00Z"),
  position: {
    type: "Point",
    coordinates: [121.5, 31.2]
  },
  speed: 0.5,
  status: "at anchor",
  time_diff_hours: 26.5
}
```

---

## 📊 数据生成进度

### 当前状态

**数据生成任务**: 🔄 正在后台运行

**查看进度**:
```bash
python3 -c "from pymongo import MongoClient; from app.config import settings; client = MongoClient(f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'); count = client[settings.mongo_db]['ais_tracks'].count_documents({}); print(f'当前: {count:,} / 20,000,000 ({count/20000000*100:.2f}%)'); client.close()"
```

### 等待数据生成完成后

1. **运行Spark分析**
   ```bash
   ./run_spark_analysis.sh
   ```

2. **启动服务**
   ```bash
   ./start_server.sh
   ```

3. **访问页面**
   ```
   http://localhost:8000/behavior
   ```

4. **测试功能**
   - 查询船舶轨迹
   - 查看异常停泊
   - 地理围栏查询
   - 查看统计图表

---

## 🎨 页面截图说明

### 整体布局
```
┌─────────────────────────────────────────────────────────────┐
│  🚢 银航宝·船舶行为分析    [时钟]  [返回大屏]  [退出登录]  │
├──────────┬──────────────────────────────────┬───────────────┤
│          │                                  │               │
│  数据概览 │                                  │  异常停泊列表  │
│          │                                  │               │
│  船舶查询 │          地图区域                 │  速度分布图   │
│          │      (Leaflet.js)               │               │
│  Spark   │                                  │  地理围栏     │
│  分析    │                                  │  查询        │
│          │                                  │               │
│  船舶类型 │                                  │  船舶信息     │
│  分布图  │                                  │               │
│          │                                  │               │
└──────────┴──────────────────────────────────┴───────────────┘
```

### 配色方案
- **背景**: 深蓝渐变（#0f172a → #1a2332）
- **卡片**: 半透明深色（#1e293b）
- **主色**: 海洋蓝（#0ea5e9）
- **辅色**: 淡紫（#a78bfa）
- **文字**: 浅色（#f1f5f9）

---

## 🔗 相关文档

- **BEHAVIOR_PAGE_REPORT.md** - 页面开发完成报告（详细）
- **PHASE2_COMPLETE_GUIDE.md** - Phase 2完整指南
- **QUICK_START.md** - 快速启动指南
- **ROADMAP.md** - 项目路线图

---

## 📞 技术支持

**开发者**: 孙帆（Sunstar）
**邮箱**: fandesunstar@outlook.com
**微信**: +86 18601657185

---

## ✅ 完成清单

- [x] HTML页面开发（templates/behavior.html）
- [x] CSS样式开发（static/css/behavior.css）
- [x] JavaScript逻辑开发（static/js/behavior.js）
- [x] 路由集成（main.py）
- [x] API端点验证（app/behavior_api.py）
- [x] 地图功能（Leaflet.js）
- [x] 图表功能（Chart.js）
- [x] Spark分析按钮
- [x] 地理围栏查询
- [x] 异常停泊展示
- [x] 启动脚本（start_server.sh）
- [x] 使用文档（本文档）

---

**创建时间**: 2026-02-21 18:20
**页面状态**: ✅ 开发完成，可以使用
**下一步**: 启动服务并测试功能
