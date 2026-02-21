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

## 🎯 当前项目状态评估（2025-02-20更新）

### 已实现的核心能力
1. **完整的用户认证体系**：从注册到登录、Token管理、安全策略全覆盖 ✅
2. **功能完备的数据大屏**：8大板块、多维度筛选、实时数据展示 ✅
3. **高性能后端架构**：FastAPI异步、连接池、角色分离、查询优化 ✅
4. **完整的数据库设计**：12张表、索引优化、查询优化 ✅
5. **Spark批处理基础**：数据迁移、聚合计算作业 ✅
6. **8个详情页面全部完成**：数据钻取、图表展示、表格渲染、多维度筛选 ✅

### 待完善的功能
1. **MongoDB集成**：已安装但未实际使用（预留AIS轨迹、日志存储）
2. **Flink CDC**：未集成（实时数据同步规划中）
3. **Hadoop完整集成**：Spark作业已就绪，但HDFS集群未部署
4. **系统治理功能**：RBAC、审计日志、系统监控未实现
5. **航运数据功能**：AIS轨迹地图、船舶画像、数据血缘未实现

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

### Phase 1：详情页面开发（8个核心钻取页面）✅ 已完成

**目标**：实现数据大屏8个板块的点击钻取功能，完善detail.html页面

**当前状态**：
- ✅ 路由框架已完成（`static/js/dashboard/app.js:163-178`）
- ✅ 详情页模板已就绪（`templates/detail.html`）
- ✅ 详情页内容全部完成（`static/js/detail.js`，1090行）
- ✅ 后端API全部完成（8个详情页端点）
- ✅ 样式文件完成（`static/css/detail.css`）

#### 已完成的详情页面（100%）

| 序号 | 详情页名称 | 类型 | API端点 | 状态 | 完成日期 |
|------|-----------|------|---------|------|---------|
| 1 | 授信详情页 | credit | /api/detail/credit | ✅ 100% | 2025-02 |
| 2 | 高风险预警详情页 | alerts | /api/detail/alerts | ✅ 100% | 2025-02 |
| 3 | 船舶资产风险页 | vessels | /api/detail/vessels | ✅ 100% | 2025-02 |
| 4 | 不良资产明细页 | npl | /api/detail/npl | ✅ 100% | 2025-02 |
| 5 | 风险趋势分析页 | trend | /api/detail/trend | ✅ 100% | 2025-02 |
| 6 | 风险因子拆解页 | factors | /api/detail/factors | ✅ 100% | 2025-02 |
| 7 | 风险等级分布详情页 | distribution | /api/detail/distribution | ✅ 100% | 2025-02 |
| 8 | 总体风险敞口详情页 | overall | /api/detail/overall | ✅ 100% | 2025-02 |

#### 1.1 高风险预警详情页（Risk Alerts Details）✅
**路由**：`/detail?type=alerts`
**触发板块**：高风险预警看板（dashboard.html:116-143）
**核心功能**：
- ✅ 高风险资产列表（公司名称、船舶名称、合同编号、敞口金额、风险评分）
- ✅ 统计卡片（高风险资产数、高风险敞口）
- ✅ 风险等级统计图（high/medium/low）
- ✅ 资产类型分布图（5种类型）
- ✅ 高风险资产列表（Top 50）

**数据来源**：`financial_assets`、`companies`、`vessels`表
**后端API**：`/api/detail/alerts`（已完成）

#### 1.2 船舶资产风险页（Vessel Risk Details）✅
**路由**：`/detail?type=vessels`
**触发板块**：船舶风险Top10（dashboard.html:210-216）
**核心功能**：
- ✅ 统计卡片（总船舶数、高风险船舶、平均船龄、平均风险评分）
- ✅ 船龄分布图（5个年龄段）
- ✅ 船型分布图（Top 10）
- ✅ 船舶风险排行榜（Top 20）

**数据来源**：`vessels`、`vessel_risk_history`、`companies`表
**后端API**：`/api/detail/vessels`（已完成）

