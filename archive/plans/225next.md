# 🚀 银航宝系统 - 下一步优化方案

**日期**: 2026-02-25
**版本**: v2.1.0 规划

---

## 📊 当前项目分析

### 已完成的页面
1. ✅ **总览大屏** (dashboard.html) - 风险敞口仪表盘
2. ✅ **船舶行为分析** (behavior.html) - AIS轨迹追踪
3. ✅ **船舶画像** (profile.html) - 综合数据分析
4. ✅ **数据血缘** (lineage.html) - 数据流转追踪
5. ✅ **详情页** (detail.html) - 详细信息展示

### 数据架构现状
```
数据源层:
├── PostgreSQL (silvernav_db)
│   ├── vessels (船舶信息)
│   ├── companies (企业信息)
│   ├── assets (资产信息)
│   ├── loans (贷款信息)
│   └── risk_assessments (风险评估)
│
└── MongoDB (silvernav)
    ├── ais_tracks (AIS轨迹 - 200万+)
    ├── vessel_statistics (船舶统计)
    ├── ais_anomalies (异常记录)
    └── vessel_analysis (船舶画像)

处理层:
└── Spark (批处理分析)
    ├── 轨迹统计
    ├── 异常检测
    └── 画像生成
```

### 性能瓶颈分析

#### 问题1: 大屏查询慢（20秒）
**原因分析**:
1. PostgreSQL直接查询，涉及多表JOIN
2. 复杂的聚合计算（SUM, AVG, GROUP BY）
3. 风险评分实时计算
4. 没有缓存机制
5. 数据量大，索引可能不够优化

**影响范围**:
- 用户体验差
- 并发能力弱
- 服务器压力大

---

## 🎯 核心优化方案：大屏性能提升（20s → 2s）

### 方案一：Redis缓存层 + 预计算（推荐）⭐⭐⭐⭐⭐

#### 架构设计
```
用户请求
    ↓
FastAPI
    ↓
Redis缓存 ←─────┐
    ↓ (miss)     │
PostgreSQL       │
    ↓            │
计算结果 ────────┘
    ↓
返回用户
```

#### 实现方案

**1. 引入Redis缓存**
```python
# app/cache.py
import redis
import json
from datetime import timedelta

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def get_dashboard_cache(base_date: str, range: str, currency: str):
    """获取大屏缓存数据"""
    cache_key = f"dashboard:{base_date}:{range}:{currency}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    return None

def set_dashboard_cache(base_date: str, range: str, currency: str, data: dict, ttl: int = 300):
    """设置大屏缓存（默认5分钟）"""
    cache_key = f"dashboard:{base_date}:{range}:{currency}"
    redis_client.setex(
        cache_key,
        ttl,
        json.dumps(data, ensure_ascii=False)
    )
```

**2. 预计算任务（定时任务）**
```python
# app/precompute.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

def precompute_dashboard_data():
    """预计算大屏数据"""
    # 计算今天、本月、近7天、近30天、近90天的数据
    today = datetime.now().date()
    
    for days_back in [0, 7, 30, 90]:
        base_date = today - timedelta(days=days_back)
        for range_type in ['today', 'month', '7d', '30d', '90d']:
            for currency in ['CNY', 'USD', 'HKD']:
                # 查询并计算
                data = compute_dashboard_metrics(base_date, range_type, currency)
                # 存入Redis
                set_dashboard_cache(str(base_date), range_type, currency, data, ttl=3600)
    
    print(f"✅ 预计算完成: {datetime.now()}")

# 启动定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(precompute_dashboard_data, 'interval', minutes=10)  # 每10分钟
scheduler.start()
```

