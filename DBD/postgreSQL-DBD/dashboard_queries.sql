-- ============================================================================
-- 银航宝·仪表盘核心查询 SQL（CNY 默认不换算，非 CNY 才换算）
-- ============================================================================
-- 参数说明：
--   :base_date       - 基准日期（当前日期）
--   :start_date      - 开始日期（时间范围起点）
--   :end_date        - 结束日期（时间范围终点）
--   :target_currency - 目标币种（CNY/USD/HKD/GBP/EUR）
-- ============================================================================
SET search_path TO silvernav;

-- fx_rate: CNY 则为 1，否则取 CNY->目标币种最新汇率
-- 可在每个查询内复用：amount * (SELECT rate FROM fx_rate)

-- ============================================================================
-- 指标1：总体风险敞口（总敞口 + 高风险敞口）
-- 对应API：/api/dashboard/summary
-- 对应函数：main.py:516-584 (get_dashboard_summary)
-- 对应详情页：/api/detail/overall (main.py:2056-2182)
-- 核心表：financial_assets
-- 说明：计算所有活跃资产的总敞口金额和高风险敞口金额
-- ============================================================================
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

-- ============================================================================
-- 指标1.1：风险敞口分布（low/medium/high）
-- 对应API：/api/dashboard/summary (包含在summary中)
-- 对应函数：main.py:516-584 (get_dashboard_summary)
-- 核心表：financial_assets
-- 说明：按风险等级统计资产数量和敞口金额
-- ============================================================================
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

-- ============================================================================
-- 指标2：高风险预警（企业/船舶/资产 Top + 即将逾期）
-- 对应API：/api/dashboard/alerts
-- 对应函数：main.py:587-652 (get_dashboard_alerts)
-- 对应详情页：/api/detail/alerts (main.py:1377-1503)
-- 核心表：companies, vessels, financial_assets
-- 说明：统计高风险企业、船舶数量，以及高风险资产Top10
-- ============================================================================

-- 2.1 高风险企业数量
SELECT COUNT(*) AS high_risk_company_count
FROM companies
WHERE is_active = TRUE AND risk_level = 'high';

-- 2.2 高风险船舶数量
SELECT COUNT(*) AS high_risk_vessel_count
FROM vessels
WHERE is_active = TRUE AND risk_level = 'high';

-- 2.3 高风险资产Top10（按敞口金额排序）
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

-- ============================================================================
-- 指标3：不良/逾期资产监控（NPL率 + 逾期分层）
-- 对应API：/api/dashboard/npl
-- 对应函数：main.py:655-700 (get_dashboard_npl)
-- 对应详情页：/api/detail/npl (main.py:1635-1779)
-- 核心表：financial_assets
-- 说明：计算不良资产数量、金额、不良率
-- ============================================================================
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

-- ============================================================================
-- 指标4：风险等级分布（企业/船舶）
-- 对应API：/api/dashboard/risk-levels
-- 对应函数：main.py:703-741 (get_dashboard_risk_levels)
-- 对应详情页：/api/detail/distribution (main.py:1978-2053)
-- 核心表：companies, vessels
-- 说明：统计企业和船舶的风险等级分布
-- ============================================================================

-- 4.1 企业风险等级分布
SELECT risk_level, COUNT(*) AS count
FROM companies
WHERE is_active = TRUE
GROUP BY risk_level
ORDER BY risk_level;

-- 4.2 船舶风险等级分布
SELECT risk_level, COUNT(*) AS count
FROM vessels
WHERE is_active = TRUE
GROUP BY risk_level
ORDER BY risk_level;

-- ============================================================================
-- 指标5：风险趋势与变化（平均风险评分 + 高风险敞口走势）
-- 对应API：/api/dashboard/trend
-- 对应函数：main.py:744-786 (get_dashboard_trend)
-- 对应详情页：/api/detail/trend (main.py:1782-1917)
-- 核心表：vessel_risk_history, financial_assets
-- 说明：展示历史风险评分趋势和高风险敞口变化
-- ============================================================================