#### 1.3 不良资产明细页（NPL Details）✅
**路由**：`/detail?type=npl`
**触发板块**：不良资产监控（dashboard.html:145-163）
**核心功能**：
- ✅ 统计卡片（不良资产数量、金额、不良率、拨备覆盖率）
- ✅ 不良资产分类图（次级、可疑、损失、关注）
- ✅ 不良资产趋势图（近12个月）
- ✅ 不良资产明细表

**数据来源**：`financial_assets`表（`is_non_performing = TRUE`）
**后端API**：`/api/detail/npl`（已完成）

#### 1.4 风险趋势分析页（Risk Trend Details）✅
**路由**：`/detail?type=trend`
**触发板块**：风险趋势（dashboard.html:192-208）
**核心功能**：
- ✅ 高风险敞口历史趋势（可选7天/30天/90天/180天/1年）
- ✅ 平均风险评分趋势
- ✅ 风险等级迁移矩阵（从低到高、从高到低的迁移数量）
- ✅ 趋势对比（同比、环比）
- ✅ 时间范围筛选器（7d/30d/90d/180d/1y）

**数据来源**：`daily_risk_summary`、`financial_risk_snapshot`表
**后端API**：`/api/detail/trend`（已完成）

#### 1.5 授信使用明细页（Credit Usage Details）✅
**路由**：`/detail?type=credit`
**触发板块**：授信使用进度（dashboard.html:218-230）
**核心功能**：
- ✅ 统计卡片（授信客户数、总授信额度、已用额度、平均使用率）
- ✅ 授信使用率分布图（0-50%、50-80%、80-100%、>100%）
- ✅ 授信集中度分析（Top10客户占比）
- ✅ 授信客户排行榜（Top 20）
- ✅ 授信到期提醒（近30天）

**数据来源**：`financial_assets`、`companies`表
**后端API**：`/api/detail/credit`（已完成）

#### 1.6 风险因子拆解页（Risk Factor Details）✅
**路由**：`/detail?type=factors`
**触发板块**：风险因子贡献Top（dashboard.html:232-238）
**核心功能**：
- ✅ SHAP特征贡献可视化（瀑布图）
- ✅ 各风险因子权重排序（柱状图）
- ✅ 风险因子贡献度排名（全部客户聚合）
- ✅ 因子重要性排名

**数据来源**：`risk_factor_contribution`表
**后端API**：`/api/detail/factors`（已完成）

#### 1.7 风险等级分布详情页（Distribution Details）✅
**路由**：`/detail?type=distribution`
**触发板块**：风险等级分布（dashboard.html:165-190）
**核心功能**：
- ✅ 企业风险等级分布（low/medium/high数量、占比）
- ✅ 船舶风险等级分布（low/medium/high数量、占比）
- ✅ 风险等级迁移分析（本月vs上月）
- ✅ 风险等级定义说明

**数据来源**：`companies`、`vessels`表
**后端API**：`/api/detail/distribution`（已完成）

#### 1.8 总体风险敞口详情页（Overall Exposure Details）✅
**路由**：`/detail?type=overall`
**触发板块**：总体风险敞口（dashboard.html:90-114）
**核心功能**：
- ✅ 统计卡片（总敞口、高风险敞口、敞口集中度、敞口变化）
- ✅ 币种敞口分布图
- ✅ 敞口集中度分析（Top10）
- ✅ 高风险敞口明细表（Top 20）
- ✅ 敞口变化趋势图（近30天）

**数据来源**：`financial_assets`、`companies`、`vessels`表
**后端API**：`/api/detail/overall`（已完成）

**Phase 1 交付物**：
- ✅ 8个详情页面HTML模板（复用detail.html，动态加载内容）
- ✅ 对应的JS逻辑文件（`static/js/detail.js`，1090行）
- ✅ 后端API接口（8个GET端点，main.py中约895行）
- ✅ 数据库查询优化（必要时创建新索引）
- ✅ 样式文件（`static/css/detail.css`）

**实际工作量**：约1-2周（2025-02完成）
**完成日期**：2025-02-20

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

## 📍 下一步执行步骤（Phase 2 开始）

