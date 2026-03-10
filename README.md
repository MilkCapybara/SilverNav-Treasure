**银航宝 — 航运金融数智风控与服务平台**

银航宝是一个完整的航运金融风控平台，面向航运企业、金融机构及供应链金融从业者，提供船舶信用、融资风险与运营异常的数智风控服务。通过大数据与机器学习技术，实现多源数据融合、实时风险评估与决策支持。

**已实现功能**
- ✅ 用户认证系统：登录/注册、JWT Token、密码策略、账号锁定机制
- ✅ 数据大屏：8大核心板块实时展示（总体风险敞口、高风险预警、不良资产监控、风险等级分布、风险趋势、船舶风险Top10、授信使用进度、风险因子贡献）
- ✅ 多币种支持：CNY/USD/HKD/GBP/EUR自由切换，实时汇率转换
- ✅ 多单位切换：万元/百万元/千万元/亿元
- ✅ 时间维度筛选：今日/本月/近7天/近30天/近90天
- ✅ 数据基准日持久化：用户选择的日期在页面切换后保持不变
- ✅ 详情页面：船舶行为分析、船舶画像、数据质量监控、数据血缘追踪（4个核心页面已完成）
- ✅ 数据血缘可视化：SVG动态图谱，支持流程视图/树形视图/网络视图三种展示模式
- ✅ 智能风险预测：集成XGBoost/LightGBM/RandomForest机器学习模型，实时预测船舶违约风险
- ✅ ClickHouse集成：OLAP数据库，查询性能提升25-60倍，核心数据已迁移（80,317,304条）
- ✅ Redis缓存：Dashboard缓存响应时间从2-3秒降至0.05秒，性能提升40-60倍
- ✅ Spark批处理作业：PostgreSQL → HDFS数据迁移、Dashboard聚合计算、AIS轨迹分析（MongoDB）
- ✅ 数据库完整设计：用户表、企业表、船舶表、金融资产表、风险评估表、汇率表等12张核心表
- ✅ 炫酷UI特效：航运金融科技风，登录页3D翻转、粒子爆发、扫描线、能量脉冲等多种动画效果
- ✅ HDFS分布式存储：20,000份船舶融资合同PDF文件已上传至HDFS（426.8 MB）
- ✅ 船舶合同风险分析：20,000份合同PDF分析、风险评分、关键词识别、可视化展示（最终功能模块）

**技术栈**
- 后端：FastAPI + Python 3.12.10（异步高性能API）
- 数据库：PostgreSQL 14.20（结构化数据）、ClickHouse 26.1.3.52（OLAP分析）、MongoDB 7.0.29（AIS轨迹分析、合同数据存储）
- 缓存：Redis 6.0.16（Dashboard缓存、会话管理）
- 大数据：Hadoop 3.3.6（HDFS存储）、Spark 3.5.1（PySpark批处理）
- 机器学习：XGBoost、LightGBM、RandomForest（风险预测模型）
- 文档处理：PyPDF2（PDF文本提取）、正则表达式（字段提取）
- 流处理：Kafka（预留实时流处理）
- 前端：原生JavaScript + HTML5 + CSS3（无框架依赖，轻量高效）
- 可视化：Canvas动画、SVG图表、环形图、趋势图、数据血缘图谱
- 部署：本地开发环境（Docker容器化规划中）
- 其他：Pydantic数据校验、bcrypt/argon2密码加密、HMAC Token签名

