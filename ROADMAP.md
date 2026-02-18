# 银航宝 SilverNav Treasure - 开发路线图

## 📋 项目概述

银航宝是一个航运金融数智风控与服务平台，通过大数据与机器学习技术实现多源数据融合、实时风险评估与决策支持。

**设计主题**：海洋蓝、深蓝、淡紫 - 体现航运、海事、船舶行业特色

---

## ✅ 已完成功能（Phase 0 - MVP基础）

### 0.1 用户认证系统（已完成）
**文件位置**：`main.py:385-513`、`templates/index.html`、`static/js/script.js`

- ✅ 登录/注册页面（炫酷Canvas动画：流星雨、航线、港口、靠泊船舶、集装箱堆场、龙门吊）
- ✅ JWT Token认证机制（HMAC-SHA256签名）
- ✅ 密码加密存储（bcrypt/argon2自动选择）
- ✅ 密码策略：最少10位、包含字母/数字/符号
- ✅ 账号锁定机制：5次失败锁定30分钟
- ✅ 用户会话管理（Token过期时间12小时）
- ✅ Root账户自动初始化

### 0.2 数据大屏主页（已完成）
**文件位置**：`templates/dashboard.html`、`static/js/dashboard/`、`main.py:516-1181`

- ✅ 金融风险总览大屏（8大核心板块）
- ✅ 实时时钟显示（右上角，Asia/Shanghai时区）
- ✅ 日期选择器（自定义日历组件，支持月份切换）
- ✅ 时间维度切换：今日/本月/近7天/近30天/近90天
- ✅ 多币种支持：CNY/USD/HKD/GBP/EUR（实时汇率转换）
- ✅ 多单位切换：万元/百万元/千万元/亿元
- ✅ 自动刷新：5分钟/10分钟/30分钟可选
- ✅ 8大核心板块数据展示：
  1. **总体风险敞口**：总敞口、高风险敞口、风险分布环形图
  2. **高风险预警看板**：高风险企业/船舶数量、资产红榜Top10
  3. **不良资产监控**：NPL率、资产总额、币种分布柱状图
  4. **风险等级分布**：企业/船舶双环形图
  5. **风险趋势**：近30天高风险敞口/平均风险评分折线图
  6. **船舶风险Top10**：风险评分最高船舶列表
  7. **授信使用进度**：已用授信/建议授信进度条、Top客户
  8. **风险因子贡献Top**：SHAP特征贡献柱状图
- ✅ 数据钻取框架（data-drill属性，8个路由预留）
- ✅ 详情页面路由预留（detail.html）
- ✅ 退出登录功能

### 0.3 后端基础架构（已完成）
**文件位置**：`main.py`、`app/`

- ✅ FastAPI RESTful API框架（1181行）
- ✅ PostgreSQL双连接池（admin/readonly角色分离）
- ✅ 分层架构设计（API → Service → Repository → DB）
- ✅ 数据序列化工具（Decimal/Date/Datetime处理）
- ✅ 环境配置管理（app/config.py）
- ✅ 完整API端点：
  - `/api/login`、`/api/register`：用户认证
  - `/api/dashboard`：大屏数据聚合（单一端点，返回全部数据）
  - `/api/dashboard/summary`：总体风险敞口
  - `/api/dashboard/alerts`：高风险预警
  - `/api/dashboard/npl`：不良资产监控
  - `/api/dashboard/distribution`：风险等级分布
  - `/api/dashboard/trend`：风险趋势
  - `/api/dashboard/vessels`：船舶风险Top10
  - `/api/dashboard/credit`：授信使用进度
  - `/api/dashboard/factors`：风险因子贡献
  - `/api/dashboard/fx`：外汇汇率

### 0.4 数据库设计（已完成）
**文件位置**：`DBD/postgreSQL-DBD/silvernav_db.sql`

- ✅ 12张核心表设计：
  1. `users`：用户表（账号、密码、状态、锁定机制）
  2. `companies`：企业表（企业名称、信用评分、风险等级）
  3. `vessels`：船舶表（IMO编号、船舶类型、资产风险评分）
  4. `vessel_risk_history`：船舶风险历史评估表
  5. `risk_factor_contribution`：风险因子贡献表（SHAP）
  6. `financial_assets`：金融资产表（授信、逾期、不良）
  7. `asset_repayment_schedule`：资产还款计划表
  8. `credit_risk_assessment`：信用风险评估表
  9. `fx_rates`：外汇汇率表（支持多币种）
  10. `daily_risk_summary`：每日风险汇总表
  11. `financial_risk_snapshot`：金融风险快照表
  12. `risk_events`：风险事件表