**3. 修改大屏API**
```python
# main.py
@app.post("/api/dashboard")
async def dashboard(payload: DashboardQuery):
    # 1. 先查缓存
    cached_data = get_dashboard_cache(
        payload.base_date or str(today_cn()),
        payload.range,
        payload.currency
    )
    
    if cached_data:
        print("✅ 命中缓存")
        return JSONResponse(cached_data)
    
    # 2. 缓存未命中，查询数据库
    print("⚠️ 缓存未命中，查询数据库")
    data = compute_dashboard_metrics(
        payload.base_date,
        payload.range,
        payload.currency
    )
    
    # 3. 存入缓存
    set_dashboard_cache(
        payload.base_date or str(today_cn()),
        payload.range,
        payload.currency,
        data,
        ttl=300
    )
    
    return JSONResponse(data)
```

#### 性能提升
- **首次访问**: 20s → 15s（优化SQL）
- **缓存命中**: 15s → 0.5s（Redis读取）
- **预计算命中**: 0.5s → 0.1s（直接返回）
- **目标达成**: ✅ < 2s

#### 优点
- ✅ 实现简单，改动小
- ✅ 效果立竿见影
- ✅ 成本低（Redis内存）
- ✅ 可扩展性强

#### 缺点
- ⚠️ 需要维护缓存一致性
- ⚠️ 增加Redis依赖

---

### 方案二：物化视图 + 增量更新 ⭐⭐⭐⭐

#### 架构设计
```
PostgreSQL
    ↓
物化视图 (每小时刷新)
    ↓
FastAPI查询
    ↓
返回用户 (< 1s)
```

#### 实现方案

**1. 创建物化视图**
```sql
-- 创建大屏总览物化视图
CREATE MATERIALIZED VIEW mv_dashboard_overview AS
SELECT 
    DATE(base_date) as stat_date,
    currency,
    SUM(exposure_amount) as total_exposure,
    SUM(CASE WHEN risk_level = 'HIGH' THEN exposure_amount ELSE 0 END) as high_risk_exposure,
    COUNT(DISTINCT company_id) as company_count,
    COUNT(DISTINCT vessel_id) as vessel_count,
    AVG(risk_score) as avg_risk_score
FROM risk_assessments
GROUP BY DATE(base_date), currency;

-- 创建索引
CREATE INDEX idx_mv_dashboard_date ON mv_dashboard_overview(stat_date);
CREATE INDEX idx_mv_dashboard_currency ON mv_dashboard_overview(currency);

-- 定时刷新（每小时）
CREATE OR REPLACE FUNCTION refresh_dashboard_mv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_overview;
END;
$$ LANGUAGE plpgsql;
```

**2. 定时刷新任务**
```python
# app/materialized_view.py
from apscheduler.schedulers.background import BackgroundScheduler

def refresh_materialized_views():
    """刷新物化视图"""
    with db_conn("admin") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT refresh_dashboard_mv();")
        conn.commit()
    print(f"✅ 物化视图刷新完成: {datetime.now()}")

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_materialized_views, 'interval', hours=1)
scheduler.start()
```

**3. 修改查询逻辑**
```python
@app.post("/api/dashboard")
async def dashboard(payload: DashboardQuery):
    # 直接查询物化视图
    with db_conn("read") as conn:
        data = query_one(conn, """
            SELECT * FROM mv_dashboard_overview
            WHERE stat_date = %s AND currency = %s
        """, (payload.base_date, payload.currency))
    
    return JSONResponse(data)
```

#### 性能提升
- **查询时间**: 20s → 0.5s
- **目标达成**: ✅ < 2s

#### 优点
- ✅ 查询极快
- ✅ 数据库原生支持
- ✅ 不需要额外组件

#### 缺点
- ⚠️ 数据有延迟（最多1小时）
- ⚠️ 占用数据库存储空间

---

### 方案三：ClickHouse OLAP引擎 ⭐⭐⭐⭐⭐（终极方案）

#### 架构设计
```
PostgreSQL (OLTP)
    ↓ (ETL每小时)
ClickHouse (OLAP)
    ↓ (实时查询)
FastAPI
    ↓
返回用户 (< 0.5s)
```