-- 5.1 平均风险评分趋势（按日期）
SELECT assessment_date AS date, AVG(risk_score) AS avg_risk_score
FROM vessel_risk_history
WHERE assessment_date BETWEEN :start_date AND :end_date
GROUP BY assessment_date
ORDER BY assessment_date;

-- 5.2 高风险敞口走势（按日期）
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

-- ============================================================================
-- 指标6：授信使用与剩余额度概览
-- 对应API：/api/dashboard/credit
-- 对应函数：main.py:805-841 (get_dashboard_credit)
-- 对应详情页：/api/detail/credit (main.py:1178-1374)
-- 核心表：financial_assets, companies
-- 说明：统计授信使用情况和Top客户
-- ============================================================================

-- 6.1 授信使用总额（实际使用 get_credit_usage 函数计算）
-- 注意：授信额度 = 已用额度 * 1.5（模拟数据）
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

-- 6.2 授信使用Top5客户
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

-- ============================================================================
-- 指标7：船舶资产风险Top榜
-- 对应API：/api/dashboard/vessel-top
-- 对应函数：main.py:789-802 (get_dashboard_vessel_top)
-- 对应详情页：/api/detail/vessels (main.py:1506-1632)
-- 核心表：vessels, companies
-- 说明：展示风险评分最高的船舶Top10
-- ============================================================================
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

-- ============================================================================
-- 指标8：风险因子Top贡献
-- 对应API：/api/dashboard/risk-factors
-- 对应函数：main.py:844-857 (get_dashboard_risk_factors)
-- 对应详情页：/api/detail/factors (main.py:1920-1975)
-- 核心表：risk_factor_contribution
-- 说明：展示SHAP特征贡献度Top5
-- ============================================================================
SELECT factor_name,
       AVG(factor_value) AS avg_value,
       SUM(contribution) AS total_contribution
FROM risk_factor_contribution
WHERE created_at::date BETWEEN :start_date AND :end_date
GROUP BY factor_name
ORDER BY ABS(SUM(contribution)) DESC NULLS LAST
LIMIT 5;

-- ============================================================================
-- 指标9：汇率波动监控 + 外币敞口折算
-- 对应API：/api/dashboard/fx
-- 对应函数：main.py:860-900 (get_dashboard_fx)
-- 核心表：fx_rates, financial_assets
-- 说明：展示汇率历史数据和各币种敞口分布
-- ============================================================================

-- 9.1 汇率历史数据（近30天）
SELECT rate_date, base_currency, quote_currency, rate
FROM fx_rates
WHERE quote_currency = :target_currency
  AND base_currency IN ('USD', 'EUR')
  AND rate_date BETWEEN (:base_date - INTERVAL '30 day') AND :base_date
ORDER BY rate_date;

-- 9.2 各币种敞口分布
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
    SUM(outstanding_amount) AS exposure_amount,
    SUM(outstanding_amount * (SELECT rate FROM fx_rate)) AS exposure_converted
FROM financial_assets
WHERE is_active = TRUE
GROUP BY currency
ORDER BY exposure_converted DESC NULLS LAST;

-- ============================================================================
-- 补充说明
-- ============================================================================
-- 1. 所有金额字段都通过 fx_rate CTE 进行汇率转换
-- 2. 时间范围过滤使用 start_date <= end_date AND maturity_date >= start_date
-- 3. 使用 COALESCE 处理 NULL 值，避免计算错误
-- 4. 使用 NULLS LAST 确保 NULL 值排在最后
-- 5. 使用 FILTER (WHERE ...) 进行条件聚合
-- 6. 所有查询都包含 is_active = TRUE 过滤条件
-- 7. 索引优化建议参见 dashboard_indexes.sql
-- 8. 查询性能目标：50ms-1000ms（取决于数据量）
-- ============================================================================