### 当前项目状态总结（2025-02-20）
- ✅ **Phase 0 完成**：用户认证、数据大屏、后端架构、数据库设计、Spark作业
- ✅ **Phase 1 完成**：8个详情页面全部开发完成，数据钻取功能完整
- 📋 **Phase 2 规划中**：航运数据功能（AIS轨迹、船舶画像、数据血缘）
- 📋 **Phase 3 规划中**：大数据技术栈集成（Flink CDC、MongoDB、Hadoop）
- 📋 **Phase 4 规划中**：系统治理功能（RBAC、审计日志、系统监控）

### Phase 2 优先级任务规划

#### 任务1：MongoDB集成与AIS数据存储（优先级：高）
**目标**：完成MongoDB集成，为AIS轨迹数据存储做准备

**实施步骤**：
1. 安装MongoDB Python驱动：`pip install pymongo motor`
2. 在`app/database.py`中添加MongoDB连接池
3. 设计AIS轨迹数据集合结构：
   ```javascript
   // ais_tracks 集合
   {
     imo_number: "IMO1234567",
     vessel_name: "COSCO SHIPPING",
     timestamp: ISODate("2025-02-20T10:30:00Z"),
     latitude: 31.2304,
     longitude: 121.4737,
     speed: 12.5,
     course: 90,
     status: "underway",
     destination: "SHANGHAI",
     eta: ISODate("2025-02-21T08:00:00Z")
   }
   ```
4. 编写数据导入脚本（CSV → MongoDB）
5. 创建MongoDB索引（imo_number, timestamp）

**预计工作量**：2-3天

#### 任务2：船舶行为分析页面开发（优先级：高）
**路由**：`/behavior`
**核心功能**：
- 航迹地图展示（Leaflet.js + AIS数据）
- 船舶实时位置标注
- 历史轨迹回放（时间轴控制）
- 异常停泊检测（停泊时间>24小时）
- 绕航行为识别（偏离正常航线）
- 高风险水域暴露分析（进入制裁区域、海盗高发区）

**技术实现**：
- 前端：Leaflet.js地图库（轻量级，无需API Key）
- 数据源：MongoDB存储AIS轨迹数据
- 后端：FastAPI + MongoDB查询
- 地图底图：OpenStreetMap（免费）

**数据来源**：MongoDB `ais_tracks`集合
**后端API**：`/api/behavior/tracks`、`/api/behavior/anomalies`

**预计工作量**：3-5天

#### 任务3：船舶/企业360度画像页面（优先级：中）
**路由**：`/profile?id={entity_id}&type={company|vessel}`
**核心功能**：
- **船舶档案**：
  - 基本信息（船名、IMO、船型、船龄、吨位、建造年份）
  - 技术参数（载重吨、总吨、净吨、主机功率）
  - 所有权信息（船东、光租人、期租人）
  - 船级社认证（CCS、DNV、ABS等）
  - 保险信息（船壳险、P&I险）
- **企业背景**：
  - 注册信息（企业名称、统一社会信用代码、注册地址）
  - 股东结构（股东名称、持股比例、实际控制人）
  - 经营范围（主营业务、行业分类）
  - 财务指标（资产总额、营收、利润、负债率）
- **历史风险事件汇总**：
  - 逾期记录（逾期时间、逾期金额、处理结果）
  - 违约事件（违约类型、违约金额、法律诉讼）
  - 船舶事故（碰撞、搁浅、火灾、沉没）
- **关联关系图谱**：
  - 企业-船舶关联（所有权、租赁关系）
  - 企业-企业关联（母子公司、关联交易）
  - 船舶-船舶关联（同一船东、同一船队）
- **360度风险画像**：
  - 信用评分趋势（近12个月）
  - 风险等级变化（历史迁移）
  - 风险因子雷达图（6-8个维度）
  - 行业对比分析（同行业平均水平）

**数据来源**：`companies`、`vessels`、`risk_events`、`financial_assets`表
**后端API**：`/api/profile/company/{id}`、`/api/profile/vessel/{id}`

**预计工作量**：4-6天