#### 为什么选择ClickHouse？
1. **列式存储** - 聚合查询快10-100倍
2. **压缩率高** - 节省存储空间
3. **分布式** - 支持PB级数据
4. **实时写入** - 支持高并发写入
5. **SQL兼容** - 学习成本低

#### 实现方案

**1. 安装ClickHouse**
```bash
# Docker方式
docker run -d \
  --name clickhouse \
  -p 8123:8123 \
  -p 9000:9000 \
  --ulimit nofile=262144:262144 \
  clickhouse/clickhouse-server
```

**2. 创建ClickHouse表**
```sql
-- 风险敞口事实表
CREATE TABLE risk_exposure_fact (
    stat_date Date,
    company_id String,
    vessel_id String,
    asset_id String,
    currency String,
    exposure_amount Decimal(18, 2),
    risk_level String,
    risk_score Float32,
    created_at DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(stat_date)
ORDER BY (stat_date, company_id, vessel_id)
SETTINGS index_granularity = 8192;

-- 聚合物化视图（自动更新）
CREATE MATERIALIZED VIEW mv_daily_risk_summary
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(stat_date)
ORDER BY (stat_date, currency)
AS SELECT
    stat_date,
    currency,
    sum(exposure_amount) as total_exposure,
    sumIf(exposure_amount, risk_level = 'HIGH') as high_risk_exposure,
    uniq(company_id) as company_count,
    uniq(vessel_id) as vessel_count,
    avg(risk_score) as avg_risk_score
FROM risk_exposure_fact
GROUP BY stat_date, currency;
```

**3. ETL数据同步**
```python
# app/clickhouse_etl.py
from clickhouse_driver import Client

ch_client = Client(host='localhost', port=9000)

def sync_to_clickhouse():
    """同步PostgreSQL数据到ClickHouse"""
    # 1. 查询PostgreSQL增量数据
    with db_conn("read") as conn:
        rows = query_all(conn, """
            SELECT 
                DATE(created_at) as stat_date,
                company_id,
                vessel_id,
                asset_id,
                currency,
                exposure_amount,
                risk_level,
                risk_score,
                created_at
            FROM risk_assessments
            WHERE created_at > (
                SELECT max(created_at) FROM risk_exposure_fact
            )
        """, ())
    
    # 2. 批量插入ClickHouse
    if rows:
        ch_client.execute(
            'INSERT INTO risk_exposure_fact VALUES',
            rows
        )
        print(f"✅ 同步 {len(rows)} 条数据到ClickHouse")

# 定时同步（每10分钟）
scheduler = BackgroundScheduler()
scheduler.add_job(sync_to_clickhouse, 'interval', minutes=10)
scheduler.start()
```

**4. 修改大屏API**
```python
# app/clickhouse_api.py
from clickhouse_driver import Client

ch_client = Client(host='localhost', port=9000)

@app.post("/api/dashboard")
async def dashboard(payload: DashboardQuery):
    # 查询ClickHouse
    result = ch_client.execute("""
        SELECT 
            total_exposure,
            high_risk_exposure,
            company_count,
            vessel_count,
            avg_risk_score
        FROM mv_daily_risk_summary
        WHERE stat_date = %(date)s
          AND currency = %(currency)s
    """, {
        'date': payload.base_date or str(today_cn()),
        'currency': payload.currency
    })
    
    return JSONResponse({
        "success": True,
        "data": result[0] if result else {}
    })
```

#### 性能提升
- **查询时间**: 20s → 0.1s（200倍提升）
- **并发能力**: 10 QPS → 1000+ QPS
- **数据延迟**: 实时 → 10分钟
- **目标达成**: ✅✅✅ < 2s

#### 优点
- ✅ 性能极强（亿级数据秒级响应）
- ✅ 支持复杂分析查询
- ✅ 自动聚合和物化视图
- ✅ 分布式扩展能力
- ✅ 适合数据中台场景

#### 缺点
- ⚠️ 需要学习新技术
- ⚠️ 增加系统复杂度
- ⚠️ 需要ETL同步

