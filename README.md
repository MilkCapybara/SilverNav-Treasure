**银航宝 — 航运金融数智风控与服务平台**

银航宝是一个轻量级、个人练手项目，面向航运企业、金融机构及供应链金融从业者，提供船舶信用、融资风险与运营异常的数智风控服务。通过大数据与机器学习技术，实现多源数据融合、实时风险评估与决策支持。

**核心功能**  
- 多源数据接入：船舶基础信息、AIS轨迹、海事监管记录、财务报表  
- ETL管道与实时处理：数据清洗、标准化、异常检测  
- 风险量化模型：XGBoost/LightGBM + SHAP可解释性，输出信用分、违约概率、欺诈预警  
- 交互式仪表盘与报告：FineReport/FineBI可视化，一键生成PDF/Excel风险报告  
- 用户操作：数据上传（Excel/CSV）、条件查询、阈值调整  

**技术栈**  
- 后端：FastAPI（高性能RESTful API）  
- 数据库：PostgreSQL PostgreSQL 14.20 (Ubuntu 14.20-0ubuntu0.22.04.1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 11.4.0-1ubuntu1~22.04.2) 11.4.0, 64-bit（结构化）、MongoDB 7.0.29（非结构化日志/轨迹）  
- 大数据：Hadoop 3.3.6 (HDFS/YARN)、Spark 3.5.1 (PySpark批处理/流式计算)  
- 编程：Python 3.12.10 (Pandas/NumPy/asyncio)、SQL  
- 可视化：FineReport、FineBI、Streamlit  
- 部署：Docker容器化  
- 其他：Pydantic校验、pytest测试、.env配置  

**项目结构**  
采用经典分层设计：API → Service → Repository → DB，代码清晰、可扩展，便于后续集成Kafka、MLflow或Kubernetes。

**作者信息**  
孙帆（Sunstar）  
邮箱：fandesunstar@outlook.com  
微信：+86 18601657185  
求职意向：数据中台可视化 / 大数据开发  
意向城市：上海市   

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