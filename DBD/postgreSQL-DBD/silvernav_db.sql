-- =========================
-- Schema 定义
-- =========================
CREATE SCHEMA IF NOT EXISTS silvernav;
SET search_path TO silvernav;

COMMENT ON SCHEMA silvernav IS '银航宝业务核心 Schema，存放航运金融风险相关结构化数据';

-- =========================
-- 用户表
-- =========================
CREATE TABLE users (
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

COMMENT ON TABLE users IS '系统用户表，存储平台登录账号、状态及基础安全信息';

COMMENT ON COLUMN users.id IS '系统内部唯一用户ID，作为所有用户关联的主键';
COMMENT ON COLUMN users.account IS '登录账号（邮箱/工号/自定义账号），全局唯一';
COMMENT ON COLUMN users.username IS '页面展示用户名，可由用户自行修改';
COMMENT ON COLUMN users.password_hash IS '密码哈希值（bcrypt / argon2 等算法结果，不可逆）';
COMMENT ON COLUMN users.status IS '账号状态：active正常、disabled禁用、pending待激活、locked风险锁定';
COMMENT ON COLUMN users.account_type IS '账号类型：local本地账号 / oauth第三方 / enterprise企业单点登录';
COMMENT ON COLUMN users.failed_login_count IS '连续登录失败次数，用于风控与账号锁定策略';
COMMENT ON COLUMN users.locked_until IS '账号锁定截止时间，超过该时间可自动解锁';
COMMENT ON COLUMN users.last_login_at IS '最近一次成功登录时间';
COMMENT ON COLUMN users.is_deleted IS '软删除标志，金融系统禁止物理删除';
COMMENT ON COLUMN users.created_at IS '账号创建时间';
COMMENT ON COLUMN users.updated_at IS '账号信息最近更新时间';

-- 索引
CREATE INDEX idx_users_account ON users(account);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_locked_until ON users(locked_until);
CREATE INDEX idx_users_is_deleted ON users(is_deleted);

-- 更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

-- =========================
-- 企业表
-- =========================
CREATE TABLE companies (
    id BIGSERIAL PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    registration_country VARCHAR(50),
    company_type VARCHAR(50),
    credit_score NUMERIC(5,2),
    risk_level VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE companies IS '航运企业/客户主数据表，作为授信与风险评估主体';

COMMENT ON COLUMN companies.id IS '企业唯一ID';
COMMENT ON COLUMN companies.company_name IS '企业名称';
COMMENT ON COLUMN companies.registration_country IS '企业注册国家或地区';
COMMENT ON COLUMN companies.company_type IS '企业类型：船东/运营商/租船人等';
COMMENT ON COLUMN companies.credit_score IS '企业整体信用评分（模拟值）';
COMMENT ON COLUMN companies.risk_level IS '企业当前风险等级（low/medium/high）';
COMMENT ON COLUMN companies.is_active IS '企业是否仍为有效合作主体';
COMMENT ON COLUMN companies.created_at IS '企业记录创建时间';

-- =========================
-- 船舶资产表
-- =========================
CREATE TABLE vessels (
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

COMMENT ON TABLE vessels IS '船舶资产表，航运金融中的核心抵押/风险评估对象';

COMMENT ON COLUMN vessels.id IS '船舶唯一ID';
COMMENT ON COLUMN vessels.imo_number IS '船舶IMO编号，国际唯一标识';
COMMENT ON COLUMN vessels.vessel_name IS '船舶名称';
COMMENT ON COLUMN vessels.vessel_type IS '船舶类型（散货船/油轮/集装箱船等）';
COMMENT ON COLUMN vessels.build_year IS '船舶建造年份';
COMMENT ON COLUMN vessels.flag_country IS '船旗国';
COMMENT ON COLUMN vessels.owner_company_id IS '船舶所属企业ID（外键关联企业表）';
COMMENT ON COLUMN vessels.asset_risk_score IS '船舶作为金融资产的风险评分';
COMMENT ON COLUMN vessels.risk_level IS '船舶当前风险等级';
COMMENT ON COLUMN vessels.is_active IS '船舶是否仍为有效金融资产';
COMMENT ON COLUMN vessels.created_at IS '船舶资产记录创建时间';

-- =========================
-- 船舶风险历史评估表
-- =========================
CREATE TABLE vessel_risk_history (
    id BIGSERIAL PRIMARY KEY,
    vessel_id BIGINT REFERENCES vessels(id),
    assessment_date DATE NOT NULL,
    risk_score NUMERIC(5, 2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE vessel_risk_history IS '船舶风险历史评估表，用于风险趋势分析';

COMMENT ON COLUMN vessel_risk_history.id IS '风险评估记录ID';
COMMENT ON COLUMN vessel_risk_history.vessel_id IS '对应船舶ID';
COMMENT ON COLUMN vessel_risk_history.assessment_date IS '风险评估日期';
COMMENT ON COLUMN vessel_risk_history.risk_score IS '评估得到的风险评分';
COMMENT ON COLUMN vessel_risk_history.risk_level IS '评估得到的风险等级';
COMMENT ON COLUMN vessel_risk_history.created_at IS '风险评估记录生成时间';

-- =========================
-- 风险因素贡献表
-- =========================
CREATE TABLE risk_factor_contribution (
    id BIGSERIAL PRIMARY KEY,
    target_type VARCHAR(20),
    target_id BIGINT,
    factor_name VARCHAR(100),
    factor_value NUMERIC(10,4),
    contribution NUMERIC(10,4),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE risk_factor_contribution IS '风险因子贡献表，用于模型可解释性分析（如SHAP）';

COMMENT ON COLUMN risk_factor_contribution.id IS '风险因子记录ID';
COMMENT ON COLUMN risk_factor_contribution.target_type IS '风险评估对象类型（company/vessel）';
COMMENT ON COLUMN risk_factor_contribution.target_id IS '风险评估对象ID';
COMMENT ON COLUMN risk_factor_contribution.factor_name IS '风险因子名称';
COMMENT ON COLUMN risk_factor_contribution.factor_value IS '风险因子原始取值';
COMMENT ON COLUMN risk_factor_contribution.contribution IS '该因子对风险评分的贡献值';
COMMENT ON COLUMN risk_factor_contribution.model_version IS '生成该解释结果的模型版本';
COMMENT ON COLUMN risk_factor_contribution.created_at IS '风险因子解释生成时间';

-- =========================
-- 金融风险指标快照表
-- =========================
CREATE TABLE financial_risk_snapshot (
    id BIGSERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    snapshot_type VARCHAR(20) DEFAULT 'daily',
    high_risk_exposure NUMERIC(18,2),
    high_risk_company_count INT,
    high_risk_vessel_count INT,
    currency VARCHAR(10) DEFAULT 'CNY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE financial_risk_snapshot IS '金融风险指标快照表，用于Dashboard展示';

COMMENT ON COLUMN financial_risk_snapshot.id IS '快照记录ID';
COMMENT ON COLUMN financial_risk_snapshot.snapshot_date IS '风险指标统计日期';
COMMENT ON COLUMN financial_risk_snapshot.snapshot_type IS '快照类型（日/周/月）';
COMMENT ON COLUMN financial_risk_snapshot.high_risk_exposure IS '高风险敞口金额（基准币种）';
COMMENT ON COLUMN financial_risk_snapshot.high_risk_company_count IS '高风险企业数量';
COMMENT ON COLUMN financial_risk_snapshot.high_risk_vessel_count IS '高风险船舶数量';
COMMENT ON COLUMN financial_risk_snapshot.currency IS '金额基准币种';
COMMENT ON COLUMN financial_risk_snapshot.created_at IS '快照生成时间';

-- =========================
-- 客户授信风险评估表
-- =========================
CREATE TABLE credit_risk_assessment (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id),
    credit_score NUMERIC(5,2),
    asset_quality_score NUMERIC(5,2),
    suggested_credit_min NUMERIC(18,2),
    suggested_credit_max NUMERIC(18,2),
    assessment_date DATE,
    assessment_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE credit_risk_assessment IS '客户授信风险评估结果表';

COMMENT ON COLUMN credit_risk_assessment.id IS '授信评估记录ID';
COMMENT ON COLUMN credit_risk_assessment.company_id IS '被评估企业ID';
COMMENT ON COLUMN credit_risk_assessment.credit_score IS '企业信用评分';
COMMENT ON COLUMN credit_risk_assessment.asset_quality_score IS '航运资产质量评分';
COMMENT ON COLUMN credit_risk_assessment.suggested_credit_min IS '建议最低授信额度';
COMMENT ON COLUMN credit_risk_assessment.suggested_credit_max IS '建议最高授信额度';
COMMENT ON COLUMN credit_risk_assessment.assessment_date IS '授信评估日期';
COMMENT ON COLUMN credit_risk_assessment.assessment_version IS '评估模型或规则版本';
COMMENT ON COLUMN credit_risk_assessment.created_at IS '授信评估记录创建时间';

-- =========================
-- 外汇汇率表
-- =========================
CREATE TABLE fx_rates (
    id BIGSERIAL PRIMARY KEY,
    base_currency VARCHAR(10) NOT NULL,
    quote_currency VARCHAR(10) NOT NULL,
    rate NUMERIC(12,6) NOT NULL,
    rate_date DATE NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (base_currency, quote_currency, rate_date)
);

COMMENT ON TABLE fx_rates IS '外汇汇率表，用于多币种风险敞口换算';

COMMENT ON COLUMN fx_rates.id IS '汇率记录ID';
COMMENT ON COLUMN fx_rates.base_currency IS '基准币种（如CNY）';
COMMENT ON COLUMN fx_rates.quote_currency IS '目标币种（如USD）';
COMMENT ON COLUMN fx_rates.rate IS '汇率值（高精度）';
COMMENT ON COLUMN fx_rates.rate_date IS '汇率对应日期';
COMMENT ON COLUMN fx_rates.source IS '汇率来源（模拟/手动/第三方）';
COMMENT ON COLUMN fx_rates.created_at IS '汇率记录创建时间';

-- =========================
-- 金融资产明细表
-- =========================
CREATE TABLE financial_assets (
    id BIGSERIAL PRIMARY KEY,
    -- 关联主体
    company_id BIGINT NOT NULL REFERENCES companies(id),
    vessel_id BIGINT REFERENCES vessels(id),
    -- 资产类型
    asset_type VARCHAR(50) NOT NULL, 
    -- loan / mortgage / leasing / guarantee / factoring
    contract_no VARCHAR(100) UNIQUE,
    -- 金额信息
    principal_amount NUMERIC(18,2) NOT NULL,          -- 初始本金
    outstanding_amount NUMERIC(18,2) NOT NULL,        -- 当前剩余本金
    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    interest_rate NUMERIC(8,4),                       -- 利率
    start_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    -- 风险相关
    risk_level VARCHAR(20) DEFAULT 'low',
    risk_score NUMERIC(5,2),
    is_non_performing BOOLEAN DEFAULT FALSE,          -- 是否不良
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE financial_assets IS '金融资产表，存储航运金融相关的各类资产信息';
COMMENT ON COLUMN financial_assets.company_id IS '关联企业ID，外键引用 companies 表';
COMMENT ON COLUMN financial_assets.vessel_id IS '关联船舶ID，外键引用 vessels 表，非必填';
COMMENT ON COLUMN financial_assets.asset_type IS '资产类型，如贷款、抵押、租赁、担保、保理等';
COMMENT ON COLUMN financial_assets.contract_no IS '合同编号，唯一标识一个金融资产';
COMMENT ON COLUMN financial_assets.principal_amount IS '金融资产的初始本金金额';
COMMENT ON COLUMN financial_assets.outstanding_amount IS '金融资产当前剩余本金金额';
COMMENT ON COLUMN financial_assets.currency IS '金额币种，默认为CNY';
COMMENT ON COLUMN financial_assets.interest_rate IS '金融资产的利率信息';
COMMENT ON COLUMN financial_assets.start_date IS '金融资产的起始日期';
COMMENT ON COLUMN financial_assets.maturity_date IS '金融资产的到期日期';
COMMENT ON COLUMN financial_assets.risk_level IS '金融资产的风险等级';
COMMENT ON COLUMN financial_assets.risk_score IS '金融资产的风险评分';
COMMENT ON COLUMN financial_assets.is_non_performing IS '标识该金融资产是否为不良资产';
COMMENT ON COLUMN financial_assets.is_active IS '标识该金融资产是否仍为有效资产';

-- =========================
-- 还款计划表
-- =========================
CREATE TABLE asset_repayment_schedule (
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT NOT NULL REFERENCES financial_assets(id),

    installment_no INT,
    due_date DATE NOT NULL,
    due_principal NUMERIC(18,2),
    due_interest NUMERIC(18,2),

    paid_principal NUMERIC(18,2) DEFAULT 0,
    paid_interest NUMERIC(18,2) DEFAULT 0,

    payment_status VARCHAR(20) DEFAULT 'pending',
    -- pending / partial / paid / overdue

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE asset_repayment_schedule IS '金融资产还款计划表，记录每笔金融资产的分期还款信息';
COMMENT ON COLUMN asset_repayment_schedule.asset_id IS '关联金融资产ID，外键引用 financial_assets 表';
COMMENT ON COLUMN asset_repayment_schedule.installment_no IS '分期编号，表示第几期还款';
COMMENT ON COLUMN asset_repayment_schedule.due_date IS '该期还款的到期日期';
COMMENT ON COLUMN asset_repayment_schedule.due_principal IS '该期应还本金金额';
COMMENT ON COLUMN asset_repayment_schedule.due_interest IS '该期应还利息金额';
COMMENT ON COLUMN asset_repayment_schedule.paid_principal IS '该期已还本金金额';
COMMENT ON COLUMN asset_repayment_schedule.paid_interest IS '该期已还利息金额';
COMMENT ON COLUMN asset_repayment_schedule.payment_status IS '该期还款状态，可能的值包括 pending（待还款）、partial（部分还款）、paid（已还清）和 overdue（逾期）';
