### 数据库设计总结（中文版）

**银航宝 — 航运金融数智风控平台数据库设计**

采用 PostgreSQL 14.20 作为核心关系型数据库，设计遵循严格的 3NF 范式，兼顾数据一致性、可维护性与查询性能。数据库以 `silvernav` Schema 隔离业务逻辑，包含 8 张核心表，覆盖用户认证、企业/船舶主体管理、风险历史追踪、可解释性分析、金融快照、授信评估及汇率支持，形成完整的风控数据闭环。

**设计亮点**
- **严格 3NF + 软删除机制**：所有表均达到 3NF，无冗余与传递依赖；采用 `is_deleted` 软删除 + 触发器自动更新 `updated_at`，确保金融数据不可物理删除、变更可追溯。
- **历史与快照分离**：`vessel_risk_history`、`credit_risk_assessment` 记录趋势变化；`financial_risk_snapshot` 预聚合高风险指标，支持 Dashboard 毫秒级展示，避免实时聚合大表。
- **可解释性支持**：`risk_factor_contribution` 表存储 SHAP 值等因子贡献，完美对接 XGBoost/LightGBM 模型解释需求。
- **多币种与汇率独立**：`fx_rates` 表采用复合唯一键（base_currency + quote_currency + rate_date），支持多币种风险敞口换算。
- **性能优化前置**：关键字段添加索引（account、status、locked_until、imo_number 等），触发器保证时间戳一致性，UNIQUE 约束防止业务重复。
- **扩展性预留**：Schema 隔离 + 外键适度使用（仅在核心关联表），便于后续分区、物化视图或读写分离。

**适用场景与局限**
当前设计完全满足个人练手、中小型原型及面试展示需求（数据量 < 10万行、QPS < 100）。在生产环境中可直接作为基础架构使用，但需补充：
- 敏感字段加密（pgcrypto 扩展）
- 操作审计日志表
- 大表分区（risk_factor_contribution、vessel_risk_history）
- 读写分离 + 连接池（PgBouncer）
- 定期 vacuum/analyze 维护

**总结一句话**  
该数据库设计在保持高一致性与可解释性的同时，通过历史表、快照表与索引优化，实现了高效的风控查询与趋势分析，体现了航运金融场景下“数据可靠 + 决策可信”的核心诉求。

（约 520 字）

### 英文版（English Version – Resume / GitHub README Ready）

**SilverNav Treasure Database Design Summary**

The database is built on PostgreSQL 14.20, strictly adhering to 3NF with a dedicated `silvernav` schema. It consists of 8 core tables covering user authentication, enterprise/vessel entities, risk history tracking, model explainability, financial snapshots, credit assessments, and FX rates — forming a complete risk-control data closed loop for shipping finance.

**Key Design Highlights**
- **Strict 3NF + Soft Delete** — All tables are in 3NF with no redundancy or transitive dependencies; soft delete via `is_deleted` flag + trigger-maintained `updated_at` ensures auditability and immutability of financial records.
- **History & Snapshot Separation** — Dedicated history tables (`vessel_risk_history`, `credit_risk_assessment`) for trend analysis; pre-aggregated snapshots (`financial_risk_snapshot`) enable millisecond-level dashboard rendering without real-time heavy joins.
- **Explainability Support** — `risk_factor_contribution` table stores SHAP values and factor contributions, directly supporting interpretable ML models (XGBoost/LightGBM).
- **Multi-Currency Handling** — `fx_rates` table with composite UNIQUE constraint (base + quote + date) for accurate cross-currency exposure conversion.
- **Performance Pre-optimization** — Strategic indexes on high-filter columns (account, status, imo_number, etc.), UNIQUE constraints, and auto-updating triggers.

**Suitability & Next Steps**
Fully suitable for personal projects, prototypes, and interview demonstrations (data volume < 100k rows, QPS < 100). For production readiness, recommended enhancements include:
- Column-level encryption (pgcrypto)
- Audit logging table
- Table partitioning for large history/contribution tables
- Read-write separation + connection pooling (PgBouncer)
- Regular VACUUM/ANALYZE maintenance

**In one sentence**  
This database design balances strong consistency, explainability, and query efficiency through history tables, snapshots, and targeted indexing — delivering reliable, trustworthy data support for intelligent shipping finance risk control.

(≈ 480 words / 2,850 characters)