---

## 🎯 推荐方案对比

| 方案 | 性能提升 | 实现难度 | 成本 | 可扩展性 | 推荐度 |
|------|---------|---------|------|---------|--------|
| Redis缓存 | ⭐⭐⭐⭐ | ⭐ | 低 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 物化视图 | ⭐⭐⭐ | ⭐⭐ | 低 | ⭐⭐ | ⭐⭐⭐⭐ |
| ClickHouse | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 分阶段实施建议

**第一阶段（立即实施）**: Redis缓存 + 预计算
- 时间：1-2天
- 效果：20s → 2s
- 风险：低

**第二阶段（1周内）**: 物化视图优化
- 时间：3-5天
- 效果：2s → 0.5s
- 风险：低

**第三阶段（1个月内）**: ClickHouse OLAP引擎
- 时间：1-2周
- 效果：0.5s → 0.1s
- 风险：中

---

## 📱 数据中台可视化 - 缺失页面分析

### 需要补充的页面

#### 1. 实时监控大屏 ⭐⭐⭐⭐⭐
**用途**: 实时监控系统运行状态

**功能**:
- 实时数据流量监控
- API调用统计
- 数据库连接池状态
- 错误率和响应时间
- 告警信息展示
- 内存监控
- 磁盘IO监控

**技术**:
- WebSocket实时推送
- ECharts折线图
- 自动刷新机制

---

#### 2. 数据质量监控页面 ⭐⭐⭐⭐⭐
**用途**: 监控数据质量指标

**功能**:
- 数据完整性检查
- 数据准确性验证
- 数据时效性监控
- 异常数据统计
- 质量趋势分析

**数据源**:
- MongoDB数据质量检查
- PostgreSQL数据验证
- 数据血缘追踪

---

#### 3. ETL任务管理页面 ⭐⭐⭐⭐
**用途**: 管理数据同步任务

**功能**:
- 任务列表展示
- 任务执行状态
- 任务日志查看
- 手动触发任务
- 任务调度配置

**技术**:
- APScheduler任务调度
- 任务状态追踪
- 日志实时查看

---

#### 4. 数据探索分析页面 ⭐⭐⭐⭐
**用途**: 自助数据分析

**功能**:
- SQL查询编辑器
- 数据表浏览
- 查询结果可视化
- 查询历史记录
- 结果导出功能

**技术**:
- Monaco Editor（代码编辑器）
- SQL语法高亮
- 结果表格展示
- 图表自动生成

---

#### 5. 指标配置管理页面 ⭐⭐⭐
**用途**: 配置业务指标

**功能**:
- 指标定义管理
- 计算规则配置
- 阈值告警设置
- 指标分类管理
- 指标血缘关系

---

#### 6. 用户权限管理页面 ⭐⭐⭐
**用途**: 管理用户和权限

**功能**:
- 用户列表管理
- 角色权限配置
- 数据权限控制
- 操作日志审计
- 登录日志查看

---

#### 7. 系统配置页面 ⭐⭐
**用途**: 系统参数配置

**功能**:
- 数据源配置
- 缓存配置
- 告警配置
- 系统参数设置
- 配置版本管理

---

## 🏗️ 技术架构升级建议

### 当前架构
```
前端: HTML + CSS + JavaScript
后端: FastAPI + Python
数据库: PostgreSQL + MongoDB
处理: Spark批处理
```

### 升级后架构
```
展示层:
├── 大屏可视化 (现有)
├── 数据探索 (新增)
└── 监控告警 (新增)

应用层:
├── FastAPI (现有)
├── WebSocket (新增 - 实时推送)
└── 任务调度 (新增 - APScheduler)

缓存层:
└── Redis (新增)
    ├── 查询缓存
    ├── 会话缓存
    └── 任务队列

数据层:
├── PostgreSQL (OLTP - 现有)
├── MongoDB (文档存储 - 现有)
├── ClickHouse (OLAP - 新增)
└── MinIO (对象存储 - 可选)

处理层:
├── Spark (批处理 - 现有)
├── Flink (流处理 - 可选)
└── ETL同步 (新增)
```

