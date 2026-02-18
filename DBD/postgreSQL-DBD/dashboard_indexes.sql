-- 建议索引（提升仪表盘查询性能）
SET search_path TO silvernav;

-- 汇率最新值查询
CREATE INDEX IF NOT EXISTS idx_fx_rates_quote_base_date
ON fx_rates (quote_currency, base_currency, rate_date DESC);

-- 金融资产过滤与聚合
CREATE INDEX IF NOT EXISTS idx_financial_assets_active_dates
ON financial_assets (is_active, start_date, maturity_date);

CREATE INDEX IF NOT EXISTS idx_financial_assets_risk
ON financial_assets (risk_level);

CREATE INDEX IF NOT EXISTS idx_financial_assets_currency
ON financial_assets (currency);

CREATE INDEX IF NOT EXISTS idx_financial_assets_company
ON financial_assets (company_id);

-- 还款计划
CREATE INDEX IF NOT EXISTS idx_repayment_due_status
ON asset_repayment_schedule (due_date, payment_status);

CREATE INDEX IF NOT EXISTS idx_repayment_asset
ON asset_repayment_schedule (asset_id);

-- 船舶风险历史（最新记录）
CREATE INDEX IF NOT EXISTS idx_vessel_risk_history_vessel_date
ON vessel_risk_history (vessel_id, assessment_date DESC);

-- 授信评估最新记录
CREATE INDEX IF NOT EXISTS idx_credit_assessment_company_date
ON credit_risk_assessment (company_id, assessment_date DESC);

-- 企业/船舶风险等级
CREATE INDEX IF NOT EXISTS idx_companies_risk_active
ON companies (risk_level, is_active);

CREATE INDEX IF NOT EXISTS idx_vessels_risk_active
ON vessels (risk_level, is_active);