**项目结构**
```
SilverNav-Treasure/
├── app/                    # 应用核心模块
│   ├── config.py          # 配置管理
│   ├── database.py        # PostgreSQL连接池
│   ├── clickhouse_client.py  # ClickHouse客户端
│   ├── cache.py           # Redis缓存管理
│   ├── behavior_api.py    # 船舶行为分析API
│   ├── profile_api.py     # 船舶画像API
│   ├── quality_api.py     # 数据质量API
│   ├── kafka_config.py    # Kafka配置（预留）
│   └── utils.py           # 工具函数
├── DBD/                   # 数据库设计文档
│   └── postgreSQL-DBD/    # PostgreSQL建表脚本、索引、查询优化
├── scripts/               # 脚本工具集
│   ├── migration/         # 数据迁移脚本
│   │   ├── migrate_all_data.py  # 全量数据迁移
│   │   ├── migrate_large_tables.py  # 大表迁移
│   │   └── check_migration_progress.py  # 迁移进度检查
│   ├── ml/                # 机器学习训练脚本
│   │   ├── train_ml_models.py  # 模型训练
│   │   ├── train_ml_batch.py   # 批量训练
│   │   └── quickstart_ml.py    # 快速启动
│   ├── generate_contracts_batch.py  # 批量生成合同PDF（20,000份）
│   ├── upload_contracts_to_hdfs.py  # 上传合同PDF到HDFS
│   ├── analyze_contracts_from_hdfs.py  # 分析合同PDF并写入MongoDB
│   ├── test_contract_api.py    # 合同API测试脚本
│   ├── start_app.sh       # 应用启动脚本
│   ├── setup_redis_only.sh  # Redis环境配置
│   └── verify_real_data.py  # 数据验证工具
├── tests/                 # 测试文件
│   ├── test_credit_api.py  # 信用评估API测试
│   ├── test_ml_prediction.py  # ML预测测试
│   ├── test_redis_integration.py  # Redis集成测试
│   └── test_*.py          # 其他测试文件
├── docs/                  # 项目文档
│   ├── ROADMAP.md         # 项目路线图
│   ├── QUICK_START.md     # 快速启动指南
│   ├── ML_QUICKSTART.md   # ML模块快速启动
│   ├── MIGRATION_COMPLETE.md  # 迁移完成报告
│   └── *.md               # 其他文档
├── logs/                  # 日志文件
│   └── migration.log      # 迁移日志
├── spark_jobs/            # Spark作业
│   ├── pg_to_hdfs.py      # PostgreSQL → HDFS数据迁移
│   └── aggregate_dashboard.py  # Dashboard聚合计算
├── ml_models/             # 机器学习模型
│   ├── xgboost_model.pkl  # XGBoost模型
│   ├── lightgbm_model.pkl # LightGBM模型
│   └── rf_model.pkl       # RandomForest模型
├── static/                # 静态资源
│   ├── css/               # 样式文件（登录页、大屏、增强特效）
│   └── js/                # 前端逻辑
├── templates/             # HTML模板
│   ├── index.html         # 登录/注册页面（炫酷3D特效）
│   ├── dashboard.html     # 数据大屏
│   ├── behavior.html      # 船舶行为分析页面
│   ├── profile.html       # 船舶画像页面
│   ├── quality.html       # 数据质量监控页面
│   ├── lineage.html       # 数据血缘追踪页面
│   ├── ml_predict.html    # 智能风险预测页面
│   └── contract_risk.html # 船舶合同风险分析页面（最终功能）
├── main.py                # FastAPI主应用（2906行）
├── README.md              # 项目说明文档
└── requirements-*.txt     # 依赖配置文件
```

**架构设计**
采用经典分层设计：API → Service → Repository → DB，代码清晰、可扩展，便于后续集成Flink CDC、Kafka、MLflow或Kubernetes。

**作者信息**  
孙帆（Sunstar）  
邮箱：fandesunstar@outlook.com  
微信：+86 18601657185  
求职意向：数据中台可视化 / 大数据开发  
意向城市：上海市   

**快速启动**
```bash
# 1. 安装依赖
pip install fastapi uvicorn psycopg2-binary passlib[bcrypt] pydantic redis clickhouse-connect xgboost lightgbm scikit-learn

# 2. 配置环境变量（或使用默认配置）
export SILVERNAV_DB_HOST=your_host
export SILVERNAV_DB_NAME=silvernav_db
export SILVERNAV_DB_ADMIN_USER=postgres
export SILVERNAV_DB_ADMIN_PASSWORD=your_password

# 3. 初始化数据库（执行DBD/postgreSQL-DBD/下的SQL脚本）
psql -h your_host -U postgres -d silvernav_db -f DBD/postgreSQL-DBD/silvernav_db.sql

# 4. 启动Redis（可选，用于缓存加速）
# 如果有云服务器Redis，配置app/config.py中的Redis连接信息
# 或本地启动：redis-server

# 5. 训练ML模型（可选，已有预训练模型）
python3 scripts/ml/train_ml_models.py
# 或使用快速启动脚本
python3 scripts/ml/quickstart_ml.py

# 6. 启动应用
python main.py
# 或使用启动脚本
bash scripts/start_app.sh
# 或使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 访问应用
# 登录页面：http://localhost:8000
# 数据大屏：http://localhost:8000/dashboard（需先登录）
# 船舶行为分析：http://localhost:8000/behavior
# 船舶画像：http://localhost:8000/profile
# 数据质量监控：http://localhost:8000/quality
# 数据血缘追踪：http://localhost:8000/lineage
# 智能风险预测：http://localhost:8000/ml-predict
# 船舶合同风险：http://localhost:8000/contract-risk
```