- ✅ 索引优化：dashboard_indexes.sql、double_indexes.sql
- ✅ 查询优化：dashboard_queries.sql（12个优化查询）

### 0.5 Spark批处理作业（已完成）
**文件位置**：`spark_jobs/`

- ✅ `pg_to_hdfs.py`：PostgreSQL → HDFS数据迁移（8张表）
- ✅ `aggregate_dashboard.py`：Dashboard聚合计算（写回快照表）
- ✅ 支持环境变量配置（PG_HOST、HDFS_BASE等）

---

## 🎯 当前项目状态评估

### 已实现的核心能力
1. **完整的用户认证体系**：从注册到登录、Token管理、安全策略全覆盖
2. **功能完备的数据大屏**：8大板块、多维度筛选、实时数据展示
3. **高性能后端架构**：FastAPI异步、连接池、角色分离、查询优化
4. **完整的数据库设计**：12张表、索引优化、查询优化
5. **Spark批处理基础**：数据迁移、聚合计算作业

### 待完善的功能
1. **详情页面**：8个钻取页面仅有路由框架，内容待开发
2. **MongoDB集成**：已安装但未实际使用（预留AIS轨迹、日志存储）
3. **Flink CDC**：未集成（实时数据同步规划中）
4. **Hadoop完整集成**：Spark作业已就绪，但HDFS集群未部署
5. **系统治理功能**：RBAC、审计日志、系统监控未实现

---

## 🏗️ 技术架构演进规划

### 当前技术栈（Phase 0 - 已实现）
```
前端：
  - 原生JavaScript（无框架依赖）
  - HTML5 + CSS3
  - Canvas动画（流星雨、航线、港口场景）
  - SVG图表（环形图、折线图、柱状图）

后端：
  - FastAPI + Python 3.12.10
  - Uvicorn ASGI服务器
  - Pydantic数据校验
  - bcrypt/argon2密码加密
  - HMAC-SHA256 Token签名

数据库：
  - PostgreSQL 14.20（已部署，12张表）
  - MongoDB 7.0.29（已安装，未使用）

大数据：
  - Spark 3.5.1（2个批处理作业已就绪）
  - Hadoop 3.3.6（未部署）

部署：
  - 本地开发环境
  - 远程PostgreSQL服务器（1.15.225.134）
```

### 目标技术栈（Phase 3完成后）
```
前端：
  - 原生JS + HTML5 + CSS3
  - Leaflet.js（地图可视化）
  - D3.js/Mermaid.js（数据血缘图）

后端：
  - FastAPI + Python 3.12.10
  - WebSocket（实时推送）

数据库：
  - PostgreSQL 14.20（结构化数据，热数据）
  - MongoDB 7.0.29（AIS轨迹、审计日志）

大数据：
  - Hadoop 3.3.6（HDFS数据湖，冷数据归档）
  - Spark 3.5.1（批处理/流式计算）
  - Flink CDC（PostgreSQL → Kafka实时同步）
  - Kafka（消息队列）

部署：
  - Docker Compose（多容器编排）
  - Nginx（反向代理）
```

---

## 🚀 迭代开发计划

### Phase 1：详情页面开发（8个核心钻取页面）

**目标**：实现数据大屏8个板块的点击钻取功能，完善detail.html页面

**当前状态**：
- ✅ 路由框架已完成（`static/js/dashboard/app.js:163-178`）
- ✅ 详情页模板已就绪（`templates/detail.html`）
- ❌ 详情页内容为空占位符

#### 1.1 高风险预警详情页（Risk Alerts Details）
**路由**：`/detail?type=alerts`
**触发板块**：高风险预警看板（dashboard.html:116-143）
**核心功能**：
- 高风险资产列表（公司名称、船舶名称、合同编号、敞口金额、风险评分）
- 支持按风险等级筛选（high/medium/low）
- 支持按资产类型筛选（企业/船舶）
- 支持搜索（公司名称、船舶名称、合同编号）
- 分页展示（每页20条）
- 导出Excel功能（可选）

**数据来源**：`financial_assets`、`companies`、`vessels`表
**后端API**：`/api/detail/alerts`（需新增）