---

## 📋 实施计划

### Week 1: 性能优化
- [ ] Day 1-2: 实现Redis缓存层
- [ ] Day 3-4: 开发预计算任务
- [ ] Day 5: 测试和优化
- [ ] 目标: 大屏响应时间 < 2s

### Week 2: 监控页面
- [ ] Day 1-2: 实时监控大屏
- [ ] Day 3-4: 数据质量监控
- [ ] Day 5: 集成和测试

### Week 3: 管理页面
- [ ] Day 1-2: ETL任务管理
- [ ] Day 3-4: 数据探索分析
- [ ] Day 5: 用户权限管理

### Week 4: ClickHouse引入
- [ ] Day 1-2: ClickHouse部署和配置
- [ ] Day 3-4: ETL同步开发
- [ ] Day 5: 性能测试和优化

---

## 💰 成本估算

### 硬件成本
- Redis服务器: 4GB内存 - ¥200/月
- ClickHouse服务器: 16GB内存 - ¥800/月
- 总计: ¥1000/月

### 开发成本
- Redis缓存: 2人天
- 物化视图: 3人天
- ClickHouse: 10人天
- 新增页面: 15人天
- 总计: 30人天

### ROI分析
- 性能提升: 10倍
- 用户体验: 显著提升
- 并发能力: 100倍
- 投资回报: 高

---

## 🎯 关键指标

### 性能指标
- 大屏响应时间: 20s → < 2s ✅
- API并发能力: 10 QPS → 1000 QPS
- 缓存命中率: > 90%
- 数据延迟: < 10分钟

### 业务指标
- 用户满意度: 提升50%
- 系统可用性: > 99.9%
- 数据准确性: > 99%
- 告警响应时间: < 5分钟

---

## 📚 技术选型理由

### Redis vs Memcached
选择Redis因为:
- ✅ 支持更多数据结构
- ✅ 持久化能力
- ✅ 主从复制
- ✅ 发布订阅

### ClickHouse vs Druid vs Doris
选择ClickHouse因为:
- ✅ 查询性能最强
- ✅ SQL兼容性好
- ✅ 社区活跃
- ✅ 运维简单

---

## 🔧 实施细节

### Redis缓存策略
```python
# 缓存分层
L1: 热点数据 (TTL: 5分钟)
L2: 常用数据 (TTL: 30分钟)
L3: 冷数据 (TTL: 2小时)

# 缓存更新策略
- 主动刷新: 定时任务预计算
- 被动刷新: 缓存过期后重新计算
- 强制刷新: 数据变更时清除缓存
```

### SQL优化建议
```sql
-- 1. 添加索引
CREATE INDEX idx_risk_date ON risk_assessments(created_at);
CREATE INDEX idx_risk_company ON risk_assessments(company_id);
CREATE INDEX idx_risk_vessel ON risk_assessments(vessel_id);

-- 2. 分区表
CREATE TABLE risk_assessments_2026_02 PARTITION OF risk_assessments
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- 3. 查询优化
-- 避免SELECT *
-- 使用EXPLAIN分析
-- 合理使用JOIN
```

---

## 🎉 预期效果

### 性能提升
- ✅ 大屏加载: 20s → 1s (20倍)
- ✅ 并发能力: 10 → 1000 QPS (100倍)
- ✅ 用户体验: 显著提升

### 功能完善
- ✅ 实时监控能力
- ✅ 数据质量保障
- ✅ 自助分析能力
- ✅ 完整的数据中台

### 技术提升
- ✅ 大数据技术栈
- ✅ 缓存架构
- ✅ OLAP引擎
- ✅ 实时计算

---

**制定人**: Claude Sonnet 4.5
**审核人**: 待定
**实施时间**: 2026-02-26 开始

🚀 **让我们一起打造业界领先的数据中台！** 🚀