**合同风险分析功能**
```bash
# 1. 分析合同PDF（已完成20,000份）
python3 scripts/analyze_contracts_from_hdfs.py --start 1 --end 20000 --batch 100

# 2. 查看统计信息
python3 scripts/analyze_contracts_from_hdfs.py --stats-only

# 3. 测试合同API
python3 scripts/test_contract_api.py

# 4. 访问合同风险分析页面
# http://localhost:8000/contract-risk
```

**开发进度**
- ✅ Phase 0：MVP基础功能（登录认证 + 数据大屏）
- ✅ Phase 1：核心详情页面（船舶行为分析、船舶画像、数据质量、数据血缘）
- ✅ Phase 2：性能优化（ClickHouse集成、Redis缓存、查询性能提升25-60倍）
- ✅ Phase 3：数据迁移（PostgreSQL → ClickHouse完整迁移，8000万+条数据）
- ✅ Phase 4：机器学习集成（XGBoost/LightGBM/RandomForest风险预测模型）
- ✅ Phase 5：UI/UX增强（航运金融科技风，炫酷动画特效，数据血缘可视化）
- ✅ Phase 6：HDFS分布式存储（20,000份船舶融资合同PDF上传至HDFS，426.8 MB）
- ✅ Phase 7：船舶合同风险分析（20,000份合同分析、风险评分、MongoDB存储、可视化展示）**【最终功能模块】**

详细开发路线图请查看 [ROADMAP.md](./ROADMAP.md)

**性能指标**
- Dashboard查询响应时间：从2-3秒降至0.05秒（使用Redis缓存，提升40-60倍）
- OLAP查询性能：ClickHouse比PostgreSQL快25-60倍
- 数据规模：8000万+条历史数据（企业、船舶、金融资产、风险历史、风险因子）
- 合同分析：20,000份PDF文档，100%提取成功，字段完整性100%
- 缓存命中率：Dashboard缓存TTL 5分钟，高频查询性能显著提升
- ML模型性能：XGBoost准确率92%+，预测响应时间<100ms
- 前端渲染：原生JS无框架依赖，首屏加载<1s，动画流畅60fps

**状态与愿景**
当前为MVP阶段，仅用于个人学习与技术展示。欢迎Star、Fork、交流或PR。
愿景：让航运金融风控从经验依赖转向数据与算法驱动，提供透明、高效、可信的数智支撑。

**项目亮点与优势**

🎯 **技术全栈性**
- 涵盖前后端、数据库、大数据、机器学习、可视化全技术栈
- 从数据采集、存储、处理到分析、预测、展示的完整闭环
- 展示了现代数据平台的完整技术架构能力

⚡ **性能优化实践**
- Redis缓存：响应时间从2-3秒降至0.05秒，提升40-60倍
- ClickHouse OLAP：查询性能比PostgreSQL快25-60倍
- 前端原生JS：无框架依赖，首屏加载<1s，动画流畅60fps
- 异步编程：FastAPI异步API，高并发处理能力

🎨 **UI/UX设计**
- 航运金融科技风格，充满未来感和专业感
- 炫酷动画特效：3D翻转、粒子爆发、扫描线、能量脉冲、流星雨、港口场景
- 数据血缘可视化：SVG动态图谱，支持三种视图模式
- 响应式设计：适配桌面端和移动端

🧠 **机器学习集成**
- 集成XGBoost、LightGBM、RandomForest三种主流模型
- 实时风险预测，准确率92%+，响应时间<100ms
- 特征工程：20+维度特征，包括船舶、企业、资产、历史风险等
- 模型可解释性：预留SHAP分析接口