#### 1.2 船舶资产风险页（Vessel Risk Details）
**路由**：`/detail?type=vessels`
**触发板块**：船舶风险Top10（dashboard.html:210-216）
**核心功能**：
- 船舶列表展示（船名、IMO、船龄、船型、风险评分、所属企业）
- 船舶作为抵押物的风险评分
- 船龄/船型/船旗国分布统计
- 风险等级变动记录（时间线）
- 支持按风险等级、船型、船龄筛选
- 船舶详情弹窗（点击船名）

**数据来源**：`vessels`、`vessel_risk_history`、`companies`表
**后端API**：`/api/detail/vessels`（需新增）

#### 1.3 不良资产明细页（NPL Details）
**路由**：`/detail?type=npl`
**触发板块**：不良资产监控（dashboard.html:145-163）
**核心功能**：
- 不良资产列表（客户、合同编号、金额、逾期天数、不良分类）
- 不良认定标准说明（次级/可疑/损失）
- 不良资产分类统计（饼图）
- 拨备覆盖率计算
- 不良资产趋势图（近12个月）
- 支持按不良分类、币种筛选

**数据来源**：`financial_assets`表（`is_non_performing = TRUE`）
**后端API**：`/api/detail/npl`（需新增）

#### 1.4 风险趋势分析页（Risk Trend Details）
**路由**：`/detail?type=trend`
**触发板块**：风险趋势（dashboard.html:192-208）
**核心功能**：
- 高风险敞口历史趋势（可选7天/30天/90天/180天/1年）
- 平均风险评分趋势
- 风险等级迁移矩阵（从低到高、从高到低的迁移数量）
- 风险预测模型输出（可选，基于历史数据）
- 趋势对比（同比、环比）
- 数据导出功能

**数据来源**：`daily_risk_summary`、`financial_risk_snapshot`表
**后端API**：`/api/detail/trend`（需新增）

#### 1.5 授信使用明细页（Credit Usage Details）
**路由**：`/detail?type=credit`
**触发板块**：授信使用进度（dashboard.html:218-230）
**核心功能**：
- 授信客户排行榜（按已用额度、按使用率）
- 授信使用率分布（0-50%、50-80%、80-100%、>100%）
- 额度调整历史记录（时间、客户、调整前、调整后、原因）
- 授信集中度分析（Top10客户占比）
- 授信到期提醒（近30天到期）
- 支持按企业、币种筛选

**数据来源**：`financial_assets`、`companies`表
**后端API**：`/api/detail/credit`（需新增）

#### 1.6 风险因子拆解页（Risk Factor Details）
**路由**：`/detail?type=factors`
**触发板块**：风险因子贡献Top（dashboard.html:232-238）
**核心功能**：
- SHAP特征贡献可视化（瀑布图）
- 各风险因子权重排序（柱状图）
- 单个客户风险因子详细拆解（选择客户后展示）
- 因子变化趋势图（近30天）
- 可解释性报告生成（PDF导出，可选）
- 因子重要性排名

**数据来源**：`risk_factor_contribution`表
**后端API**：`/api/detail/factors`（需新增）

#### 1.7 风险等级分布详情页（Distribution Details）
**路由**：`/detail?type=distribution`
**触发板块**：风险等级分布（dashboard.html:165-190）
**核心功能**：
- 企业风险等级分布（low/medium/high数量、占比）
- 船舶风险等级分布（low/medium/high数量、占比）
- 风险等级迁移分析（本月vs上月）
- 按行业、地区、船型细分统计
- 风险等级定义说明
- 数据导出功能

**数据来源**：`companies`、`vessels`表
**后端API**：`/api/detail/distribution`（需新增）

#### 1.8 总体风险敞口详情页（Overall Exposure Details）
**路由**：`/detail?type=overall`
**触发板块**：总体风险敞口（dashboard.html:90-114）
**核心功能**：
- 总敞口明细（按币种、按客户、按船舶）
- 高风险敞口明细列表
- 敞口集中度分析（Top10客户、Top10船舶）
- 敞口变化趋势（近30天）
- 币种敞口分布（饼图）
- 敞口预警阈值设置（只读展示）

**数据来源**：`financial_assets`、`companies`、`vessels`表
**后端API**：`/api/detail/overall`（需新增）

