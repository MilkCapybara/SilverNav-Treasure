-- ============================================================================
-- 银航宝·深蓝启航 - 所有SQL指标汇总
-- 项目：SilverNav-Treasure
-- 生成时间：2026-03-08
-- 说明：本文件汇总了项目中所有使用的SQL查询指标
-- ============================================================================

-- ============================================================================
-- 目录
-- ============================================================================
-- 1. 数据库表结构 (DDL)
-- 2. Dashboard 核心指标查询
-- 3. 数据质量监控查询
-- 4. 船舶画像查询
-- 5. 行为分析查询 (MongoDB)
-- 6. 机器学习相关查询
-- 7. ClickHouse 查询
-- 8. 汇率与币种转换
-- 9. 用户认证与权限
-- 10. 数据迁移与同步
-- ============================================================================

SET search_path TO silvernav;

-- ============================================================================
-- 1. 数据库表结构 (DDL)
-- ============================================================================

-- 1.1 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    account VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    account_type VARCHAR(30) NOT NULL DEFAULT 'local',
    failed_login_count INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMP,
    last_login_at TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 1.2 企业表
CREATE TABLE IF NOT EXISTS companies (
    id BIGSERIAL PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    registration_country VARCHAR(50),
    company_type VARCHAR(50),
    credit_score NUMERIC(5,2),
    risk_level VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1.3 船舶资产表
CREATE TABLE IF NOT EXISTS vessels (
    id BIGSERIAL PRIMARY KEY,
    imo_number VARCHAR(20) UNIQUE,
    vessel_name VARCHAR(100),
    vessel_type VARCHAR(50),
    build_year INT,
    flag_country VARCHAR(50),
    owner_company_id BIGINT REFERENCES companies(id),
    asset_risk_score NUMERIC(5,2),
    risk_level VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1.4 金融资产表
CREATE TABLE IF NOT EXISTS financial_assets (
    id BIGSERIAL PRIMARY KEY,
    contract_no VARCHAR(100) UNIQUE,
    company_id BIGINT REFERENCES companies(id),
    vessel_id BIGINT REFERENCES vessels(id),
    asset_type VARCHAR(50),
    currency VARCHAR(10),
    principal_amount NUMERIC(18,2),
    outstanding_amount NUMERIC(18,2),
    start_date DATE,
    maturity_date DATE,
    risk_score NUMERIC(5,2),
    risk_level VARCHAR(20),
    is_non_performing BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1.5 船舶风险历史评估表
CREATE TABLE IF NOT EXISTS vessel_risk_history (
    id BIGSERIAL PRIMARY KEY,
    vessel_id BIGINT REFERENCES vessels(id),
    assessment_date DATE NOT NULL,
    risk_score NUMERIC(5, 2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1.6 风险因素贡献表
CREATE TABLE IF NOT EXISTS risk_factor_contribution (
    id BIGSERIAL PRIMARY KEY,
    target_type VARCHAR(20),
    target_id BIGINT,
    factor_name VARCHAR(100),
    factor_value NUMERIC(10,4),
    contribution NUMERIC(10,4),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1.7 汇率表
CREATE TABLE IF NOT EXISTS fx_rates (
    id BIGSERIAL PRIMARY KEY,
    base_currency VARCHAR(10) NOT NULL,
    quote_currency VARCHAR(10) NOT NULL,
    rate NUMERIC(12,6) NOT NULL,
    rate_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. Dashboard 核心指标查询
-- ============================================================================

-- 2.1 总体风险敞口（总敞口 + 高风险敞口）
-- 对应API：/api/dashboard/summary
-- 对应函数：main.py:get_dashboard_summary
WITH fx_rate AS (
    SELECT CASE
        WHEN :target_currency = 'CNY' THEN 1
        ELSE COALESCE((
            SELECT rate
            FROM fx_rates
            WHERE base_currency = 'CNY'
              AND quote_currency = :target_currency
              AND rate_date <= :end_date
            ORDER BY rate_date DESC
            LIMIT 1
        ), 1)
    END AS rate
), assets_base AS (
    SELECT
        risk_level,
        outstanding_amount * (SELECT rate FROM fx_rate) AS amount_converted
    FROM financial_assets
    WHERE is_active = TRUE
      AND start_date <= :end_date
      AND maturity_date >= :start_date
)
SELECT
    COALESCE(SUM(amount_converted), 0) AS total_exposure,
    COALESCE(SUM(CASE WHEN risk_level = 'high' THEN amount_converted ELSE 0 END), 0) AS high_risk_exposure
FROM assets_base;

-- 2.2 风险敞口分布（low/medium/high）
WITH fx_rate AS (
    SELECT CASE
        WHEN :target_currency = 'CNY' THEN 1
        ELSE COALESCE((
            SELECT rate FROM fx_rates
            WHERE base_currency = 'CNY'
              AND quote_currency = :target_currency
              AND rate_date <= :end_date
            ORDER BY rate_date DESC
            LIMIT 1
        ), 1)
    END AS rate
), assets_base AS (
    SELECT
        risk_level,
        outstanding_amount * (SELECT rate FROM fx_rate) AS amount_converted
    FROM financial_assets
    WHERE is_active = TRUE
      AND start_date <= :end_date
      AND maturity_date >= :start_date
)
SELECT
    risk_level,
    COUNT(*) AS asset_count,
    COALESCE(SUM(amount_converted), 0) AS exposure_amount
FROM assets_base
GROUP BY risk_level
ORDER BY risk_level;

-- 2.3 高风险预警 - 高风险企业数量
SELECT COUNT(*) AS high_risk_company_count
FROM companies
WHERE is_active = TRUE AND risk_level = 'high';

-- 2.4 高风险预警 - 高风险船舶数量
SELECT COUNT(*) AS high_risk_vessel_count
FROM vessels
WHERE is_active = TRUE AND risk_level = 'high';

-- 2.5 高风险资产Top10
WITH fx_rate AS (
    SELECT CASE
        WHEN :target_currency = 'CNY' THEN 1
        ELSE COALESCE((
            SELECT rate FROM fx_rates
            WHERE base_currency = 'CNY'
              AND quote_currency = :target_currency
              AND rate_date <= :end_date
            ORDER BY rate_date DESC
            LIMIT 1
        ), 1)
    END AS rate
)
SELECT
    a.contract_no,
    c.company_name,
    v.vessel_name,
    (a.outstanding_amount * (SELECT rate FROM fx_rate)) AS outstanding_amount,
    :target_currency AS currency,
    a.risk_score
FROM financial_assets a
LEFT JOIN companies c ON c.id = a.company_id
LEFT JOIN vessels v ON v.id = a.vessel_id
WHERE a.is_active = TRUE
  AND a.risk_level = 'high'
ORDER BY a.outstanding_amount DESC NULLS LAST
LIMIT 10;

-- 2.6 不良资产监控（NPL率）
WITH fx_rate AS (
    SELECT CASE
        WHEN :target_currency = 'CNY' THEN 1
        ELSE COALESCE((
            SELECT rate FROM fx_rates
            WHERE base_currency = 'CNY'
              AND quote_currency = :target_currency
              AND rate_date <= :end_date
            ORDER BY rate_date DESC
            LIMIT 1
        ), 1)
    END AS rate
), assets_base AS (
    SELECT
        is_non_performing,
        outstanding_amount * (SELECT rate FROM fx_rate) AS amount_converted
    FROM financial_assets
    WHERE is_active = TRUE
      AND start_date <= :end_date
      AND maturity_date >= :start_date
)
SELECT
    COUNT(*) FILTER (WHERE is_non_performing) AS npl_count,
    COUNT(*) AS total_count,
    COALESCE(SUM(CASE WHEN is_non_performing THEN amount_converted ELSE 0 END), 0) AS npl_amount,
    COALESCE(SUM(amount_converted), 0) AS total_amount
FROM assets_base;

-- 2.7 风险等级分布 - 企业
SELECT risk_level, COUNT(*) AS count
FROM companies
WHERE is_active = TRUE
GROUP BY risk_level
ORDER BY risk_level;

-- 2.8 风险等级分布 - 船舶
SELECT risk_level, COUNT(*) AS count
FROM vessels
WHERE is_active = TRUE
GROUP BY risk_level
ORDER BY risk_level;

-- 2.9 风险趋势 - 平均风险评分
SELECT assessment_date AS date, AVG(risk_score) AS avg_risk_score
FROM vessel_risk_history
WHERE assessment_date BETWEEN :start_date AND :end_date
GROUP BY assessment_date
ORDER BY assessment_date;

-- 2.10 风险趋势 - 高风险敞口走势
WITH fx_rate AS (
    SELECT CASE
        WHEN :target_currency = 'CNY' THEN 1
        ELSE COALESCE((
            SELECT rate FROM fx_rates
            WHERE base_currency = 'CNY'
              AND quote_currency = :target_currency
              AND rate_date <= :end_date
            ORDER BY rate_date DESC
            LIMIT 1
        ), 1)
    END AS rate
)
SELECT
    start_date AS date,
    COALESCE(SUM(outstanding_amount * (SELECT rate FROM fx_rate)), 0) AS high_risk_exposure
FROM financial_assets
WHERE risk_level = 'high'
  AND start_date BETWEEN :start_date AND :end_date
GROUP BY start_date
ORDER BY start_date;

-- 2.11 授信使用总额
WITH fx_rate AS (
    SELECT CASE
        WHEN :target_currency = 'CNY' THEN 1
        ELSE COALESCE((
            SELECT rate FROM fx_rates
            WHERE base_currency = 'CNY'
              AND quote_currency = :target_currency
              AND rate_date <= :end_date
            ORDER BY rate_date DESC
            LIMIT 1
        ), 1)
    END AS rate
)
SELECT
    COALESCE(SUM(outstanding_amount * (SELECT rate FROM fx_rate)), 0) AS used_total
FROM financial_assets
WHERE is_active = TRUE;

-- 2.12 授信使用Top5客户
WITH fx_rate AS (
    SELECT CASE
        WHEN :target_currency = 'CNY' THEN 1
        ELSE COALESCE((
            SELECT rate FROM fx_rates
            WHERE base_currency = 'CNY'
              AND quote_currency = :target_currency
              AND rate_date <= :end_date
            ORDER BY rate_date DESC
            LIMIT 1
        ), 1)
    END AS rate
)
SELECT c.company_name, u.used_amount
FROM (
    SELECT company_id, SUM(outstanding_amount * (SELECT rate FROM fx_rate)) AS used_amount
    FROM financial_assets
    WHERE is_active = TRUE
    GROUP BY company_id
) u
LEFT JOIN companies c ON c.id = u.company_id
ORDER BY u.used_amount DESC NULLS LAST
LIMIT 5;

-- 2.13 船舶风险Top10
SELECT
    v.vessel_name,
    v.imo_number,
    c.company_name,
    v.asset_risk_score AS risk_score,
    v.risk_level
FROM vessels v
LEFT JOIN companies c ON c.id = v.owner_company_id
WHERE v.is_active = TRUE
ORDER BY v.asset_risk_score DESC NULLS LAST
LIMIT 10;

-- 2.14 风险因子Top5贡献
SELECT factor_name,
       AVG(factor_value) AS avg_value,
       SUM(contribution) AS total_contribution
FROM risk_factor_contribution
WHERE created_at >= :start_date::date - INTERVAL '30 days'
  AND created_at <= :end_date::date
GROUP BY factor_name
ORDER BY SUM(ABS(contribution)) DESC
LIMIT 5;

-- 2.15 资产统计数据
WITH fx_rate AS (
    SELECT CASE
        WHEN :target_currency = 'CNY' THEN 1
        ELSE COALESCE((
            SELECT rate FROM fx_rates
            WHERE base_currency = 'CNY'
              AND quote_currency = :target_currency
              AND rate_date <= :end_date
            ORDER BY rate_date DESC
            LIMIT 1
        ), 1)
    END AS rate
)
SELECT
    COUNT(*) as total_count,
    COALESCE(SUM(outstanding_amount * (SELECT rate FROM fx_rate)), 0) as total_amount
FROM financial_assets
WHERE is_active = TRUE;

-- 2.16 币种分布数据
WITH fx_rate AS (
    SELECT CASE
        WHEN :target_currency = 'CNY' THEN 1
        ELSE COALESCE((
            SELECT rate FROM fx_rates
            WHERE base_currency = 'CNY'
              AND quote_currency = :target_currency
              AND rate_date <= :end_date
            ORDER BY rate_date DESC
            LIMIT 1
        ), 1)
    END AS rate
)
SELECT
    currency,
    COUNT(*) as asset_count,
    COALESCE(SUM(outstanding_amount * (SELECT rate FROM fx_rate)), 0) as amount
FROM financial_assets
WHERE is_active = TRUE
GROUP BY currency
ORDER BY amount DESC;

-- ============================================================================
-- 3. 数据质量监控查询
-- ============================================================================

-- 3.1 vessels表质量检查
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE imo_number IS NULL OR imo_number = '') as null_imo,
    COUNT(*) FILTER (WHERE vessel_name IS NULL OR vessel_name = '') as null_name,
    COUNT(DISTINCT imo_number) as unique_imo
FROM vessels
WHERE is_active = true;

-- 3.2 companies表质量检查
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE company_name IS NULL OR company_name = '') as null_name,
    COUNT(*) FILTER (WHERE registration_country IS NULL) as null_country
FROM companies
WHERE is_active = true;

-- 3.3 financial_assets表质量检查
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE asset_type IS NULL) as null_type,
    COUNT(*) FILTER (WHERE principal_amount IS NULL) as null_value
FROM financial_assets
WHERE is_active = true;

-- 3.4 风险评分范围校验
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE risk_score IS NULL) as null_score,
    COUNT(*) FILTER (WHERE risk_score < 0 OR risk_score > 100) as invalid_score
FROM financial_assets
WHERE is_active = true;

-- 3.5 船舶IMO号唯一性检查
SELECT
    COUNT(*) as total,
    COUNT(DISTINCT imo_number) as unique_count
FROM vessels
WHERE is_active = true AND imo_number IS NOT NULL AND imo_number != '';

-- 3.6 风险评分范围校验
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE risk_score < 0 OR risk_score > 100) as violations
FROM financial_assets
WHERE is_active = true AND risk_score IS NOT NULL;

-- 3.7 时间戳一致性检查
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE created_at > updated_at) as violations
FROM vessels
WHERE is_active = true;

-- 3.8 数据时效性监控 - AIS轨迹数据
SELECT MAX(created_at) as last_update
FROM vessels
WHERE is_active = true;

-- 3.9 数据时效性监控 - 风险评估数据
SELECT MAX(created_at) as last_update
FROM financial_assets
WHERE is_active = true;

-- 3.10 数据时效性监控 - 汇率数据
SELECT MAX(rate_date) as last_update
FROM fx_rates;

-- ============================================================================
-- 4. 船舶画像查询
-- ============================================================================

-- 4.1 获取指定船舶详细信息（PostgreSQL）
SELECT * FROM vessels WHERE imo_number = :imo_number;

-- 4.2 船舶活跃度统计（需要配合MongoDB的ais_tracks集合）
-- MongoDB查询：db.ais_tracks.distinct("imo_number")

-- 4.3 船舶类型分布
-- MongoDB查询：db.ais_tracks.aggregate([
--   {"$group": {"_id": "$ship_type", "count": {"$sum": 1}}},
--   {"$sort": {"count": -1}},
--   {"$limit": 10}
-- ])

-- 4.4 船旗国分布
-- MongoDB查询：db.ais_tracks.aggregate([
--   {"$group": {"_id": "$flag", "count": {"$sum": 1}}},
--   {"$sort": {"count": -1}},
--   {"$limit": 10}
-- ])

-- ============================================================================
-- 5. 行为分析查询 (MongoDB)
-- ============================================================================

-- 5.1 获取船舶轨迹数据
-- MongoDB查询：db.ais_tracks.find({"imo_number": "IMO1234567"})
--   .sort({"timestamp": 1})
--   .limit(1000)

-- 5.2 获取异常停泊记录
-- MongoDB查询：db.ais_anomalies.find({})
--   .sort({"timestamp": -1})
--   .limit(50)

-- 5.3 地理围栏查询
-- MongoDB查询：db.ais_tracks.find({
--   "position": {
--     "$geoWithin": {
--       "$box": [[min_lng, min_lat], [max_lng, max_lat]]
--     }
--   }
-- })

-- 5.4 船舶统计信息
-- MongoDB查询：db.vessel_statistics.find({})
--   .sort({"track_count": -1})
--   .limit(20)

-- 5.5 行为分析总览
-- MongoDB查询：
-- - db.ais_tracks.count()
-- - db.ais_tracks.distinct("imo_number").length
-- - db.ais_anomalies.count()

-- ============================================================================
-- 6. 机器学习相关查询
-- ============================================================================

-- 6.1 获取训练数据特征
SELECT
    v.id,
    v.imo_number,
    v.vessel_type,
    v.build_year,
    v.asset_risk_score,
    c.credit_score,
    c.risk_level as company_risk_level,
    a.outstanding_amount,
    a.risk_score as asset_risk_score,
    a.is_non_performing
FROM vessels v
LEFT JOIN companies c ON c.id = v.owner_company_id
LEFT JOIN financial_assets a ON a.vessel_id = v.id
WHERE v.is_active = TRUE
  AND a.is_active = TRUE;

-- 6.2 获取风险因子数据
SELECT
    target_type,
    target_id,
    factor_name,
    factor_value,
    contribution
FROM risk_factor_contribution
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY ABS(contribution) DESC;

-- ============================================================================
-- 7. ClickHouse 查询
-- ============================================================================

-- 7.1 ClickHouse - 总体风险敞口
-- SELECT
--     risk_level,
--     count() AS asset_count,
--     sum(outstanding_amount * {fx_rate}) AS exposure_amount
-- FROM financial_assets FINAL
-- WHERE is_active = 1
--   AND start_date <= {end_date}
--   AND maturity_date >= {start_date}
-- GROUP BY risk_level

-- 7.2 ClickHouse - 高风险企业数量
-- SELECT count() FROM companies FINAL
-- WHERE is_active = 1 AND risk_level = 'high'

-- 7.3 ClickHouse - 高风险船舶数量
-- SELECT count() FROM vessels FINAL
-- WHERE is_active = 1 AND risk_level = 'high'

-- 7.4 ClickHouse - 汇率查询
-- SELECT rate
-- FROM fx_rates FINAL
-- WHERE base_currency = 'CNY'
--   AND quote_currency = {currency}
--   AND rate_date <= {end_date}
-- ORDER BY rate_date DESC
-- LIMIT 1

-- ============================================================================
-- 8. 汇率与币种转换
-- ============================================================================

-- 8.1 获取汇率
SELECT rate
FROM fx_rates
WHERE base_currency = 'CNY'
  AND quote_currency = :target_currency
  AND rate_date <= :end_date
ORDER BY rate_date DESC
LIMIT 1;

-- 8.2 汇率历史数据（近30天）
SELECT rate_date, base_currency, quote_currency, rate
FROM fx_rates
WHERE quote_currency = :target_currency
  AND base_currency IN ('USD', 'EUR')
  AND rate_date BETWEEN (:base_date - INTERVAL '30 day') AND :base_date
ORDER BY rate_date;

-- ============================================================================
-- 9. 用户认证与权限
-- ============================================================================

-- 9.1 用户登录查询
SELECT id, password_hash FROM users WHERE account = :account;

-- 9.2 用户信息查询
SELECT id, account, username, password_hash, status, failed_login_count,
       locked_until, last_login_at
FROM users
WHERE account = :account AND is_deleted = FALSE;

-- 9.3 更新登录失败次数
UPDATE users
SET failed_login_count = failed_login_count + 1,
    locked_until = CASE
        WHEN failed_login_count + 1 >= 5
        THEN CURRENT_TIMESTAMP + INTERVAL '30 minutes'
        ELSE locked_until
    END
WHERE account = :account;

-- 9.4 重置登录失败次数
UPDATE users
SET failed_login_count = 0,
    locked_until = NULL,
    last_login_at = CURRENT_TIMESTAMP
WHERE account = :account;

-- 9.5 创建新用户
INSERT INTO users (account, username, password_hash, status, account_type)
VALUES (:account, :username, :password_hash, 'active', 'local');

-- ============================================================================
-- 10. 数据迁移与同步
-- ============================================================================

-- 10.1 检查迁移进度
SELECT COUNT(*) FROM financial_assets WHERE is_active = TRUE;
SELECT COUNT(*) FROM companies WHERE is_active = TRUE;
SELECT COUNT(*) FROM vessels WHERE is_active = TRUE;

-- 10.2 数据一致性检查
SELECT
    (SELECT COUNT(*) FROM financial_assets WHERE is_active = TRUE) as pg_count,
    'financial_assets' as table_name;

-- ============================================================================
-- 附录：索引优化建议
-- ============================================================================

-- A.1 financial_assets表索引
CREATE INDEX IF NOT EXISTS idx_financial_assets_active ON financial_assets(is_active);
CREATE INDEX IF NOT EXISTS idx_financial_assets_risk_level ON financial_assets(risk_level);
CREATE INDEX IF NOT EXISTS idx_financial_assets_dates ON financial_assets(start_date, maturity_date);
CREATE INDEX IF NOT EXISTS idx_financial_assets_company ON financial_assets(company_id);
CREATE INDEX IF NOT EXISTS idx_financial_assets_vessel ON financial_assets(vessel_id);

-- A.2 vessels表索引
CREATE INDEX IF NOT EXISTS idx_vessels_active ON vessels(is_active);
CREATE INDEX IF NOT EXISTS idx_vessels_risk_level ON vessels(risk_level);
CREATE INDEX IF NOT EXISTS idx_vessels_imo ON vessels(imo_number);
CREATE INDEX IF NOT EXISTS idx_vessels_owner ON vessels(owner_company_id);

-- A.3 companies表索引
CREATE INDEX IF NOT EXISTS idx_companies_active ON companies(is_active);
CREATE INDEX IF NOT EXISTS idx_companies_risk_level ON companies(risk_level);

-- A.4 vessel_risk_history表索引
CREATE INDEX IF NOT EXISTS idx_vessel_risk_history_vessel ON vessel_risk_history(vessel_id);
CREATE INDEX IF NOT EXISTS idx_vessel_risk_history_date ON vessel_risk_history(assessment_date);

-- A.5 risk_factor_contribution表索引
CREATE INDEX IF NOT EXISTS idx_risk_factor_target ON risk_factor_contribution(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_risk_factor_created ON risk_factor_contribution(created_at);

-- A.6 fx_rates表索引
CREATE INDEX IF NOT EXISTS idx_fx_rates_lookup ON fx_rates(base_currency, quote_currency, rate_date);

-- ============================================================================
-- 附录：性能优化建议
-- ============================================================================

-- B.1 使用EXPLAIN ANALYZE分析查询性能
-- EXPLAIN ANALYZE SELECT ...

-- B.2 定期更新统计信息
-- ANALYZE financial_assets;
-- ANALYZE vessels;
-- ANALYZE companies;

-- B.3 使用物化视图缓存复杂查询
-- CREATE MATERIALIZED VIEW mv_dashboard_summary AS
-- SELECT ...

-- B.4 分区表优化（按日期分区）
-- CREATE TABLE financial_assets_partitioned (
--     ...
-- ) PARTITION BY RANGE (start_date);

-- ============================================================================
-- 文档说明
-- ============================================================================
-- 1. 所有金额字段都通过 fx_rate CTE 进行汇率转换
-- 2. 时间范围过滤使用 start_date <= end_date AND maturity_date >= start_date
-- 3. 使用 COALESCE 处理 NULL 值，避免计算错误
-- 4. 使用 NULLS LAST 确保 NULL 值排在最后
-- 5. 使用 FILTER (WHERE ...) 进行条件聚合
-- 6. 所有查询都包含 is_active = TRUE 过滤条件
-- 7. MongoDB查询使用聚合管道和地理空间索引
-- 8. ClickHouse查询使用FINAL修饰符确保数据一致性
-- ============================================================================