📊 **数据可视化**
- 8大核心板块：总体风险敞口、高风险预警、不良资产监控等
- 多维度分析：多币种、多单位、多时间维度
- 交互式图表：环形图、趋势图、柱状图、数据血缘图谱
- 实时更新：自动刷新机制，数据实时同步

🏗️ **架构设计**
- 分层架构：API → Service → Repository → DB，清晰可扩展
- 微服务友好：模块化设计，易于拆分为微服务
- 容器化就绪：Docker容器化规划，支持K8s部署
- 可观测性：预留日志、监控、追踪接口

💾 **数据处理能力**
- 支持8000万+条历史数据
- Spark批处理：PostgreSQL → HDFS数据迁移
- 多数据源集成：PostgreSQL、ClickHouse、MongoDB、Redis
- PDF文档处理：20,000份合同，PyPDF2文本提取，正则表达式字段匹配
- 预留Kafka实时流处理接口

🔒 **安全性**
- JWT Token认证，HMAC签名
- bcrypt/argon2密码加密
- 账号锁定机制，防暴力破解
- SQL注入防护，参数化查询

📈 **可扩展性**
- 预留Kafka、Flink CDC、MLflow、Kubernetes集成接口
- 支持水平扩展，Redis集群、ClickHouse集群
- 插件化设计，易于添加新功能模块
- API版本控制，向后兼容

🎓 **学习价值**
- 完整的数据平台项目实践
- 涵盖数据工程、数据分析、机器学习、前端开发
- 真实业务场景：航运金融风控
- 代码规范，注释详细，易于学习和二次开发

**免责声明**
本项目不涉及真实商业数据或生产环境使用，仅供技术演示与学习参考。


---

**SilverNav Treasure — Intelligent Risk Control Platform for Shipping Finance**

SilverNav Treasure is a lightweight, personal practice project designed for shipping companies, financial institutions, and supply chain financiers. It delivers intelligent risk control services for vessel credit, financing risks, and operational anomalies through big data and machine learning technologies, enabling multi-source data integration, real-time risk assessment, and decision support.

**Implemented Features**
- ✅ User Authentication System: Login/Registration, JWT Token, Password Policy, Account Lockout Mechanism
- ✅ Data Dashboard: 8 Core Modules Real-time Display (Total Risk Exposure, High-Risk Alerts, Non-Performing Assets Monitoring, Risk Level Distribution, Risk Trends, Top 10 Vessel Risks, Credit Usage Progress, Risk Factor Contribution)
- ✅ Multi-Currency Support: CNY/USD/HKD/GBP/EUR Free Switching, Real-time Exchange Rate Conversion
- ✅ Multi-Unit Switching: Ten Thousand/Million/Ten Million/Hundred Million Yuan
- ✅ Time Dimension Filtering: Today/This Month/Last 7 Days/Last 30 Days/Last 90 Days
- ✅ Data Reference Date Persistence: User-selected Date Remains Unchanged After Page Switching
- ✅ Detail Pages: Vessel Behavior Analysis, Vessel Profile, Data Quality Monitoring, Data Lineage Tracking (4 Core Pages Completed)
- ✅ Data Lineage Visualization: SVG Dynamic Graph, Supporting Process View/Tree View/Network View Three Display Modes
- ✅ Intelligent Risk Prediction: Integrated XGBoost/LightGBM/RandomForest Machine Learning Models, Real-time Vessel Default Risk Prediction
- ✅ ClickHouse Integration: OLAP Database, Query Performance Improved 25-60x, Core Data Migrated (80,317,304 Records)
- ✅ Redis Caching: Dashboard Cache Response Time Reduced from 2-3s to 0.05s, Performance Improved 40-60x
- ✅ Spark Batch Jobs: PostgreSQL → HDFS Data Migration, Dashboard Aggregation Calculation, AIS trajectory analysis（MongoDB）
- ✅ Complete Database Design: User Table, Enterprise Table, Vessel Table, Financial Asset Table, Risk Assessment Table, Exchange Rate Table, etc. 12 Core Tables
- ✅ Cool UI Effects: Shipping Finance Tech Style, Login Page 3D Flip, Particle Burst, Scan Lines, Energy Pulse, and Multiple Animation Effects
- ✅ HDFS Distributed Storage: 20,000 Vessel Financing Contract PDFs Uploaded to HDFS (426.8 MB)
- ✅ Vessel Contract Risk Analysis: 20,000 Contract PDF Analysis, Risk Scoring, Keyword Recognition, Visualization (Final Feature Module)

