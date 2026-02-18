-- 优先建这个（覆盖过滤 + 常用输出列）
CREATE INDEX idx_fin_assets_active_dates_risk_amount
ON financial_assets (is_active, maturity_date, start_date)
INCLUDE (risk_level, outstanding_amount, currency, id)
WHERE is_active = TRUE;  -- 部分索引，只存活跃资产，节省空间

-- 如果 risk_level 过滤频繁（如 high），再加一个
CREATE INDEX idx_fin_assets_active_risk
ON financial_assets (is_active, risk_level)
INCLUDE (outstanding_amount, currency, start_date, maturity_date)
WHERE is_active = TRUE;

-- 核心索引：支持 WHERE due_date < :base_date AND payment_status <> 'paid' + 计算 remaining
CREATE INDEX idx_repayment_overdue_core
ON asset_repayment_schedule (due_date, payment_status)
INCLUDE (asset_id, due_principal, due_interest, paid_principal, paid_interest)
WHERE payment_status <> 'paid';  -- 部分索引，只存未付记录，大幅节省空间

-- 如果 JOIN asset_id 频繁，再加一个（可选，但推荐）
CREATE INDEX idx_repayment_asset_due
ON asset_repayment_schedule (asset_id, due_date)
INCLUDE (payment_status, due_principal, due_interest, paid_principal, paid_interest);

-- 支持 JOIN s.asset_id = a.id + 过滤 is_active
CREATE INDEX idx_fin_assets_id_active
ON financial_assets (id)
INCLUDE (currency, is_active)
WHERE is_active = TRUE;  -- 部分索引

-- 如果你后续还经常过滤 is_active + 其他条件，可复用之前建议的
CREATE INDEX idx_fin_assets_active_currency
ON financial_assets (is_active, currency)
INCLUDE (id, outstanding_amount);