#### 任务4：数据质量&数据血缘页面（优先级：中）
**路由**：`/data_quality`
**核心功能**：
- **数据来源展示**：
  - AIS数据源（卫星AIS、岸基AIS）
  - 财务数据源（企业财报、银行授信）
  - 监管数据源（海事局、银保监会）
  - 第三方数据源（船级社、保险公司）
- **ETL流程可视化**：
  - 数据采集 → 数据清洗 → 数据转换 → 数据加载
  - 每个环节的处理逻辑说明
  - 数据流向图（Mermaid.js或D3.js）
- **数据更新时间&完整性监控**：
  - 各数据源最后更新时间
  - 数据完整性评分（缺失率、异常率）
  - 数据时效性监控（延迟时间）
- **数据质量评分**：
  - 准确性（Accuracy）：数据与真实值的一致性
  - 完整性（Completeness）：数据缺失率
  - 一致性（Consistency）：跨表数据一致性
  - 时效性（Timeliness）：数据更新频率
  - 唯一性（Uniqueness）：重复数据率
- **血缘关系追踪**：
  - 表级血缘（哪些表生成了哪些表）
  - 字段级血缘（字段来源追踪）
  - 可视化展示（节点-边图）

**技术实现**：
- 数据血缘元数据存储（PostgreSQL新增表`data_lineage`）
- 可视化：Mermaid.js（轻量级）或D3.js（复杂图）
- 数据质量规则引擎（Python脚本定期检查）

**数据来源**：新增`data_lineage`、`data_quality_metrics`表
**后端API**：`/api/data_quality/summary`、`/api/data_quality/lineage`

**预计工作量**：3-5天

### Phase 2 交付物总结
- ✅ MongoDB集成完成（连接池、数据导入）
- ✅ 船舶行为分析页面（AIS轨迹地图）
- ✅ 船舶/企业360度画像页面
- ✅ 数据质量&数据血缘页面
- ✅ 新增数据库表（data_lineage、data_quality_metrics）
- ✅ 新增MongoDB集合（ais_tracks、audit_logs）

**预计总工作量**：2-3周

---

### Phase 3 技术栈集成规划（Phase 2完成后）

#### 任务1：Hadoop HDFS数据湖部署
**目标**：部署Hadoop单节点/伪分布式集群，实现历史数据归档

**实施步骤**：
1. 安装Hadoop 3.3.6（单节点模式）
2. 配置HDFS存储路径：`hdfs:///silvernav/raw`
3. 运行Spark作业`pg_to_hdfs.py`测试数据迁移
4. 验证数据完整性
5. 实现冷热数据分离策略：
   - 热数据（近3个月）：PostgreSQL/MongoDB
   - 温数据（3-12个月）：MongoDB
   - 冷数据（>12个月）：HDFS

**预计工作量**：3-5天

#### 任务2：Flink CDC实时数据同步
**目标**：实现PostgreSQL → Flink CDC → Kafka → 实时计算

**实施步骤**：
1. 部署Flink CDC Connector（PostgreSQL）
2. 配置Kafka消息队列（单节点）
3. 实现实时风险评分计算（Flink作业）
4. WebSocket推送实时预警到前端
5. 性能测试与优化（目标延迟<5秒）

**涉及表**：`financial_assets`、`risk_events`、`vessels`

**预计工作量**：5-7天

#### 任务3：Spark批处理与流式计算增强
**目标**：大规模数据处理与机器学习模型训练

**实施步骤**：
1. 开发Spark批处理作业（风险评分批量计算）
2. 实现Spark Streaming（实时异常检测）
3. 集成MLlib（XGBoost/LightGBM模型训练）
4. 模型版本管理（MLflow可选）

**Spark作业**：
- `spark_jobs/risk_scoring.py`：批量风险评分
- `spark_jobs/anomaly_detection.py`：异常行为检测
- `spark_jobs/feature_engineering.py`：特征工程

**预计工作量**：5-7天

#### 任务4：Docker容器化部署
**目标**：实现一键部署，提升开发效率

**实施步骤**：
1. 编写Dockerfile（FastAPI应用）
2. 编写docker-compose.yml（多容器编排）
   - PostgreSQL容器
   - MongoDB容器
   - Kafka容器
   - Flink容器
   - FastAPI应用容器
   - Nginx反向代理容器