**Tech Stack**
- Backend: FastAPI + Python 3.12.10 (Async High-Performance API)
- Databases: PostgreSQL 14.20 (Structured Data), ClickHouse 26.1.3.52 (OLAP Analysis), MongoDB 7.0.29 (AIS trajectory analysis, Contract data storage)
- Cache: Redis 6.0.16 (Dashboard Cache, Session Management)
- Big Data: Hadoop 3.3.6 (HDFS Storage), Spark 3.5.1 (PySpark Batch Processing)
- Machine Learning: XGBoost, LightGBM, RandomForest (Risk Prediction Models)
- Document Processing: PyPDF2 (PDF text extraction), Regular expressions (Field matching)
- Stream Processing: Kafka (Reserved for Real-time Stream Processing)
- Frontend: Native JavaScript + HTML5 + CSS3 (No Framework Dependencies, Lightweight and Efficient)
- Visualization: Canvas Animation, SVG Charts, Ring Charts, Trend Charts, Data Lineage Graphs
- Deployment: Local Development Environment (Docker Containerization Planned)
- Others: Pydantic Data Validation, bcrypt/argon2 Password Encryption, HMAC Token Signing

**Project Structure**
```
SilverNav-Treasure/
├── app/                    # Application Core Modules
│   ├── config.py          # Configuration Management
│   ├── database.py        # PostgreSQL Connection Pool
│   ├── clickhouse_client.py  # ClickHouse Client
│   ├── cache.py           # Redis Cache Management
│   ├── behavior_api.py    # Vessel Behavior Analysis API
│   ├── profile_api.py     # Vessel Profile API
│   ├── quality_api.py     # Data Quality API
│   ├── kafka_config.py    # Kafka Configuration (Reserved)
│   └── utils.py           # Utility Functions
├── DBD/                   # Database Design Documents
│   └── postgreSQL-DBD/    # PostgreSQL Table Scripts, Indexes, Query Optimization
├── scripts/               # Script Tools
│   ├── migration/         # Data Migration Scripts
│   │   ├── migrate_all_data.py  # Full Data Migration
│   │   ├── migrate_large_tables.py  # Large Table Migration
│   │   └── check_migration_progress.py  # Migration Progress Check
│   ├── ml/                # Machine Learning Training Scripts
│   │   ├── train_ml_models.py  # Model Training
│   │   ├── train_ml_batch.py   # Batch Training
│   │   └── quickstart_ml.py    # Quick Start
│   ├── generate_contracts_batch.py  # Batch Generate Contract PDFs (20,000 files)
│   ├── upload_contracts_to_hdfs.py  # Upload Contract PDFs to HDFS
│   ├── analyze_contracts_from_hdfs.py  # Analyze Contract PDFs and write to MongoDB
│   ├── test_contract_api.py    # Contract API test script
│   ├── start_app.sh       # Application Startup Script
│   ├── setup_redis_only.sh  # Redis Environment Setup
│   └── verify_real_data.py  # Data Verification Tool
├── tests/                 # Test Files
│   ├── test_credit_api.py  # Credit Assessment API Test
│   ├── test_ml_prediction.py  # ML Prediction Test
│   ├── test_redis_integration.py  # Redis Integration Test
│   └── test_*.py          # Other Test Files
├── docs/                  # Project Documentation
│   ├── ROADMAP.md         # Project Roadmap
│   ├── QUICK_START.md     # Quick Start Guide
│   ├── ML_QUICKSTART.md   # ML Module Quick Start
│   ├── MIGRATION_COMPLETE.md  # Migration Complete Report
│   └── *.md               # Other Documentation
├── logs/                  # Log Files
│   └── migration.log      # Migration Log
├── spark_jobs/            # Spark Jobs
│   ├── pg_to_hdfs.py      # PostgreSQL → HDFS Data Migration
│   └── aggregate_dashboard.py  # Dashboard Aggregation Calculation
├── ml_models/             # Machine Learning Models
│   ├── xgboost_model.pkl  # XGBoost Model
│   ├── lightgbm_model.pkl # LightGBM Model
│   └── rf_model.pkl       # RandomForest Model
├── static/                # Static Resources
│   ├── css/               # Style Files (Login Page, Dashboard, Enhanced Effects)
│   └── js/                # Frontend Logic
├── templates/             # HTML Templates
│   ├── index.html         # Login/Registration Page (Cool 3D Effects)
│   ├── dashboard.html     # Data Dashboard
│   ├── behavior.html      # Vessel Behavior Analysis Page
│   ├── profile.html       # Vessel Profile Page
│   ├── quality.html       # Data Quality Monitoring Page
│   ├── lineage.html       # Data Lineage Tracking Page
│   ├── ml_predict.html    # Intelligent Risk Prediction Page
│   └── contract_risk.html # Vessel Contract Risk Analysis Page (Final Feature)
├── main.py                # FastAPI Main Application (2906 lines)
├── README.md              # Project Documentation
└── requirements-*.txt     # Dependency Configuration Files
```

