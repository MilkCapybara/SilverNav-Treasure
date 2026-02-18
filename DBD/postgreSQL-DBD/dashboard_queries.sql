-- 银航宝·仪表盘核心查询 SQL（CNY 默认不换算，非 CNY 才换算）
-- 参数说明：:base_date / :start_date / :end_date / :target_currency
SET search_path TO silvernav;

-- fx_rate: CNY 则为 1，否则取 CNY->目标币种最新汇率
-- 可在每个查询内复用：amount * (SELECT rate FROM fx_rate)

-- 1. 总体风险敞口（总敞口 + 高风险敞口）
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

-- 1.1 风险敞口分布（low/medium/high）
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

-- 2. 高风险预警（企业/船舶/资产 Top + 即将逾期）
SELECT COUNT(*) AS high_risk_company_count
FROM companies
WHERE is_active = TRUE AND risk_level = 'high';

SELECT COUNT(*) AS high_risk_vessel_count
FROM vessels
WHERE is_active = TRUE AND risk_level = 'high';

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


-- 整改
-- WITH fx_rate AS (
--     SELECT CASE
--         WHEN :target_currency = 'CNY' THEN 1
--         ELSE COALESCE((
--             SELECT rate FROM fx_rates
--             WHERE base_currency = 'CNY'
--               AND quote_currency = :target_currency
--               AND rate_date <= :end_date
--             ORDER BY rate_date DESC
--             LIMIT 1
--         ), 1)
--     END AS rate
-- ), schedule_base AS (
--     SELECT
--         due_date,
--         payment_status,
--         (COALESCE(due_principal,0) + COALESCE(due_interest,0)
--          - COALESCE(paid_principal,0) - COALESCE(paid_interest,0))
--          * (SELECT rate FROM fx_rate) AS remaining_converted
--     FROM asset_repayment_schedule
-- )
-- SELECT
--     COALESCE(SUM(CASE WHEN due_date < :base_date AND payment_status <> 'paid'
--         THEN remaining_converted ELSE 0 END), 0) AS overdue_amount,
--     COUNT(*) FILTER (WHERE due_date < :base_date AND payment_status <> 'paid') AS overdue_count,
--     COALESCE(SUM(CASE WHEN due_date BETWEEN :base_date AND (:base_date + INTERVAL '7 day')
--         AND payment_status <> 'paid' THEN remaining_converted ELSE 0 END), 0) AS due_soon_amount,
--     COUNT(*) FILTER (WHERE due_date BETWEEN :base_date AND (:base_date + INTERVAL '7 day')
--         AND payment_status <> 'paid') AS due_soon_count
-- FROM schedule_base;

-- 3. 不良/逾期资产监控（NPL率 + 逾期分层）
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

-- 整改
-- WITH fx_rate AS (
--     SELECT CASE
--         WHEN :target_currency = 'CNY' THEN 1
--         ELSE COALESCE((
--             SELECT rate FROM fx_rates
--             WHERE base_currency = 'CNY'
--               AND quote_currency = :target_currency
--               AND rate_date <= :end_date
--             ORDER BY rate_date DESC
--             LIMIT 1
--         ), 1)
--     END AS rate
-- ), schedule_base AS (
--     SELECT
--         due_date,
--         (COALESCE(due_principal,0) + COALESCE(due_interest,0)
--          - COALESCE(paid_principal,0) - COALESCE(paid_interest,0))
--          * (SELECT rate FROM fx_rate) AS remaining_converted
--     FROM asset_repayment_schedule
--     WHERE due_date < :base_date AND payment_status <> 'paid'
-- )
-- SELECT
--     COALESCE(SUM(CASE WHEN days_overdue BETWEEN 1 AND 30 THEN remaining_converted ELSE 0 END), 0) AS overdue_1_30,
--     COALESCE(SUM(CASE WHEN days_overdue BETWEEN 31 AND 90 THEN remaining_converted ELSE 0 END), 0) AS overdue_31_90,
--     COALESCE(SUM(CASE WHEN days_overdue > 90 THEN remaining_converted ELSE 0 END), 0) AS overdue_90_plus
-- FROM (
--     SELECT
--         (:base_date::date - due_date)::int AS days_overdue,
--         remaining_converted
--     FROM schedule_base
-- ) t;

-- 4. 风险等级分布（企业/船舶）
SELECT risk_level, COUNT(*) AS count
FROM companies
WHERE is_active = TRUE
GROUP BY risk_level
ORDER BY risk_level;

SELECT risk_level, COUNT(*) AS count
FROM vessels
WHERE is_active = TRUE
GROUP BY risk_level
ORDER BY risk_level;