**Phase 1 交付物**：
- ✅ 8个详情页面HTML模板（复用detail.html，动态加载内容）
- ✅ 对应的JS逻辑文件（`static/js/detail.js`，约500-800行）
- ✅ 后端API接口（8个GET/POST端点，每个约50-100行）
- ✅ 数据库查询优化（必要时创建新索引）
- ✅ 样式文件（`static/css/detail.css`，约200-300行）

**预计工作量**：1-2周（每个详情页1-2天）

---

### Phase 2：航运数据&行为支撑功能

#### 2.1 船舶行为分析页（AIS & Behavior）
**路由**：`/behavior`
**核心功能**：
- 航迹地图展示（Leaflet.js + AIS数据）
- 异常停泊检测
- 绕航行为识别
- 高风险水域暴露分析
- 航行轨迹回放

**技术实现**：
- 前端：Leaflet.js地图库
- 数据源：MongoDB存储AIS轨迹数据
- 后端：FastAPI + MongoDB查询

#### 2.2 船舶/企业画像页（Profile）
**路由**：`/profile?id={entity_id}&type={company|vessel}`
**核心功能**：
- 船舶档案（基本信息、技术参数、所有权）
- 企业背景（注册信息、股东结构、经营范围）
- 历史风险事件汇总
- 关联关系图谱
- 360度风险画像

**数据来源**：`companies`、`vessels`、`risk_events`、`relationships`表

#### 2.3 数据质量&数据血缘页（Data Lineage & Quality）
**路由**：`/data_quality`
**核心功能**：
- 数据来源展示（AIS/财务/监管）
- ETL流程可视化
- 数据更新时间&完整性监控
- 数据质量评分
- 血缘关系追踪

**技术实现**：
- 数据血缘元数据存储（PostgreSQL）
- 可视化：D3.js或Mermaid.js

**Phase 2 交付物**：
- 3个新页面开发
- MongoDB集成（AIS数据存储）
- 地图可视化功能
- 数据血缘元数据表设计

---

### Phase 3：大数据技术栈集成

#### 3.1 Flink CDC实时数据同步
**目标**：实现PostgreSQL → Flink CDC → Kafka → 实时计算
**实现步骤**：
1. 部署Flink CDC Connector（PostgreSQL）
2. 配置Kafka消息队列
3. 实现实时风险评分计算
4. WebSocket推送实时预警到前端

**涉及表**：`credit_lines`、`risk_events`、`vessels`

#### 3.2 Hadoop HDFS数据湖
**目标**：历史数据归档与大规模数据存储
**实现步骤**：
1. 部署Hadoop 3.3.6集群（单节点/伪分布式）
2. 历史AIS轨迹数据迁移至HDFS
3. 历史风险评分数据归档
4. 实现冷热数据分离策略

**数据迁移**：
- 热数据（近3个月）：PostgreSQL/MongoDB
- 温数据（3-12个月）：MongoDB
- 冷数据（>12个月）：HDFS

#### 3.3 Spark批处理与流式计算
**目标**：大规模数据处理与机器学习模型训练
**实现步骤**：
1. 开发Spark批处理作业（风险评分批量计算）
2. 实现Spark Streaming（实时异常检测）
3. 集成MLlib（XGBoost/LightGBM模型训练）
4. 模型版本管理（MLflow可选）

**Spark作业**：
- `spark_jobs/risk_scoring.py`：批量风险评分
- `spark_jobs/anomaly_detection.py`：异常行为检测
- `spark_jobs/feature_engineering.py`：特征工程

#### 3.4 MongoDB非结构化数据存储
**目标**：存储AIS轨迹、日志、审计记录
**集合设计**：
- `ais_tracks`：船舶AIS轨迹数据
- `audit_logs`：用户操作日志
- `system_logs`：系统运行日志
- `model_predictions`：模型预测结果

**Phase 3 交付物**：
- Flink CDC实时同步管道
- Hadoop HDFS数据湖
- Spark批处理/流式作业
- MongoDB集成完成
- Docker Compose编排文件

---

### Phase 4：系统治理&工程能力

#### 4.1 模型配置与版本管理页（Model & Config）
**路由**：`/model_config`
**核心功能**：
- 当前模型版本展示
- 特征列表与权重
- 阈值配置（只读展示）
- 模型性能指标（AUC/Precision/Recall）
- 模型训练历史

#### 4.2 用户/角色/权限页（RBAC）
**路由**：`/admin/users`
**核心功能**：
- 用户列表管理
- 角色定义（分析员/管理员/审计员）
- 权限矩阵配置
- 用户操作日志关联