**Architecture Design**
Classic layered design: API → Service → Repository → DB, clean code, extensible, easy for future integration with Flink CDC, Kafka, MLflow or Kubernetes.

**Author**
Sun Fan (Sunstar)
Email: fandesunstar@outlook.com
WeChat: +86 18601657185
Job Intention: Data Mid-Platform Visualization / Big Data Development
Preferred City: Shanghai

**Quick Start**
```bash
# 1. Install Dependencies
pip install fastapi uvicorn psycopg2-binary passlib[bcrypt] pydantic redis clickhouse-connect xgboost lightgbm scikit-learn

# 2. Configure Environment Variables (or use default configuration)
export SILVERNAV_DB_HOST=your_host
export SILVERNAV_DB_NAME=silvernav_db
export SILVERNAV_DB_ADMIN_USER=postgres
export SILVERNAV_DB_ADMIN_PASSWORD=your_password

# 3. Initialize Database (execute SQL scripts in DBD/postgreSQL-DBD/)
psql -h your_host -U postgres -d silvernav_db -f DBD/postgreSQL-DBD/silvernav_db.sql

# 4. Start Redis (optional, for cache acceleration)
# If you have cloud server Redis, configure Redis connection info in app/config.py
# Or start locally: redis-server

# 5. Train ML Models (optional, pre-trained models available)
python scripts/ml/train_ml_models.py
# Or use quick start script
python scripts/ml/quickstart_ml.py

# 6. Start Application
python main.py
# Or use startup script
bash scripts/start_app.sh
# Or use uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 7. Access Application
# Login Page: http://localhost:8000
# Data Dashboard: http://localhost:8000/dashboard (login required)
# Vessel Behavior Analysis: http://localhost:8000/behavior
# Vessel Profile: http://localhost:8000/profile
# Data Quality Monitoring: http://localhost:8000/quality
# Data Lineage Tracking: http://localhost:8000/lineage
# Intelligent Risk Prediction: http://localhost:8000/ml-predict
# Vessel Contract Risk: http://localhost:8000/contract-risk
```

**Development Progress**
- ✅ Phase 0: MVP Basic Features (Login Authentication + Data Dashboard)
- ✅ Phase 1: Core Detail Pages (Vessel Behavior Analysis, Vessel Profile, Data Quality, Data Lineage)
- ✅ Phase 2: Performance Optimization (ClickHouse Integration, Redis Cache, Query Performance Improved 25-60x)
- ✅ Phase 3: Data Migration (PostgreSQL → ClickHouse Complete Migration, 80M+ Records)
- ✅ Phase 4: Machine Learning Integration (XGBoost/LightGBM/RandomForest Risk Prediction Models)
- ✅ Phase 5: UI/UX Enhancement (Shipping Finance Tech Style, Cool Animation Effects, Data Lineage Visualization)
- ✅ Phase 6: HDFS Distributed Storage (20,000 Vessel Financing Contract PDFs Uploaded to HDFS, 426.8 MB)
- ✅ Phase 7: Vessel Contract Risk Analysis (20,000 Contract PDF Analysis, Risk Scoring, MongoDB Storage, Visualization) **[Final Feature Module]**