-- 5. 风险趋势与变化（平均风险评分 + 高风险敞口走势）
SELECT assessment_date AS date, AVG(risk_score) AS avg_risk_score
FROM vessel_risk_history
WHERE assessment_date BETWEEN :start_date AND :end_date
GROUP BY assessment_date
ORDER BY assessment_date;

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

-- 6. 授信使用与剩余额度概览 整改
-- WITH fx_rate AS (
--     SELECT CASE
--         WHEN :target_currency = 'CNY' THEN 1
--         ELSE COALESCE((
--             SELECT rate FROM fx_rates
--             WHERE base_currency = 'CNY'
--               AND quote_currency = :target_currency
--               AND rate_date <= :end_date
--             ORDER BY rate_date DESC
--             LIMIT 1
--         ), 1)
--     END AS rate
-- ), latest AS (
--     SELECT DISTINCT ON (company_id)
--         company_id, suggested_credit_max, assessment_date
--     FROM credit_risk_assessment
--     ORDER BY company_id, assessment_date DESC
-- ), usage AS (
--     SELECT company_id, SUM(outstanding_amount * (SELECT rate FROM fx_rate)) AS used_amount
--     FROM financial_assets
--     WHERE is_active = TRUE
--     GROUP BY company_id
-- ), joined AS (
--     SELECT l.company_id,
--            COALESCE(l.suggested_credit_max, 0) * (SELECT rate FROM fx_rate) AS suggested_credit_max,
--            COALESCE(u.used_amount, 0) AS used_amount
--     FROM latest l
--     LEFT JOIN usage u ON u.company_id = l.company_id
-- )
-- SELECT
--     COALESCE(SUM(used_amount), 0) AS used_total,
--     COALESCE(SUM(suggested_credit_max), 0) AS limit_total
-- FROM joined;

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

-- 7. 资产质量与还款健康
-- WITH fx_rate AS (
--     SELECT CASE
--         WHEN :target_currency = 'CNY' THEN 1
--         ELSE COALESCE((
--             SELECT rate FROM fx_rates
--             WHERE base_currency = 'CNY'
--               AND quote_currency = :target_currency
--               AND rate_date <= :end_date
--             ORDER BY rate_date DESC
--             LIMIT 1
--         ), 1)
--     END AS rate
-- ), schedule_base AS (
--     SELECT
--         due_date,
--         (COALESCE(due_principal + due_interest, 0)) * (SELECT rate FROM fx_rate) AS due_converted,
--         (COALESCE(paid_principal + paid_interest, 0)) * (SELECT rate FROM fx_rate) AS paid_converted
--     FROM asset_repayment_schedule
-- )
-- SELECT
--     COALESCE(SUM(due_converted), 0) AS due_total,
--     COALESCE(SUM(paid_converted), 0) AS paid_total
-- FROM schedule_base
-- WHERE due_date BETWEEN :start_date AND :end_date;

-- 8. 船舶资产风险Top榜 整改
-- WITH latest_vessel_risk AS (
--     SELECT DISTINCT ON (vessel_id)
--         vessel_id, risk_score, risk_level, assessment_date
--     FROM vessel_risk_history
--     ORDER BY vessel_id, assessment_date DESC
-- )
-- SELECT
--     v.vessel_name,
--     v.imo_number,
--     c.company_name,
--     COALESCE(h.risk_score, v.asset_risk_score) AS risk_score,
--     COALESCE(h.risk_level, v.risk_level) AS risk_level,
--     h.assessment_date
-- FROM vessels v
-- LEFT JOIN companies c ON c.id = v.owner_company_id
-- LEFT JOIN latest_vessel_risk h ON h.vessel_id = v.id
-- WHERE v.is_active = TRUE
-- ORDER BY COALESCE(h.risk_score, v.asset_risk_score) DESC NULLS LAST
-- LIMIT 10;

-- 9. 风险因子Top贡献 整改
-- SELECT factor_name,
--        AVG(factor_value) AS avg_value,
--        SUM(contribution) AS total_contribution
-- FROM risk_factor_contribution
-- WHERE created_at::date BETWEEN :start_date AND :end_date
-- GROUP BY factor_name
-- ORDER BY ABS(SUM(contribution)) DESC NULLS LAST
-- LIMIT 5;

-- 10. 汇率波动监控 + 外币敞口折算
SELECT rate_date, base_currency, quote_currency, rate
FROM fx_rates
WHERE quote_currency = :target_currency
  AND base_currency IN ('USD', 'EUR')
  AND rate_date BETWEEN (:base_date - INTERVAL '30 day') AND :base_date
ORDER BY rate_date;

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