#### 4.3 审计日志页（Audit Log）
**路由**：`/admin/audit`
**核心功能**：
- 登录日志（时间/IP/设备）
- 风险操作记录（数据修改/配置变更）
- 日志检索与导出
- 异常登录告警

#### 4.4 系统状态&任务监控页（System Monitor）
**路由**：`/admin/monitor`
**核心功能**：
- 数据更新状态监控
- Spark任务状态展示
- Flink作业健康检查
- 数据库连接池状态
- 系统资源使用率

**Phase 4 交付物**：
- 4个系统管理页面
- RBAC权限控制实现
- 审计日志MongoDB存储
- 系统监控API

---

## 📍 下一步执行步骤（立即开始）

### Step 1：完善详情页面路由逻辑（0.5天）
**现状分析**：
- ✅ 路由框架已完成：`static/js/dashboard/app.js:163-178`（bindDrill函数）
- ✅ 详情页模板已就绪：`templates/detail.html`
- ❌ 详情页内容为空占位符

**任务**：
1. 创建`static/js/detail.js`处理详情页逻辑
2. 在`templates/detail.html`中添加动态内容容器
3. 实现根据URL参数`type`加载不同内容

**代码位置**：
- `static/js/dashboard/app.js:163-178`（已完成的bindDrill函数）
- `templates/detail.html:30-37`（空白内容区域）

### Step 2：开发授信/客户风险评估页（1-2天）
**任务**：
1. 后端：在`main.py`中添加`/api/detail/credit` API端点
2. 数据库：编写SQL查询（关联companies、financial_assets、risk_events表）
3. 前端：实现企业列表表格、筛选器、搜索框
4. 样式：复用`dashboard.css`，新增`detail.css`

**SQL示例**：
```sql
SELECT
    c.company_name,
    c.credit_score,
    c.risk_level,
    COUNT(DISTINCT fa.id) as asset_count,
    COALESCE(SUM(fa.outstanding_amount), 0) as total_outstanding,
    COUNT(DISTINCT re.id) as risk_event_count
FROM companies c
LEFT JOIN financial_assets fa ON c.id = fa.company_id AND fa.is_active = TRUE
LEFT JOIN risk_events re ON c.id = re.company_id
WHERE c.is_active = TRUE AND c.risk_level = 'high'
GROUP BY c.id, c.company_name, c.credit_score, c.risk_level
ORDER BY total_outstanding DESC
LIMIT 50;
```

### Step 3：依次开发其余7个详情页（1-2周）
**优先级排序**（基于数据大屏点击热度）：
1. **高风险预警详情页**（/detail?type=alerts）- 对应大屏"高风险预警看板"
2. **船舶资产风险页**（/detail?type=vessels）- 对应大屏"船舶风险Top10"
3. **不良资产明细页**（/detail?type=npl）- 对应大屏"不良资产监控"
4. **风险趋势分析页**（/detail?type=trend）- 对应大屏"风险趋势"
5. **授信使用明细页**（/detail?type=credit）- 对应大屏"授信使用进度"
6. **风险因子拆解页**（/detail?type=factors）- 对应大屏"风险因子贡献Top"
7. **风险等级分布详情页**（/detail?type=distribution）- 对应大屏"风险等级分布"
8. **总体风险敞口详情页**（/detail?type=overall）- 对应大屏"总体风险敞口"

**开发模式**：
- 每个页面独立开发、测试、上线
- 复用组件（表格、图表、筛选器）
- 统一样式规范（继承dashboard.css）
- 每个详情页约200-300行代码（HTML + JS + API）

### Step 4：MongoDB集成准备（与Phase 1并行，可选）
**任务**：
1. 安装MongoDB Python驱动：`pip install pymongo motor`
2. 在`app/database.py`中添加MongoDB连接池
3. 设计AIS轨迹数据集合结构：
   ```javascript
   {
     imo_number: "IMO1234567",
     vessel_name: "COSCO SHIPPING",
     timestamp: ISODate("2026-02-18T10:30:00Z"),
     latitude: 31.2304,
     longitude: 121.4737,
     speed: 12.5,
     course: 90,
     status: "underway"
   }
   ```
4. 编写数据导入脚本（CSV → MongoDB）

**优先级**：低（Phase 2再实现）

