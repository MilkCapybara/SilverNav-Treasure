**银航宝 — 航运金融数智风控与服务平台**

银航宝是一个轻量级、个人练手项目，面向航运企业、金融机构及供应链金融从业者，提供船舶信用、融资风险与运营异常的数智风控服务。通过大数据与机器学习技术，实现多源数据融合、实时风险评估与决策支持。

**已实现功能**
- ✅ 用户认证系统：登录/注册、JWT Token、密码策略、账号锁定机制
- ✅ 数据大屏：8大核心板块实时展示（总体风险敞口、高风险预警、不良资产监控、风险等级分布、风险趋势、船舶风险Top10、授信使用进度、风险因子贡献）
- ✅ 多币种支持：CNY/USD/HKD/GBP/EUR自由切换，实时汇率转换
- ✅ 多单位切换：万元/百万元/千万元/亿元
- ✅ 时间维度筛选：今日/本月/近7天/近30天/近90天
- ✅ 数据钻取框架：预留8个详情页面路由（待开发）
- ✅ Spark批处理作业：PostgreSQL → HDFS数据迁移、Dashboard聚合计算
- ✅ 数据库完整设计：用户表、企业表、船舶表、金融资产表、风险评估表、汇率表等12张核心表

**技术栈**
- 后端：FastAPI + Python 3.12.10（异步高性能API）
- 数据库：PostgreSQL 14.20（结构化数据）、MongoDB 7.0.29（预留AIS轨迹/日志）
- 大数据：Hadoop 3.3.6（HDFS存储）、Spark 3.5.1（PySpark批处理）
- 前端：原生JavaScript + HTML5 + CSS3（无框架依赖）
- 可视化：Canvas动画、SVG图表、环形图、趋势图
- 部署：本地开发环境（Docker容器化规划中）
- 其他：Pydantic数据校验、bcrypt/argon2密码加密、HMAC Token签名

**项目结构**
```
SilverNav-Treasure/
├── app/                    # 应用核心模块
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接池
│   └── utils.py           # 工具函数
├── DBD/                   # 数据库设计文档
│   └── postgreSQL-DBD/    # PostgreSQL建表脚本、索引、查询优化
├── spark_jobs/            # Spark作业
│   ├── pg_to_hdfs.py      # PostgreSQL → HDFS数据迁移
│   └── aggregate_dashboard.py  # Dashboard聚合计算
├── static/                # 静态资源
│   ├── css/               # 样式文件（登录页、大屏）
│   └── js/                # 前端逻辑（登录动画、大屏交互）
├── templates/             # HTML模板
│   ├── index.html         # 登录/注册页面
│   ├── dashboard.html     # 数据大屏
│   └── detail.html        # 详情页面（框架）
└── main.py                # FastAPI主应用（1181行）
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
pip install fastapi uvicorn psycopg2-binary passlib[bcrypt] pydantic

# 2. 配置环境变量（或使用默认配置）
export SILVERNAV_DB_HOST=your_host
export SILVERNAV_DB_NAME=silvernav_db
export SILVERNAV_DB_ADMIN_USER=postgres
export SILVERNAV_DB_ADMIN_PASSWORD=your_password

# 3. 初始化数据库（执行DBD/postgreSQL-DBD/下的SQL脚本）
psql -h your_host -U postgres -d silvernav_db -f DBD/postgreSQL-DBD/silvernav_db.sql

# 4. 启动应用
python main.py
# 或使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 5. 访问应用
# 登录页面：http://localhost:8000
# 数据大屏：http://localhost:8000/dashboard（需先登录）
# 默认管理员账号：root / sunfannb0307SF?
```

**开发进度**
- ✅ Phase 0：MVP基础功能（登录认证 + 数据大屏）
- 🚧 Phase 1：8个详情页面开发（规划中）
- 📋 Phase 2：航运数据功能（AIS轨迹、船舶画像、数据血缘）
- 📋 Phase 3：大数据技术栈集成（Flink CDC、MongoDB、Hadoop完整集成）
- 📋 Phase 4：系统治理功能（RBAC、审计日志、系统监控）

详细开发路线图请查看 [ROADMAP.md](./ROADMAP.md)

**状态与愿景**
当前为MVP阶段，仅用于个人学习与技术展示。欢迎Star、Fork、交流或PR。
愿景：让航运金融风控从经验依赖转向数据与算法驱动，提供透明、高效、可信的数智支撑。

**免责声明**  
本项目不涉及真实商业数据或生产环境使用，仅供技术演示与学习参考。

（约548中文字符）

**SilverNav Treasure — Intelligent Risk Control Platform for Shipping Finance**

SilverNav Treasure is a lightweight, personal practice project designed for shipping companies, financial institutions, and supply chain financiers. It delivers intelligent risk control services for vessel credit, financing risks, and operational anomalies using big data and machine learning.

**Core Features**  
- Multi-source data integration: vessel profiles, AIS trajectories, regulatory records, financial statements  
- ETL pipelines & real-time processing: cleaning, standardization, anomaly detection  
- Quantitative risk models: XGBoost/LightGBM + SHAP explainability, outputting credit scores, default probabilities, fraud alerts  
- Interactive dashboards & reports: FineReport/FineBI visualization, one-click PDF/Excel risk report generation  
- User operations: data upload (Excel/CSV), conditional queries, threshold customization  

**Tech Stack**  
- Backend: FastAPI (high-performance RESTful APIs)  
- Databases: PostgreSQL PostgreSQL 14.20 (Ubuntu 14.20-0ubuntu0.22.04.1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 11.4.0-1ubuntu1~22.04.2) 11.4.0, 64-bit (structured), MongoDB 7.0.29 (unstructured logs/tracks)  
- Big Data: Hadoop 3.3.6 (HDFS/YARN), Spark 3.5.1 (PySpark batch/streaming)  
- Programming: Python 3.12.10 (Pandas/NumPy/asyncio), SQL  
- Visualization: FineReport, FineBI, Streamlit  
- Deployment: Docker  
- Others: Pydantic validation, pytest testing, .env config  

**Project Structure**  
Classic layered architecture: API → Service → Repository → DB, clean and extensible for future Kafka, MLflow or Kubernetes integration.

**Author**  
Sun Fan (Sunstar)  
Email: fandesunstar@outlook.com  
WeChat: +86 18601657185  
Job Intention: Data Mid-Platform Visualization / Big Data Development  
Preferred City: Shanghai  

**Status & Vision**  
Currently at MVP stage, for personal learning and technical demonstration only. Welcome Stars, Forks, discussions or PRs.  
Vision: Shift shipping finance risk control from experience reliance to data- and algorithm-driven transparency, efficiency, and reliability.

**Disclaimer**  
This project uses no real commercial data or production environment; for technical showcase and learning purposes only.

(约520英文字符)