For detailed development roadmap, please see [ROADMAP.md](./ROADMAP.md)

**Performance Metrics**
- Dashboard Query Response Time: Reduced from 2-3s to 0.05s (using Redis cache, 40-60x improvement)
- OLAP Query Performance: ClickHouse 25-60x faster than PostgreSQL
- Data Scale: 80M+ historical records (enterprises, vessels, financial assets, risk history, risk factors)
- Contract Analysis: 20,000 PDF documents, 100% extraction success, 100% field integrity
- Cache Hit Rate: Dashboard cache TTL 5 minutes, high-frequency query performance significantly improved
- ML Model Performance: XGBoost accuracy 92%+, prediction response time <100ms
- Frontend Rendering: Native JS no framework dependencies, first screen load <1s, smooth animation 60fps

**Status & Vision**
Currently at MVP stage, for personal learning and technical demonstration only. Welcome Stars, Forks, discussions or PRs.
Vision: Shift shipping finance risk control from experience reliance to data- and algorithm-driven transparency, efficiency, and reliability.

**Project Highlights & Advantages**

🎯 **Full-Stack Technology**
- Covers full-stack: frontend, backend, databases, big data, machine learning, visualization
- Complete closed loop from data collection, storage, processing to analysis, prediction, display
- Demonstrates complete technical architecture capabilities of modern data platforms

⚡ **Performance Optimization Practice**
- Redis Cache: Response time reduced from 2-3s to 0.05s, 40-60x improvement
- ClickHouse OLAP: Query performance 25-60x faster than PostgreSQL
- Frontend Native JS: No framework dependencies, first screen load <1s, smooth animation 60fps
- Async Programming: FastAPI async API, high concurrency processing capability

🎨 **UI/UX Design**
- Shipping finance tech style, full of futuristic and professional feel
- Cool animation effects: 3D flip, particle burst, scan lines, energy pulse, meteor shower, port scene
- Data lineage visualization: SVG dynamic graph, supporting three view modes
- Responsive design: Adapted for desktop and mobile

🧠 **Machine Learning Integration**
- Integrated three mainstream models: XGBoost, LightGBM, RandomForest
- Real-time risk prediction, accuracy 92%+, response time <100ms
- Feature engineering: 20+ dimensional features, including vessel, enterprise, asset, historical risk, etc.
- Model explainability: Reserved SHAP analysis interface

📊 **Data Visualization**
- 8 core modules: Total risk exposure, high-risk alerts, non-performing assets monitoring, etc.
- Multi-dimensional analysis: Multi-currency, multi-unit, multi-time dimension
- Interactive charts: Ring charts, trend charts, bar charts, data lineage graphs
- Real-time updates: Auto-refresh mechanism, data real-time synchronization

🏗️ **Architecture Design**
- Layered architecture: API → Service → Repository → DB, clear and extensible
- Microservice-friendly: Modular design, easy to split into microservices
- Container-ready: Docker containerization planned, supporting K8s deployment
- Observability: Reserved logging, monitoring, tracing interfaces

💾 **Data Processing Capability**
- Supports 80M+ historical records
- Spark batch processing: PostgreSQL → HDFS data migration
- Multi-data source integration: PostgreSQL, ClickHouse, MongoDB, Redis
- PDF document processing: 20,000 contracts, PyPDF2 text extraction, regex field matching
- Reserved Kafka real-time stream processing interface

🔒 **Security**
- JWT Token authentication, HMAC signing
- bcrypt/argon2 password encryption
- Account lockout mechanism, preventing brute force attacks
- SQL injection protection, parameterized queries

📈 **Scalability**
- Reserved Kafka, Flink CDC, MLflow, Kubernetes integration interfaces
- Supports horizontal scaling, Redis cluster, ClickHouse cluster
- Plugin design, easy to add new functional modules
- API version control, backward compatible

🎓 **Learning Value**
- Complete data platform project practice
- Covers data engineering, data analysis, machine learning, frontend development
- Real business scenario: Shipping finance risk control
- Code standards, detailed comments, easy to learn and secondary development

**Disclaimer**
This project uses no real commercial data or production environment; for technical showcase and learning purposes only.