3. 配置环境变量管理（.env文件）
4. 测试一键启动/停止

**预计工作量**：2-3天

### Phase 3 交付物总结
- ✅ Hadoop HDFS数据湖部署
- ✅ Flink CDC实时同步管道
- ✅ Spark批处理/流式作业增强
- ✅ Docker Compose编排文件
- ✅ 一键部署脚本

**预计总工作量**：3-4周

---

### Phase 4 系统治理功能规划（Phase 3完成后）

#### 任务1：RBAC权限控制系统
**路由**：`/admin/users`、`/admin/roles`
**核心功能**：
- 用户列表管理（增删改查）
- 角色定义（分析员/管理员/审计员/只读用户）
- 权限矩阵配置（页面访问权限、API调用权限）
- 用户-角色绑定
- 权限继承机制

**数据库设计**：
- 新增表：`roles`、`permissions`、`user_roles`、`role_permissions`

**预计工作量**：3-4天

#### 任务2：审计日志系统
**路由**：`/admin/audit`
**核心功能**：
- 登录日志（时间/IP/设备/浏览器）
- 风险操作记录（数据修改/配置变更/权限变更）
- 日志检索与导出（按用户、按时间、按操作类型）
- 异常登录告警（异地登录、频繁失败）

**数据存储**：MongoDB `audit_logs`集合

**预计工作量**：2-3天

#### 任务3：模型配置与版本管理页面
**路由**：`/model_config`
**核心功能**：
- 当前模型版本展示
- 特征列表与权重
- 阈值配置（只读展示）
- 模型性能指标（AUC/Precision/Recall/F1）
- 模型训练历史（版本对比）

**数据库设计**：
- 新增表：`model_versions`、`model_features`、`model_metrics`

**预计工作量**：2-3天

#### 任务4：系统状态&任务监控页面
**路由**：`/admin/monitor`
**核心功能**：
- 数据更新状态监控（各表最后更新时间）
- Spark任务状态展示（运行中/成功/失败）
- Flink作业健康检查（延迟、吞吐量）
- 数据库连接池状态（活跃连接数、空闲连接数）
- 系统资源使用率（CPU、内存、磁盘）

**技术实现**：
- 后端：定期采集系统指标（psutil库）
- 前端：实时刷新（WebSocket或轮询）

**预计工作量**：3-4天

### Phase 4 交付物总结
- ✅ RBAC权限控制系统
- ✅ 审计日志系统
- ✅ 模型配置与版本管理页面
- ✅ 系统状态&任务监控页面
- ✅ 新增数据库表（roles、permissions、user_roles等）

**预计总工作量**：1-2周

---

### 立即开始的下一步行动（Phase 2 第一步）

#### 🎯 推荐优先任务：MongoDB集成与AIS数据存储

**为什么优先做这个**：
1. MongoDB已安装但未使用，需要激活
2. 为后续AIS轨迹地图功能打基础
3. 技术难度适中，可快速见效
4. 不依赖其他未完成功能

**具体执行步骤**：
1. **安装Python驱动**（5分钟）
   ```bash
   pip install pymongo motor
   ```

2. **配置MongoDB连接池**（30分钟）
   - 在`app/database.py`中添加MongoDB连接
   - 配置连接字符串（localhost:27017）
   - 实现异步连接池（motor库）

3. **设计AIS数据集合**（1小时）
   - 创建`ais_tracks`集合
   - 定义文档结构（imo_number, timestamp, lat, lon等）
   - 创建索引（imo_number, timestamp复合索引）

4. **编写数据导入脚本**（2-3小时）
   - 生成模拟AIS数据（100艘船舶，近30天轨迹）
   - CSV → MongoDB批量导入
   - 验证数据完整性

5. **测试MongoDB查询**（1小时）
   - 编写测试API：`/api/test/mongodb`
   - 查询单艘船舶轨迹
   - 查询指定时间范围内所有船舶位置

**预计完成时间**：1天

**完成后的下一步**：开发船舶行为分析页面（AIS轨迹地图）

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