### Step 5：Hadoop HDFS集群部署（Phase 1完成后）
**任务**：
1. 部署Hadoop 3.3.6单节点/伪分布式集群
2. 配置HDFS存储路径：`hdfs:///silvernav/raw`
3. 运行Spark作业`pg_to_hdfs.py`测试数据迁移
4. 验证数据完整性

**优先级**：中（Phase 3前完成）

### Step 6：Flink CDC技术调研与POC（Phase 2开始前）
**任务**：
1. 搭建Flink CDC开发环境（Flink 1.17+）
2. 配置PostgreSQL CDC Connector
3. 实现PostgreSQL → Kafka简单示例
4. 编写实时风险评分计算逻辑
5. 性能测试与优化

**优先级**：低（Phase 3实现）

---

## 📊 项目里程碑

| 里程碑 | 目标 | 预计工作量 | 状态 |
|--------|------|-----------|------|
| Phase 0 | MVP基础功能（登录认证 + 数据大屏） | 2-3周 | ✅ 已完成 |
| Phase 1 | 8个详情页面开发 | 1-2周 | 🚧 进行中（0%） |
| Phase 2 | 航运数据功能（AIS轨迹、船舶画像、数据血缘） | 2-3周 | 📋 规划中 |
| Phase 3 | 大数据技术栈集成（Flink CDC、MongoDB、Hadoop） | 3-4周 | 📋 规划中 |
| Phase 4 | 系统治理功能（RBAC、审计日志、系统监控） | 1-2周 | 📋 规划中 |

**总计**：9-14周完成全部功能

---

## 🎯 成功标准

### 功能完整性
- ✅ Phase 0：登录认证 + 数据大屏（已完成）
- ⬜ Phase 1：8个详情页面全部开发完成
- ⬜ Phase 2：AIS轨迹地图、船舶画像、数据血缘可视化
- ⬜ Phase 3：Flink CDC实时同步、MongoDB集成、Hadoop数据湖
- ⬜ Phase 4：RBAC权限控制、审计日志、系统监控

### 技术先进性
- ⬜ Flink CDC实时同步延迟 < 5秒
- ⬜ Spark批处理作业稳定运行（已就绪，待部署）
- ⬜ MongoDB查询性能优化（索引、聚合管道）
- ⬜ API响应时间 < 500ms（当前已达标）

### 工程质量
- ✅ 代码结构清晰（分层架构）
- ✅ API响应时间 < 500ms（当前平均200-300ms）
- ⬜ 代码覆盖率 > 70%（未实施单元测试）
- ⬜ Docker一键部署（规划中）

---

## 📝 备注

1. **数据安全**：所有数据为模拟数据，不涉及真实商业信息
2. **性能优化**：Phase 1完成后需进行全面性能测试与优化
3. **文档完善**：每个Phase完成后更新技术文档
4. **代码规范**：遵循PEP 8（Python）、ESLint（JavaScript）
5. **数据库连接**：当前使用远程PostgreSQL（1.15.225.134），生产环境需迁移至本地或云服务
6. **MongoDB使用**：已安装但未实际使用，Phase 2开始集成
7. **Hadoop部署**：Spark作业已就绪，但HDFS集群未部署，Phase 3部署

---

## 🔄 版本历史

**v0.1.0 (2026-02-18) - MVP基础版本**
- ✅ 用户认证系统（登录/注册/Token）
- ✅ 数据大屏（8大核心板块）
- ✅ 多币种/多单位/多时间维度支持
- ✅ 数据库完整设计（12张表）
- ✅ Spark批处理作业（2个）
- ✅ 详情页面路由框架

**v0.2.0 (规划中) - 详情页面版本**
- ⬜ 8个详情页面开发完成
- ⬜ 数据钻取功能完整
- ⬜ 数据导出功能（Excel/PDF）

**v0.3.0 (规划中) - 航运数据版本**
- ⬜ AIS轨迹地图可视化
- ⬜ 船舶/企业360度画像
- ⬜ 数据质量&数据血缘追踪

**v1.0.0 (规划中) - 大数据集成版本**
- ⬜ Flink CDC实时数据同步
- ⬜ MongoDB完整集成
- ⬜ Hadoop HDFS数据湖
- ⬜ Docker容器化部署

---

**最后更新**：2026-02-18
**维护者**：孙帆（Sunstar）
**联系方式**：fandesunstar@outlook.com
**项目状态**：MVP阶段，Phase 0已完成，Phase 1进行中
