-- ============================================================================
-- 银航宝 ClickHouse 数据库建表脚本
-- 用途：将 PostgreSQL 数据迁移到 ClickHouse 以提升 Dashboard 查询性能
-- 目标：将 20s 查询时间降低到 1s 以内
-- ============================================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS silvernav;

USE silvernav;

-- ============================================================================
-- 1. 企业表 (companies)
-- 引擎：ReplacingMergeTree - 支持数据更新（按 id 去重）
-- 分区：按创建年月分区
-- 排序：按 id 排序，支持快速点查
-- ============================================================================
CREATE TABLE IF NOT EXISTS companies (
    id Int64,
    company_name String,
    registration_country String,
    company_type String,
    credit_score Decimal(5, 2),
    risk_level String,
    is_active UInt8,
    created_at DateTime,
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(created_at)
ORDER BY (id)
SETTINGS index_granularity = 8192;

-- ============================================================================
-- 2. 船舶表 (vessels)
-- 引擎：ReplacingMergeTree - 支持数据更新
-- 分区：按创建年月分区
-- 排序：按 id 和 owner_company_id 排序，支持企业维度查询
-- ============================================================================
CREATE TABLE IF NOT EXISTS vessels (
    id Int64,
    imo_number String,
    vessel_name String,
    vessel_type String,
    build_year Int32,
    flag_country String,
    owner_company_id Int64,
    asset_risk_score Decimal(5, 2),
    risk_level String,
    is_active UInt8,
    created_at DateTime,
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(created_at)
ORDER BY (id, owner_company_id)
SETTINGS index_granularity = 8192;

-- ============================================================================
-- 3. 金融资产表 (financial_assets)
-- 引擎：ReplacingMergeTree - 支持数据更新
-- 分区：按起始日期年月分区（重要：按时间分区提升查询性能）
-- 排序：按 risk_level, company_id, start_date 排序
-- 说明：这是 Dashboard 最核心的表，查询频率最高
-- ============================================================================
CREATE TABLE IF NOT EXISTS financial_assets (
    id Int64,
    company_id Int64,
    vessel_id Nullable(Int64),
    asset_type String,
    contract_no String,
    principal_amount Decimal(18, 2),
    outstanding_amount Decimal(18, 2),
    currency String,
    interest_rate Nullable(Decimal(8, 4)),
    start_date Date,
    maturity_date Date,
    risk_level String,
    risk_score Nullable(Decimal(5, 2)),
    is_non_performing UInt8,
    is_active UInt8,
    created_at DateTime,
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(start_date)
ORDER BY (risk_level, company_id, start_date, id)
SETTINGS index_granularity = 8192;

-- ============================================================================
-- 4. 船舶风险历史表 (vessel_risk_history)
-- 引擎：MergeTree - 只追加，不更新
-- 分区：按评估日期年月分区
-- 排序：按 assessment_date, vessel_id 排序，支持时间序列查询
-- ============================================================================
CREATE TABLE IF NOT EXISTS vessel_risk_history (
    id Int64,
    vessel_id Int64,
    assessment_date Date,
    risk_score Decimal(5, 2),
    risk_level String,
    created_at DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(assessment_date)
ORDER BY (assessment_date, vessel_id)
SETTINGS index_granularity = 8192;

-- ============================================================================
-- 5. 风险因子贡献表 (risk_factor_contribution)
-- 引擎：MergeTree - 只追加
-- 分区：按创建日期年月分区
-- 排序：按 created_at, target_type, target_id 排序
-- ============================================================================
CREATE TABLE IF NOT EXISTS risk_factor_contribution (
    id Int64,
    target_type String,
    target_id Int64,
    factor_name String,
    factor_value Decimal(10, 4),
    contribution Decimal(10, 4),
    model_version String,
    created_at DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (toDate(created_at), target_type, target_id)
SETTINGS index_granularity = 8192;

-- ============================================================================
-- 6. 外汇汇率表 (fx_rates)
-- 引擎：ReplacingMergeTree - 支持汇率更新
-- 分区：按汇率日期年月分区
-- 排序：按 rate_date, base_currency, quote_currency 排序
-- ============================================================================
CREATE TABLE IF NOT EXISTS fx_rates (
    id Int64,
    base_currency String,
    quote_currency String,
    rate Decimal(12, 6),
    rate_date Date,
    source String,
    created_at DateTime,
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(rate_date)
ORDER BY (rate_date, base_currency, quote_currency)
SETTINGS index_granularity = 8192;

-- ============================================================================
-- 物化视图：Dashboard 核心指标预聚合
-- 用途：加速 Dashboard 总体风险敞口查询
-- 更新：数据插入时自动更新
-- ============================================================================

-- 7.1 每日风险敞口汇总（按风险等级）
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_risk_exposure
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(stat_date)
ORDER BY (stat_date, risk_level, currency)
AS SELECT
    toDate(start_date) AS stat_date,
    risk_level,
    currency,
    count() AS asset_count,
    sum(outstanding_amount) AS total_exposure,
    sumIf(outstanding_amount, is_non_performing = 1) AS npl_amount
FROM financial_assets
WHERE is_active = 1
GROUP BY stat_date, risk_level, currency;

-- 7.2 企业风险等级分布（每日快照）
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_company_risk
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(stat_date)
ORDER BY (stat_date, risk_level)
AS SELECT
    today() AS stat_date,
    risk_level,
    count() AS company_count
FROM companies
WHERE is_active = 1
GROUP BY stat_date, risk_level;

-- 7.3 船舶风险等级分布（每日快照）
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_vessel_risk
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(stat_date)
ORDER BY (stat_date, risk_level)
AS SELECT
    today() AS stat_date,
    risk_level,
    count() AS vessel_count
FROM vessels
WHERE is_active = 1
GROUP BY stat_date, risk_level;

-- ============================================================================
-- 索引优化
-- ============================================================================

-- 为 financial_assets 创建跳数索引（加速范围查询）
ALTER TABLE financial_assets ADD INDEX idx_start_date start_date TYPE minmax GRANULARITY 4;
ALTER TABLE financial_assets ADD INDEX idx_maturity_date maturity_date TYPE minmax GRANULARITY 4;
ALTER TABLE financial_assets ADD INDEX idx_risk_level risk_level TYPE set(10) GRANULARITY 4;

-- 为 vessel_risk_history 创建跳数索引
ALTER TABLE vessel_risk_history ADD INDEX idx_assessment_date assessment_date TYPE minmax GRANULARITY 4;

-- ============================================================================
-- 查询优化建议
-- ============================================================================
-- 1. 使用 PREWHERE 替代 WHERE 进行主键过滤
-- 2. 利用物化视图查询预聚合数据
-- 3. 使用 toYYYYMM() 函数进行分区裁剪
-- 4. 避免 SELECT *，只查询需要的列
-- 5. 使用 FINAL 关键字获取最新数据（ReplacingMergeTree）
-- ============================================================================

-- 示例优化查询：
-- 原始查询：
-- SELECT * FROM financial_assets WHERE start_date >= '2026-01-01' AND risk_level = 'high';
--
-- 优化后：
-- SELECT id, company_id, outstanding_amount, risk_score
-- FROM financial_assets FINAL
-- PREWHERE risk_level = 'high'
-- WHERE start_date >= '2026-01-01';

-- ============================================================================
-- 性能测试查询
-- ============================================================================

-- 测试1：总体风险敞口查询（Dashboard 核心查询）
-- SELECT
--     risk_level,
--     sum(outstanding_amount) AS total_exposure
-- FROM financial_assets FINAL
-- WHERE is_active = 1
--   AND start_date <= today()
--   AND maturity_date >= today()
-- GROUP BY risk_level;

-- 测试2：使用物化视图查询（更快）
-- SELECT
--     risk_level,
--     sum(total_exposure) AS total_exposure
-- FROM mv_daily_risk_exposure
-- WHERE stat_date = today()
--   AND currency = 'CNY'
-- GROUP BY risk_level;

-- ============================================================================
-- 数据保留策略（可选）
-- ============================================================================

-- 设置 TTL：自动删除 3 年前的历史数据
-- ALTER TABLE vessel_risk_history MODIFY TTL assessment_date + INTERVAL 3 YEAR;
-- ALTER TABLE risk_factor_contribution MODIFY TTL created_at + INTERVAL 3 YEAR;

-- ============================================================================
-- 完成
-- ============================================================================
-- 建表脚本创建完成
-- 下一步：运行数据迁移脚本 migrate_to_clickhouse.py
-- ============================================================================
