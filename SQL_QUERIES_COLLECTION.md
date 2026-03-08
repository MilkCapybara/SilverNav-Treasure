# 银航宝项目 SQL 查询语句汇总

本文档汇总了项目中所有的 SQL 查询语句，按文件和功能模块分类整理。

---

## 目录
1. [PostgreSQL 数据库表结构](#1-postgresql-数据库表结构)
2. [ClickHouse 数据库表结构](#2-clickhouse-数据库表结构)
3. [主应用 (main.py)](#3-主应用-mainpy)
4. [ClickHouse 客户端 (app/clickhouse_client.py)](#4-clickhouse-客户端-appclickhouse_clientpy)
5. [数据质量 API (app/quality_api.py)](#5-数据质量-api-appquality_apipy)
6. [船舶画像 API (app/profile_api.py)](#6-船舶画像-api-appprofile_apipy)
7. [Dashboard 查询 SQL](#7-dashboard-查询-sql)
8. [机器学习模型相关](#8-机器学习模型相关)
9. [数据生成脚本](#9-数据生成脚本)
10. [数据迁移脚本](#10-数据迁移脚本)

---

## 1. PostgreSQL 数据库表结构

### 文件: DBD/postgreSQL-DBD/silvernav_db.sql

#### 1.1 用户表 (users)
```sql
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
```

#### 1.2 企业表 (companies)
```sql
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
```

#### 1.3 船舶表 (vessels)
```sql
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
```

#### 1.4 船舶风险历史表 (vessel_risk_history)
```sql
CREATE TABLE vessel_risk_history (
    id BIGSERIAL PRIMARY KEY,
    vessel_id BIGINT REFERENCES vessels(id),
    assessment_date DATE NOT NULL,
    risk_score NUMERIC(5, 2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 1.5 风险因素贡献表 (risk_factor_contribution)
```sql
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
```

#### 1.6 金融资产表 (financial_assets)
```sql
CREATE TABLE financial_assets (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(id),
    vessel_id BIGINT REFERENCES vessels(id),
    asset_type VARCHAR(50) NOT NULL,
    contract_no VARCHAR(100) UNIQUE,
    principal_amount NUMERIC(18,2) NOT NULL,
    outstanding_amount NUMERIC(18,2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    interest_rate NUMERIC(8,4),
    start_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    risk_level VARCHAR(20) DEFAULT 'low',
    risk_score NUMERIC(5,2),
    is_non_performing BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 1.7 外汇汇率表 (fx_rates)
```sql
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
```

#### 1.8 还款计划表 (asset_repayment_schedule)
```sql
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. ClickHouse 数据库表结构

### 文件: clickhouse/create_tables.sql

#### 2.1 企业表 (companies)
```sql
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
```

#### 2.2 船舶表 (vessels)
```sql
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
```

#### 2.3 金融资产表 (financial_assets)
```sql
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
```

#### 2.4 物化视图 - 每日风险敞口汇总
```sql
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
```

---

## 3. 主应用 (main.py)

### 文件: main.py

#### 3.1 用户认证相关

##### 初始化 root 账户
```sql
SELECT id, password_hash FROM users WHERE account=%s
```

```sql
INSERT INTO users (account, username, password_hash, status, account_type)
VALUES (%s, %s, %s, 'active', 'local')
```

##### 用户登录
```sql
SELECT id, account, username, password_hash, status, failed_login_count,
       locked_until, is_deleted
FROM users WHERE account=%s
```

```sql
UPDATE users
SET failed_login_count=%s, locked_until=%s, updated_at=CURRENT_TIMESTAMP
WHERE account=%s
```

```sql
UPDATE users
SET failed_login_count=0, locked_until=NULL, last_login_at=CURRENT_TIMESTAMP,
    updated_at=CURRENT_TIMESTAMP
WHERE account=%s
```

##### 用户注册
```sql
SELECT id FROM users WHERE account=%s AND is_deleted=FALSE
```

```sql
INSERT INTO users (account, username, password_hash, status, account_type)
VALUES (%s, %s, %s, 'active', 'local')
```

#### 3.2 汇率查询
```sql
SELECT rate
FROM fx_rates
WHERE base_currency = 'CNY'
  AND quote_currency = %s
  AND rate_date <= %s
ORDER BY rate_date DESC
LIMIT 1
```

#### 3.3 授信使用情况
```sql
SELECT COALESCE(SUM(outstanding_amount), 0) as used_total
FROM financial_assets
WHERE is_active = TRUE
```

#### 3.4 资产统计
```sql
SELECT
    COUNT(*) as total_count,
    COALESCE(SUM(outstanding_amount), 0) as total_amount
FROM financial_assets
WHERE is_active = TRUE
```

#### 3.5 币种分布
```sql
SELECT
    currency,
    COUNT(*) as asset_count,
    COALESCE(SUM(outstanding_amount), 0) as amount
FROM financial_assets
WHERE is_active = TRUE
GROUP BY currency
ORDER BY amount DESC
```

#### 3.6 船舶风险 Top 榜
```sql
SELECT
    v.vessel_name,
    v.imo_number,
    c.company_name,
    v.asset_risk_score as risk_score,
    v.risk_level,
    CURRENT_DATE as assessment_date
FROM vessels v
LEFT JOIN companies c ON c.id = v.owner_company_id
WHERE v.is_active = TRUE
  AND v.asset_risk_score IS NOT NULL
ORDER BY v.asset_risk_score DESC
LIMIT 10
```

#### 3.7 风险因子贡献
```sql
SELECT
    factor_name,
    AVG(factor_value) as avg_value,
    SUM(contribution) as total_contribution
FROM risk_factor_contribution
WHERE created_at >= %s::date - INTERVAL '30 days'
  AND created_at <= %s::date
GROUP BY factor_name
ORDER BY SUM(ABS(contribution)) DESC
LIMIT 5
```

#### 3.8 Dashboard 总览查询

##### 总体风险敞口
```sql
WITH assets_base AS (
    SELECT
        a.risk_level,
        a.outstanding_amount * %s AS amount_converted
    FROM financial_assets a
    WHERE a.is_active = TRUE
      AND a.start_date <= %s
      AND a.maturity_date >= %s
)
SELECT
    COALESCE(SUM(amount_converted), 0) AS total_exposure,
    COALESCE(SUM(CASE WHEN risk_level='high' THEN amount_converted ELSE 0 END), 0)
        AS high_risk_exposure
FROM assets_base
```

##### 风险分布
```sql
WITH assets_base AS (
    SELECT
        a.risk_level,
        a.outstanding_amount * %s AS amount_converted
    FROM financial_assets a
    WHERE a.is_active = TRUE
      AND a.start_date <= %s
      AND a.maturity_date >= %s
)
SELECT
    risk_level,
    COUNT(*) AS asset_count,
    COALESCE(SUM(amount_converted), 0) AS exposure_amount
FROM assets_base
GROUP BY risk_level
ORDER BY risk_level
```

##### 高风险资产列表
```sql
SELECT
    a.id,
    a.contract_no,
    (a.outstanding_amount * %s) AS outstanding_amount,
    %s AS currency,
    a.risk_score,
    a.risk_level,
    c.company_name,
    v.vessel_name
FROM financial_assets a
LEFT JOIN companies c ON c.id = a.company_id
LEFT JOIN vessels v ON v.id = a.vessel_id
WHERE a.is_active = TRUE
  AND a.risk_level = 'high'
ORDER BY a.outstanding_amount DESC
LIMIT 10
```

##### 高风险企业/船舶数量
```sql
SELECT COUNT(*) AS count
FROM companies
WHERE is_active = TRUE AND risk_level = 'high'
```

```sql
SELECT COUNT(*) AS count
FROM vessels
WHERE is_active = TRUE AND risk_level = 'high'
```

#### 3.9 不良资产监控
```sql
WITH assets_base AS (
    SELECT
        a.is_non_performing,
        a.outstanding_amount * %s AS amount_converted
    FROM financial_assets a
    WHERE a.is_active = TRUE
      AND a.start_date <= %s
      AND a.maturity_date >= %s
)
SELECT
    COUNT(*) FILTER (WHERE is_non_performing) AS npl_count,
    COUNT(*) AS total_count,
    COALESCE(SUM(CASE WHEN is_non_performing THEN amount_converted ELSE 0 END), 0) AS npl_amount,
    COALESCE(SUM(amount_converted), 0) AS total_amount
FROM assets_base
```

#### 3.10 风险等级分布

##### 企业风险分布
```sql
SELECT risk_level, COUNT(*) AS count
FROM companies
WHERE is_active = TRUE
GROUP BY risk_level
ORDER BY risk_level
```

##### 船舶风险分布
```sql
SELECT risk_level, COUNT(*) AS count
FROM vessels
WHERE is_active = TRUE
GROUP BY risk_level
ORDER BY risk_level
```

#### 3.11 风险趋势

##### 平均风险评分趋势
```sql
SELECT assessment_date AS date, AVG(risk_score) AS avg_risk_score
FROM vessel_risk_history
WHERE assessment_date BETWEEN %s AND %s
GROUP BY assessment_date
ORDER BY assessment_date
```

##### 高风险敞口走势
```sql
SELECT
    start_date AS date,
    COALESCE(SUM(outstanding_amount * %s), 0) AS high_risk_exposure
FROM financial_assets
WHERE risk_level = 'high'
  AND start_date BETWEEN %s AND %s
GROUP BY start_date
ORDER BY start_date
```

#### 3.12 授信使用 Top 客户
```sql
SELECT c.company_name, u.used_amount
FROM (
    SELECT
        company_id,
        SUM(outstanding_amount * %s) AS used_amount
    FROM financial_assets
    WHERE is_active = TRUE
    GROUP BY company_id
    ORDER BY used_amount DESC
    LIMIT 5
) u
LEFT JOIN companies c ON c.id = u.company_id
```

#### 3.13 汇率历史数据
```sql
SELECT rate_date, base_currency, quote_currency, rate
FROM fx_rates
WHERE quote_currency = %s
  AND base_currency IN ('USD', 'EUR')
  AND rate_date BETWEEN %s AND %s
ORDER BY rate_date
```

#### 3.14 风险迁移矩阵（模拟数据）
```sql
SELECT 'high', 'medium', 30
UNION ALL SELECT 'high', 'low', 20
UNION ALL SELECT 'medium', 'high', 25
UNION ALL SELECT 'medium', 'medium', 100
UNION ALL SELECT 'medium', 'low', 75
UNION ALL SELECT 'low', 'high', 10
UNION ALL SELECT 'low', 'medium', 50
UNION ALL SELECT 'low', 'low', 500
```

#### 3.15 客户列表查询
```sql
SELECT DISTINCT
    c.id,
    c.company_name,
    c.registration_country,
    c.company_type,
    c.credit_score,
    c.risk_level
FROM companies c
WHERE c.is_active = TRUE
ORDER BY c.company_name
```

#### 3.16 授信集中度 Top10
```sql
SELECT COALESCE(SUM(total_exposure), 0) AS top10_exposure
FROM (
    SELECT
        company_id,
        SUM(outstanding_amount * %s) AS total_exposure
    FROM financial_assets
    WHERE is_active = TRUE
    GROUP BY company_id
    ORDER BY total_exposure DESC
    LIMIT 10
) top10
```

---

## 4. ClickHouse 客户端 (app/clickhouse_client.py)

### 文件: app/clickhouse_client.py

#### 4.1 连接测试
```sql
SELECT 1
```

#### 4.2 汇率查询
```sql
SELECT rate
FROM fx_rates FINAL
WHERE base_currency = 'CNY'
  AND quote_currency = {currency:String}
  AND rate_date <= {end_date:Date}
ORDER BY rate_date DESC
LIMIT 1
```

#### 4.3 风险敞口查询
```sql
SELECT
    risk_level,
    count() AS asset_count,
    sum(outstanding_amount * {fx_rate:Float64}) AS exposure_amount
FROM financial_assets FINAL
WHERE is_active = 1
  AND start_date <= {end_date:Date}
  AND maturity_date >= {start_date:Date}
GROUP BY risk_level
```

#### 4.4 高风险统计
```sql
SELECT count() FROM companies FINAL
WHERE is_active = 1 AND risk_level = 'high'
```

```sql
SELECT count() FROM vessels FINAL
WHERE is_active = 1 AND risk_level = 'high'
```

#### 4.5 高风险资产 Top10
```sql
SELECT
    a.contract_no,
    c.company_name,
    v.vessel_name,
    a.outstanding_amount * {fx_rate:Float64} AS outstanding_amount,
    a.risk_score
FROM (SELECT * FROM financial_assets FINAL) AS a
LEFT JOIN (SELECT * FROM companies FINAL) AS c ON c.id = a.company_id
LEFT JOIN (SELECT * FROM vessels FINAL) AS v ON v.id = a.vessel_id
WHERE a.is_active = 1 AND a.risk_level = 'high'
ORDER BY a.outstanding_amount DESC
LIMIT 10
```

#### 4.6 不良资产统计
```sql
SELECT
    countIf(is_non_performing = 1) AS npl_count,
    count() AS total_count,
    sumIf(outstanding_amount * {fx_rate:Float64}, is_non_performing = 1) AS npl_amount,
    sum(outstanding_amount * {fx_rate:Float64}) AS total_amount
FROM financial_assets FINAL
WHERE is_active = 1
  AND start_date <= {end_date:Date}
  AND maturity_date >= {start_date:Date}
```

#### 4.7 风险等级分布
```sql
SELECT risk_level, count() AS count
FROM companies FINAL
WHERE is_active = 1
GROUP BY risk_level
ORDER BY risk_level
```

```sql
SELECT risk_level, count() AS count
FROM vessels FINAL
WHERE is_active = 1
GROUP BY risk_level
ORDER BY risk_level
```

#### 4.8 风险趋势
```sql
SELECT assessment_date, avg(risk_score) AS avg_risk_score
FROM vessel_risk_history
WHERE assessment_date BETWEEN {start_date:Date} AND {end_date:Date}
GROUP BY assessment_date
ORDER BY assessment_date
```

```sql
SELECT
    start_date AS date,
    sum(outstanding_amount * {fx_rate:Float64}) AS high_risk_exposure
FROM financial_assets FINAL
WHERE risk_level = 'high'
  AND start_date BETWEEN {start_date:Date} AND {end_date:Date}
GROUP BY start_date
ORDER BY start_date
```

#### 4.9 船舶风险 Top10
```sql
SELECT
    v.vessel_name,
    v.imo_number,
    c.company_name,
    v.asset_risk_score,
    v.risk_level
FROM (SELECT * FROM vessels FINAL) AS v
LEFT JOIN (SELECT * FROM companies FINAL) AS c ON c.id = v.owner_company_id
WHERE v.is_active = 1
ORDER BY v.asset_risk_score DESC
LIMIT 10
```

#### 4.10 授信使用情况
```sql
SELECT sum(outstanding_amount * {fx_rate:Float64})
FROM financial_assets FINAL
WHERE is_active = 1
```

```sql
SELECT c.company_name, sum(a.outstanding_amount * {fx_rate:Float64}) AS used_amount
FROM (SELECT * FROM financial_assets FINAL) AS a
LEFT JOIN (SELECT * FROM companies FINAL) AS c ON c.id = a.company_id
WHERE a.is_active = 1
GROUP BY c.company_name
ORDER BY used_amount DESC
LIMIT 5
```

#### 4.11 风险因子贡献
```sql
SELECT
    factor_name,
    avg(factor_value) AS avg_value,
    sum(contribution) AS total_contribution
FROM risk_factor_contribution
WHERE toDate(created_at) >= {start_date:Date}
  AND toDate(created_at) <= {end_date:Date}
GROUP BY factor_name
ORDER BY abs(sum(contribution)) DESC
LIMIT 5
```

---

## 5. 数据质量 API (app/quality_api.py)

### 文件: app/quality_api.py

#### 5.1 船舶数据质量检查
```sql
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE imo_number IS NULL OR imo_number = '') as null_imo,
    COUNT(*) FILTER (WHERE vessel_name IS NULL OR vessel_name = '') as null_name,
    COUNT(DISTINCT imo_number) as unique_imo
FROM vessels
WHERE is_active = true
```

#### 5.2 企业数据质量检查
```sql
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE company_name IS NULL OR company_name = '') as null_name,
    COUNT(*) FILTER (WHERE registration_country IS NULL) as null_country
FROM companies
WHERE is_active = true
```

#### 5.3 金融资产数据质量检查
```sql
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE asset_type IS NULL) as null_type,
    COUNT(*) FILTER (WHERE principal_amount IS NULL) as null_value
FROM financial_assets
WHERE is_active = true
```

#### 5.4 风险评分质量检查
```sql
SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE risk_score IS NULL) as null_score,
    COUNT(*) FILTER (WHERE risk_score < 0 OR risk_score > 100) as invalid_score
FROM financial_assets
WHERE is_active = true
```

#### 5.5 数据一致性规则检查

##### IMO 号唯一性
```sql
SELECT
    COUNT(*) as total,
    COUNT(DISTINCT imo_number) as unique_count
FROM vessels
WHERE is_active = true AND imo_number IS NOT NULL AND imo_number != ''
```

##### 风险评分范围校验
```sql
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE risk_score < 0 OR risk_score > 100) as violations
FROM financial_assets
WHERE is_active = true AND risk_score IS NOT NULL
```

##### 时间戳一致性
```sql
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE created_at > updated_at) as violations
FROM vessels
WHERE is_active = true
```

#### 5.6 数据时效性检查
```sql
SELECT MAX(created_at) as last_update
FROM vessels
WHERE is_active = true
```

```sql
SELECT MAX(created_at) as last_update
FROM financial_assets
WHERE is_active = true
```

```sql
SELECT MAX(rate_date) as last_update
FROM fx_rates
```

---

## 6. 船舶画像 API (app/profile_api.py)

### 文件: app/profile_api.py

#### 6.1 船舶基础信息查询
```sql
SELECT * FROM vessels WHERE imo_number = %s
```

---

## 7. Dashboard 查询 SQL

### 文件: DBD/postgreSQL-DBD/dashboard_queries.sql

这个文件包含了所有 Dashboard 页面的核心查询，已在上面的 main.py 部分详细列出。主要包括：

- 总体风险敞口查询
- 高风险预警查询
- 不良资产监控查询
- 风险等级分布查询
- 风险趋势查询
- 授信使用查询
- 船舶资产风险 Top 榜
- 风险因子贡献查询
- 汇率波动监控查询

---

## 8. 机器学习模型相关

### 文件: ml_models/predict_api.py, ml_models/data_loader.py

#### 8.1 船舶数据加载
```sql
SELECT
    v.imo_number as vessel_imo,
    v.vessel_name,
    v.vessel_type,
    v.build_year as built_year,
    v.flag_country,
    v.asset_risk_score,
    v.risk_level,
    v.owner_company_id,
    2026 - v.build_year as vessel_age
FROM vessels v
WHERE v.is_active = 1
ORDER BY v.id
LIMIT {limit} OFFSET {offset}
```

#### 8.2 风险等级统计
```sql
SELECT risk_level, COUNT(*) as count
FROM vessels
WHERE is_active = 1
GROUP BY risk_level
```

---

## 9. 数据生成脚本

### 文件: scripts/generate_ais_data_linked.py

#### 9.1 加载船舶数据
```sql
SELECT
    id,
    vessel_name,
    imo_number,
    vessel_type,
    flag_country,
    build_year
FROM silvernav.vessels
WHERE is_active = TRUE
ORDER BY id
LIMIT 200
```

### 文件: scripts/generate_contracts_batch.py

#### 9.2 加载船舶和企业数据
```sql
SELECT v.id, v.imo_number, v.vessel_name, v.vessel_type,
       v.build_year, v.flag_country, v.owner_company_id,
       v.asset_risk_score, v.risk_level
FROM vessels v
WHERE v.is_active = TRUE
ORDER BY v.id
```

```sql
SELECT c.id, c.company_name, c.registration_country,
       c.company_type, c.credit_score, c.risk_level
FROM companies c
WHERE c.is_active = TRUE
ORDER BY c.id
```

---

## 10. 数据迁移脚本

### 文件: clickhouse/migrate_to_clickhouse.py, scripts/migration/*.py

#### 10.1 数据统计查询
```sql
SELECT COUNT(*) FROM {table_name}
```

#### 10.2 批量数据读取
```sql
SELECT {column_list} FROM {table_name} ORDER BY id LIMIT %s OFFSET %s
```

#### 10.3 ClickHouse 数据插入
```sql
INSERT INTO {table_name} VALUES
```

#### 10.4 数据验证查询
```sql
SELECT count() FROM {table_name}
```

---

## 总结

本项目共涉及以下主要 SQL 操作类型：

1. **DDL (数据定义语言)**
   - CREATE TABLE: 创建 PostgreSQL 和 ClickHouse 表
   - CREATE INDEX: 创建索引优化查询
   - CREATE MATERIALIZED VIEW: 创建物化视图
   - ALTER TABLE: 修改表结构

2. **DML (数据操作语言)**
   - SELECT: 数据查询（最常用）
   - INSERT: 数据插入
   - UPDATE: 数据更新
   - DELETE: 数据删除（较少使用，多用软删除）

3. **查询优化技术**
   - CTE (WITH 子句): 提高查询可读性
   - JOIN: 多表关联查询
   - 聚合函数: SUM, COUNT, AVG 等
   - 窗口函数: FILTER, PARTITION BY 等
   - 索引优化: 主键、外键、普通索引

4. **数据库特性**
   - PostgreSQL: 触发器、函数、约束
   - ClickHouse: 分区、物化视图、ReplacingMergeTree 引擎

---

**文档生成时间**: 2026-03-08
**项目**: 银航宝 (SilverNav-Treasure)
**数据库**: PostgreSQL + ClickHouse + MongoDB

---

## 附录 A: 按功能分类的 SQL 查询索引

### A.1 用户认证与权限管理
- 用户登录验证: `main.py:528-537`
- 用户注册: `main.py:625-635`
- 密码重置: `main.py:562-563`
- Root 账户初始化: `main.py:262-271`

### A.2 风险评估与监控
- 总体风险敞口: `main.py:659-688`, `clickhouse_client.py:148-200`
- 高风险预警: `main.py:729-762`, `clickhouse_client.py:200-258`
- 不良资产监控: `main.py:798-806`, `clickhouse_client.py:258-294`
- 风险等级分布: `main.py:844-856`, `clickhouse_client.py:294-303`
- 风险趋势分析: `main.py:915-927`, `clickhouse_client.py:337-346`

### A.3 授信管理
- 授信使用情况: `main.py:355-375`, `clickhouse_client.py:431-440`
- 授信 Top 客户: `main.py:978-980`, `clickhouse_client.py:440-442`
- 授信集中度: `main.py:2393-2395`

### A.4 船舶资产管理
- 船舶基础信息: `profile_api.py:153`
- 船舶风险 Top 榜: `main.py:420-449`, `clickhouse_client.py:395-402`
- 船舶风险历史: `vessel_risk_history` 表相关查询

### A.5 数据质量监控
- 完整性检查: `quality_api.py:24-65`
- 一致性规则: `quality_api.py:213-256`
- 时效性检查: `quality_api.py:307-328`

### A.6 汇率与外币管理
- 汇率查询: `main.py:330`, `clickhouse_client.py:116`
- 汇率历史: `main.py:1031`
- 币种分布: `main.py:394-420`

### A.7 机器学习与预测
- 训练数据加载: `ml_models/data_loader.py:39-87`
- 预测数据查询: `ml_models/predict_api.py:107-226`
- 风险等级统计: `ml_models/predict_api.py:386`

### A.8 数据迁移与同步
- PostgreSQL 数据导出: `migrate_to_clickhouse.py:84-133`
- ClickHouse 数据导入: `migrate_to_clickhouse.py:148-154`
- 数据验证: `migrate_to_clickhouse.py:294`

---

## 附录 B: 性能优化建议

### B.1 PostgreSQL 优化

#### 索引优化
```sql
-- 为 financial_assets 表创建复合索引
CREATE INDEX idx_financial_assets_active_risk ON financial_assets(is_active, risk_level, start_date);
CREATE INDEX idx_financial_assets_company ON financial_assets(company_id, is_active);
CREATE INDEX idx_financial_assets_dates ON financial_assets(start_date, maturity_date);

-- 为 vessels 表创建索引
CREATE INDEX idx_vessels_risk ON vessels(is_active, risk_level);
CREATE INDEX idx_vessels_owner ON vessels(owner_company_id, is_active);

-- 为 companies 表创建索引
CREATE INDEX idx_companies_risk ON companies(is_active, risk_level);

-- 为 vessel_risk_history 表创建索引
CREATE INDEX idx_vessel_risk_history_date ON vessel_risk_history(assessment_date, vessel_id);

-- 为 fx_rates 表创建索引
CREATE INDEX idx_fx_rates_lookup ON fx_rates(base_currency, quote_currency, rate_date DESC);
```

#### 分区表优化
```sql
-- 将 financial_assets 按年份分区
CREATE TABLE financial_assets_2024 PARTITION OF financial_assets
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE financial_assets_2025 PARTITION OF financial_assets
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE financial_assets_2026 PARTITION OF financial_assets
FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

#### 查询优化示例
```sql
-- 优化前：全表扫描
SELECT * FROM financial_assets WHERE risk_level = 'high';

-- 优化后：使用索引 + 只查询需要的列
SELECT id, contract_no, outstanding_amount, risk_score
FROM financial_assets
WHERE is_active = TRUE AND risk_level = 'high'
ORDER BY outstanding_amount DESC
LIMIT 100;
```

### B.2 ClickHouse 优化

#### 使用 PREWHERE 优化
```sql
-- 优化前
SELECT * FROM financial_assets FINAL
WHERE is_active = 1 AND risk_level = 'high' AND start_date >= '2026-01-01';

-- 优化后
SELECT id, contract_no, outstanding_amount, risk_score
FROM financial_assets FINAL
PREWHERE risk_level = 'high'
WHERE is_active = 1 AND start_date >= '2026-01-01';
```

#### 利用物化视图
```sql
-- 直接查询物化视图，避免实时聚合
SELECT risk_level, sum(total_exposure) AS total_exposure
FROM mv_daily_risk_exposure
WHERE stat_date = today() AND currency = 'CNY'
GROUP BY risk_level;
```

#### 分区裁剪
```sql
-- 利用分区键加速查询
SELECT count()
FROM financial_assets
WHERE toYYYYMM(start_date) = 202603  -- 分区裁剪
  AND risk_level = 'high';
```

### B.3 查询缓存策略

#### Redis 缓存键设计
```python
# Dashboard 数据缓存
cache_key = f"dashboard:{base_date}:{range_key}:{currency}"

# 船舶画像缓存
cache_key = f"vessel_profile:{imo_number}:{date}"

# 风险评估缓存
cache_key = f"risk_assessment:{company_id}:{date}"
```

#### 缓存失效策略
```python
# 设置 TTL
cache.set(key, value, ttl=3600)  # 1小时过期

# 主动失效
cache.delete(f"dashboard:*")  # 数据更新时清除相关缓存
```

---

## 附录 C: 常见查询模式

### C.1 时间范围查询
```sql
-- 查询指定时间范围内的资产
SELECT *
FROM financial_assets
WHERE start_date <= :end_date
  AND maturity_date >= :start_date
  AND is_active = TRUE;
```

### C.2 汇率转换查询
```sql
-- 使用 CTE 进行汇率转换
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
    contract_no,
    outstanding_amount * (SELECT rate FROM fx_rate) AS amount_converted
FROM financial_assets
WHERE is_active = TRUE;
```

### C.3 Top N 查询
```sql
-- 查询 Top 10 高风险资产
SELECT
    a.contract_no,
    a.outstanding_amount,
    a.risk_score,
    c.company_name
FROM financial_assets a
LEFT JOIN companies c ON c.id = a.company_id
WHERE a.is_active = TRUE AND a.risk_level = 'high'
ORDER BY a.outstanding_amount DESC
LIMIT 10;
```

### C.4 聚合统计查询
```sql
-- 按风险等级聚合统计
SELECT
    risk_level,
    COUNT(*) AS asset_count,
    SUM(outstanding_amount) AS total_amount,
    AVG(risk_score) AS avg_risk_score
FROM financial_assets
WHERE is_active = TRUE
GROUP BY risk_level
ORDER BY risk_level;
```

### C.5 条件聚合查询
```sql
-- 使用 FILTER 进行条件聚合
SELECT
    COUNT(*) AS total_count,
    COUNT(*) FILTER (WHERE risk_level = 'high') AS high_risk_count,
    COUNT(*) FILTER (WHERE is_non_performing) AS npl_count,
    SUM(outstanding_amount) AS total_amount,
    SUM(outstanding_amount) FILTER (WHERE risk_level = 'high') AS high_risk_amount
FROM financial_assets
WHERE is_active = TRUE;
```

---

## 附录 D: 数据字典

### D.1 核心表字段说明

#### financial_assets (金融资产表)
| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| id | BIGINT | 主键 | 1 |
| company_id | BIGINT | 企业ID | 100 |
| vessel_id | BIGINT | 船舶ID (可空) | 200 |
| asset_type | VARCHAR(50) | 资产类型 | loan, mortgage, leasing |
| contract_no | VARCHAR(100) | 合同编号 | CN-2026-001 |
| principal_amount | NUMERIC(18,2) | 初始本金 | 10000000.00 |
| outstanding_amount | NUMERIC(18,2) | 剩余本金 | 8500000.00 |
| currency | VARCHAR(10) | 币种 | CNY, USD, EUR |
| interest_rate | NUMERIC(8,4) | 利率 | 0.0450 (4.5%) |
| start_date | DATE | 起始日期 | 2026-01-01 |
| maturity_date | DATE | 到期日期 | 2028-12-31 |
| risk_level | VARCHAR(20) | 风险等级 | low, medium, high |
| risk_score | NUMERIC(5,2) | 风险评分 | 75.50 (0-100) |
| is_non_performing | BOOLEAN | 是否不良 | TRUE/FALSE |
| is_active | BOOLEAN | 是否有效 | TRUE/FALSE |

#### vessels (船舶表)
| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| id | BIGINT | 主键 | 1 |
| imo_number | VARCHAR(20) | IMO编号 | IMO9876543 |
| vessel_name | VARCHAR(100) | 船舶名称 | OCEAN STAR |
| vessel_type | VARCHAR(50) | 船舶类型 | Bulk Carrier, Tanker |
| build_year | INT | 建造年份 | 2015 |
| flag_country | VARCHAR(50) | 船旗国 | China, Panama |
| owner_company_id | BIGINT | 所属企业ID | 100 |
| asset_risk_score | NUMERIC(5,2) | 资产风险评分 | 65.30 |
| risk_level | VARCHAR(20) | 风险等级 | low, medium, high |

#### companies (企业表)
| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| id | BIGINT | 主键 | 1 |
| company_name | VARCHAR(200) | 企业名称 | 中远海运集团 |
| registration_country | VARCHAR(50) | 注册国家 | China, Singapore |
| company_type | VARCHAR(50) | 企业类型 | Shipowner, Operator |
| credit_score | NUMERIC(5,2) | 信用评分 | 85.50 |
| risk_level | VARCHAR(20) | 风险等级 | low, medium, high |

### D.2 风险等级定义

| 风险等级 | 评分范围 | 说明 | 处理建议 |
|----------|----------|------|----------|
| low | 0-40 | 低风险 | 正常监控 |
| medium | 41-70 | 中风险 | 加强关注 |
| high | 71-100 | 高风险 | 重点监控，考虑风险缓释措施 |

### D.3 资产类型说明

| 资产类型 | 英文名称 | 说明 |
|----------|----------|------|
| 贷款 | loan | 传统船舶贷款 |
| 抵押 | mortgage | 船舶抵押融资 |
| 租赁 | leasing | 融资租赁 |
| 担保 | guarantee | 担保业务 |
| 保理 | factoring | 应收账款保理 |

---

## 附录 E: 监控与告警 SQL

### E.1 数据质量监控

#### 检查空值比例
```sql
SELECT
    'vessels' AS table_name,
    COUNT(*) AS total_records,
    COUNT(*) FILTER (WHERE imo_number IS NULL) AS null_imo,
    ROUND(COUNT(*) FILTER (WHERE imo_number IS NULL)::NUMERIC / COUNT(*) * 100, 2) AS null_rate
FROM vessels
WHERE is_active = TRUE;
```

#### 检查重复数据
```sql
SELECT imo_number, COUNT(*) AS duplicate_count
FROM vessels
WHERE is_active = TRUE
GROUP BY imo_number
HAVING COUNT(*) > 1;
```

#### 检查数据异常
```sql
-- 检查风险评分异常值
SELECT COUNT(*) AS abnormal_count
FROM financial_assets
WHERE is_active = TRUE
  AND (risk_score < 0 OR risk_score > 100 OR risk_score IS NULL);
```

### E.2 业务指标监控

#### 高风险资产占比告警
```sql
SELECT
    COUNT(*) FILTER (WHERE risk_level = 'high') AS high_risk_count,
    COUNT(*) AS total_count,
    ROUND(COUNT(*) FILTER (WHERE risk_level = 'high')::NUMERIC / COUNT(*) * 100, 2) AS high_risk_ratio
FROM financial_assets
WHERE is_active = TRUE;
-- 告警阈值: high_risk_ratio > 20%
```

#### 不良资产率告警
```sql
SELECT
    COUNT(*) FILTER (WHERE is_non_performing) AS npl_count,
    COUNT(*) AS total_count,
    ROUND(COUNT(*) FILTER (WHERE is_non_performing)::NUMERIC / COUNT(*) * 100, 2) AS npl_ratio
FROM financial_assets
WHERE is_active = TRUE;
-- 告警阈值: npl_ratio > 5%
```

#### 授信集中度告警
```sql
WITH top_customer AS (
    SELECT
        company_id,
        SUM(outstanding_amount) AS total_exposure
    FROM financial_assets
    WHERE is_active = TRUE
    GROUP BY company_id
    ORDER BY total_exposure DESC
    LIMIT 1
)
SELECT
    tc.total_exposure AS top_customer_exposure,
    (SELECT SUM(outstanding_amount) FROM financial_assets WHERE is_active = TRUE) AS total_exposure,
    ROUND(tc.total_exposure / (SELECT SUM(outstanding_amount) FROM financial_assets WHERE is_active = TRUE) * 100, 2) AS concentration_ratio
FROM top_customer tc;
-- 告警阈值: concentration_ratio > 30%
```

### E.3 系统性能监控

#### 慢查询监控 (PostgreSQL)
```sql
-- 查看慢查询
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE mean_time > 1000  -- 平均执行时间 > 1秒
ORDER BY mean_time DESC
LIMIT 20;
```

#### 表大小监控
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'silvernav'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 附录 F: 数据备份与恢复

### F.1 PostgreSQL 备份

#### 全库备份
```bash
pg_dump -h localhost -U postgres -d silvernav_db > backup_$(date +%Y%m%d).sql
```

#### 单表备份
```bash
pg_dump -h localhost -U postgres -d silvernav_db -t silvernav.financial_assets > financial_assets_backup.sql
```

#### 数据导出为 CSV
```sql
COPY (
    SELECT * FROM financial_assets WHERE is_active = TRUE
) TO '/tmp/financial_assets.csv' WITH CSV HEADER;
```

### F.2 ClickHouse 备份

#### 表备份
```sql
-- 创建备份表
CREATE TABLE financial_assets_backup AS financial_assets;

-- 插入数据
INSERT INTO financial_assets_backup SELECT * FROM financial_assets;
```

#### 分区备份
```sql
-- 备份指定分区
ALTER TABLE financial_assets FREEZE PARTITION '202603';
```

### F.3 数据恢复

#### PostgreSQL 恢复
```bash
psql -h localhost -U postgres -d silvernav_db < backup_20260308.sql
```

#### ClickHouse 恢复
```sql
-- 从备份表恢复
INSERT INTO financial_assets SELECT * FROM financial_assets_backup;
```

---

## 附录 G: 安全与权限管理

### G.1 用户权限设置

#### 创建只读用户
```sql
-- PostgreSQL
CREATE USER readonly_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE silvernav_db TO readonly_user;
GRANT USAGE ON SCHEMA silvernav TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA silvernav TO readonly_user;
```

#### 创建应用用户
```sql
-- PostgreSQL
CREATE USER app_user WITH PASSWORD 'app_password';
GRANT CONNECT ON DATABASE silvernav_db TO app_user;
GRANT USAGE ON SCHEMA silvernav TO app_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA silvernav TO app_user;
```

### G.2 数据脱敏查询

#### 敏感信息脱敏
```sql
-- 脱敏企业名称
SELECT
    id,
    LEFT(company_name, 3) || '***' AS company_name_masked,
    registration_country,
    risk_level
FROM companies;

-- 脱敏合同编号
SELECT
    id,
    LEFT(contract_no, 5) || '***' AS contract_no_masked,
    outstanding_amount,
    risk_level
FROM financial_assets;
```

---

## 附录 H: 测试数据生成

### H.1 生成测试企业数据
```sql
INSERT INTO companies (company_name, registration_country, company_type, credit_score, risk_level, is_active)
SELECT
    'Test Company ' || generate_series AS company_name,
    CASE (random() * 4)::INT
        WHEN 0 THEN 'China'
        WHEN 1 THEN 'Singapore'
        WHEN 2 THEN 'Hong Kong'
        WHEN 3 THEN 'Japan'
        ELSE 'South Korea'
    END AS registration_country,
    CASE (random() * 2)::INT
        WHEN 0 THEN 'Shipowner'
        WHEN 1 THEN 'Operator'
        ELSE 'Charterer'
    END AS company_type,
    (random() * 100)::NUMERIC(5,2) AS credit_score,
    CASE
        WHEN random() < 0.6 THEN 'low'
        WHEN random() < 0.9 THEN 'medium'
        ELSE 'high'
    END AS risk_level,
    TRUE AS is_active
FROM generate_series(1, 100);
```

### H.2 生成测试船舶数据
```sql
INSERT INTO vessels (imo_number, vessel_name, vessel_type, build_year, flag_country, owner_company_id, asset_risk_score, risk_level, is_active)
SELECT
    'IMO' || LPAD(generate_series::TEXT, 7, '0') AS imo_number,
    'Test Vessel ' || generate_series AS vessel_name,
    CASE (random() * 4)::INT
        WHEN 0 THEN 'Bulk Carrier'
        WHEN 1 THEN 'Container Ship'
        WHEN 2 THEN 'Tanker'
        WHEN 3 THEN 'LNG Carrier'
        ELSE 'General Cargo'
    END AS vessel_type,
    2000 + (random() * 24)::INT AS build_year,
    CASE (random() * 4)::INT
        WHEN 0 THEN 'China'
        WHEN 1 THEN 'Panama'
        WHEN 2 THEN 'Liberia'
        WHEN 3 THEN 'Marshall Islands'
        ELSE 'Singapore'
    END AS flag_country,
    (random() * 100 + 1)::BIGINT AS owner_company_id,
    (random() * 100)::NUMERIC(5,2) AS asset_risk_score,
    CASE
        WHEN random() < 0.6 THEN 'low'
        WHEN random() < 0.9 THEN 'medium'
        ELSE 'high'
    END AS risk_level,
    TRUE AS is_active
FROM generate_series(1, 500);
```

### H.3 生成测试金融资产数据
```sql
INSERT INTO financial_assets (
    company_id, vessel_id, asset_type, contract_no,
    principal_amount, outstanding_amount, currency,
    interest_rate, start_date, maturity_date,
    risk_level, risk_score, is_non_performing, is_active
)
SELECT
    (random() * 100 + 1)::BIGINT AS company_id,
    (random() * 500 + 1)::BIGINT AS vessel_id,
    CASE (random() * 4)::INT
        WHEN 0 THEN 'loan'
        WHEN 1 THEN 'mortgage'
        WHEN 2 THEN 'leasing'
        WHEN 3 THEN 'guarantee'
        ELSE 'factoring'
    END AS asset_type,
    'CN-2026-' || LPAD(generate_series::TEXT, 6, '0') AS contract_no,
    (random() * 50000000 + 1000000)::NUMERIC(18,2) AS principal_amount,
    (random() * 40000000 + 500000)::NUMERIC(18,2) AS outstanding_amount,
    CASE (random() * 2)::INT
        WHEN 0 THEN 'CNY'
        WHEN 1 THEN 'USD'
        ELSE 'EUR'
    END AS currency,
    (random() * 0.05 + 0.03)::NUMERIC(8,4) AS interest_rate,
    CURRENT_DATE - (random() * 365)::INT AS start_date,
    CURRENT_DATE + (random() * 1095)::INT AS maturity_date,
    CASE
        WHEN random() < 0.6 THEN 'low'
        WHEN random() < 0.9 THEN 'medium'
        ELSE 'high'
    END AS risk_level,
    (random() * 100)::NUMERIC(5,2) AS risk_score,
    random() < 0.05 AS is_non_performing,
    TRUE AS is_active
FROM generate_series(1, 1000);
```

---

**文档版本**: v1.0
**最后更新**: 2026-03-08
**维护者**: SilverNav Development Team


---

## 附录 I: MongoDB 查询语句

### 文件: app/behavior_api.py, app/profile_api.py, scripts/generate_ais_data_linked.py

虽然本项目主要使用 PostgreSQL 和 ClickHouse，但 AIS 轨迹数据存储在 MongoDB 中。以下是相关的 MongoDB 查询。

#### I.1 AIS 轨迹数据查询

##### 查询船舶最近30天的轨迹
```javascript
db.ais_tracks.find({
    "imo_number": "IMO9876543",
    "timestamp": {
        "$gte": ISODate("2026-02-06T00:00:00Z"),
        "$lte": ISODate("2026-03-08T00:00:00Z")
    }
}).sort({ "timestamp": 1 })
```

##### 统计轨迹数量
```javascript
db.ais_tracks.countDocuments({
    "imo_number": "IMO9876543",
    "timestamp": {
        "$gte": ISODate("2026-02-06T00:00:00Z"),
        "$lte": ISODate("2026-03-08T00:00:00Z")
    }
})
```

##### 查询船舶最新位置
```javascript
db.ais_tracks.findOne(
    { "imo_number": "IMO9876543" },
    { sort: { "timestamp": -1 } }
)
```

##### 聚合查询 - 计算平均速度
```javascript
db.ais_tracks.aggregate([
    {
        $match: {
            "imo_number": "IMO9876543",
            "timestamp": {
                "$gte": ISODate("2026-02-06T00:00:00Z"),
                "$lte": ISODate("2026-03-08T00:00:00Z")
            }
        }
    },
    {
        $group: {
            "_id": null,
            "avg_speed": { "$avg": "$speed" },
            "max_speed": { "$max": "$speed" },
            "min_speed": { "$min": "$speed" }
        }
    }
])
```

##### 地理空间查询 - 查询指定区域内的船舶
```javascript
db.ais_tracks.find({
    "location": {
        "$geoWithin": {
            "$box": [
                [120.0, 30.0],  // 左下角坐标
                [122.0, 32.0]   // 右上角坐标
            ]
        }
    },
    "timestamp": {
        "$gte": ISODate("2026-03-08T00:00:00Z")
    }
})
```

##### 创建地理空间索引
```javascript
db.ais_tracks.createIndex({ "location": "2dsphere" })
db.ais_tracks.createIndex({ "imo_number": 1, "timestamp": -1 })
db.ais_tracks.createIndex({ "timestamp": 1 })
```

#### I.2 船舶合同文档查询

##### 查询合同文档
```javascript
db.contracts.find({
    "contract_no": "CN-2026-000001"
})
```

##### 查询企业的所有合同
```javascript
db.contracts.find({
    "company_id": 100
}).sort({ "created_at": -1 })
```

##### 全文搜索合同内容
```javascript
db.contracts.find({
    "$text": { "$search": "船舶抵押" }
})
```

##### 创建文本索引
```javascript
db.contracts.createIndex({
    "contract_content": "text",
    "contract_no": "text",
    "company_name": "text"
})
```

#### I.3 数据清理与维护

##### 删除旧数据（保留最近3个月）
```javascript
db.ais_tracks.deleteMany({
    "timestamp": {
        "$lt": ISODate("2025-12-08T00:00:00Z")
    }
})
```

##### 统计集合大小
```javascript
db.ais_tracks.stats()
```

##### 查看索引使用情况
```javascript
db.ais_tracks.aggregate([
    { $indexStats: {} }
])
```

---

## 附录 J: 数据分析常用 SQL

### J.1 时间序列分析

#### 按月统计资产增长
```sql
SELECT
    DATE_TRUNC('month', start_date) AS month,
    COUNT(*) AS new_assets,
    SUM(principal_amount) AS total_principal
FROM financial_assets
WHERE start_date >= '2025-01-01'
GROUP BY DATE_TRUNC('month', start_date)
ORDER BY month;
```

#### 按周统计风险变化
```sql
SELECT
    DATE_TRUNC('week', assessment_date) AS week,
    AVG(risk_score) AS avg_risk_score,
    COUNT(*) AS assessment_count
FROM vessel_risk_history
WHERE assessment_date >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY DATE_TRUNC('week', assessment_date)
ORDER BY week;
```

#### 滚动窗口分析 - 30天移动平均
```sql
SELECT
    assessment_date,
    risk_score,
    AVG(risk_score) OVER (
        ORDER BY assessment_date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS moving_avg_30d
FROM vessel_risk_history
WHERE vessel_id = 1
ORDER BY assessment_date;
```

### J.2 同比环比分析

#### 同比增长率
```sql
WITH current_year AS (
    SELECT
        DATE_TRUNC('month', start_date) AS month,
        SUM(principal_amount) AS amount
    FROM financial_assets
    WHERE EXTRACT(YEAR FROM start_date) = 2026
    GROUP BY DATE_TRUNC('month', start_date)
),
last_year AS (
    SELECT
        DATE_TRUNC('month', start_date) + INTERVAL '1 year' AS month,
        SUM(principal_amount) AS amount
    FROM financial_assets
    WHERE EXTRACT(YEAR FROM start_date) = 2025
    GROUP BY DATE_TRUNC('month', start_date)
)
SELECT
    cy.month,
    cy.amount AS current_amount,
    ly.amount AS last_year_amount,
    ROUND((cy.amount - ly.amount) / ly.amount * 100, 2) AS yoy_growth_rate
FROM current_year cy
LEFT JOIN last_year ly ON cy.month = ly.month
ORDER BY cy.month;
```

#### 环比增长率
```sql
WITH monthly_data AS (
    SELECT
        DATE_TRUNC('month', start_date) AS month,
        SUM(principal_amount) AS amount
    FROM financial_assets
    WHERE start_date >= '2025-01-01'
    GROUP BY DATE_TRUNC('month', start_date)
)
SELECT
    month,
    amount,
    LAG(amount) OVER (ORDER BY month) AS prev_month_amount,
    ROUND((amount - LAG(amount) OVER (ORDER BY month)) / 
          LAG(amount) OVER (ORDER BY month) * 100, 2) AS mom_growth_rate
FROM monthly_data
ORDER BY month;
```

### J.3 客户分层分析

#### RFM 分析（最近、频率、金额）
```sql
WITH customer_metrics AS (
    SELECT
        company_id,
        MAX(start_date) AS last_transaction_date,
        COUNT(*) AS transaction_frequency,
        SUM(principal_amount) AS total_amount
    FROM financial_assets
    WHERE is_active = TRUE
    GROUP BY company_id
),
rfm_scores AS (
    SELECT
        company_id,
        NTILE(5) OVER (ORDER BY last_transaction_date DESC) AS recency_score,
        NTILE(5) OVER (ORDER BY transaction_frequency) AS frequency_score,
        NTILE(5) OVER (ORDER BY total_amount) AS monetary_score
    FROM customer_metrics
)
SELECT
    c.company_name,
    r.recency_score,
    r.frequency_score,
    r.monetary_score,
    (r.recency_score + r.frequency_score + r.monetary_score) AS total_score,
    CASE
        WHEN (r.recency_score + r.frequency_score + r.monetary_score) >= 12 THEN 'VIP客户'
        WHEN (r.recency_score + r.frequency_score + r.monetary_score) >= 9 THEN '重要客户'
        WHEN (r.recency_score + r.frequency_score + r.monetary_score) >= 6 THEN '普通客户'
        ELSE '低价值客户'
    END AS customer_segment
FROM rfm_scores r
JOIN companies c ON c.id = r.company_id
ORDER BY total_score DESC;
```

#### 客户贡献度分析（帕累托分析）
```sql
WITH customer_contribution AS (
    SELECT
        company_id,
        SUM(outstanding_amount) AS total_exposure,
        SUM(SUM(outstanding_amount)) OVER () AS grand_total
    FROM financial_assets
    WHERE is_active = TRUE
    GROUP BY company_id
),
cumulative_contribution AS (
    SELECT
        company_id,
        total_exposure,
        ROUND(total_exposure / grand_total * 100, 2) AS contribution_pct,
        ROUND(SUM(total_exposure) OVER (ORDER BY total_exposure DESC) / grand_total * 100, 2) AS cumulative_pct,
        ROW_NUMBER() OVER (ORDER BY total_exposure DESC) AS rank
    FROM customer_contribution
)
SELECT
    c.company_name,
    cc.total_exposure,
    cc.contribution_pct,
    cc.cumulative_pct,
    cc.rank,
    CASE
        WHEN cc.cumulative_pct <= 80 THEN 'A类客户 (80%贡献)'
        WHEN cc.cumulative_pct <= 95 THEN 'B类客户 (15%贡献)'
        ELSE 'C类客户 (5%贡献)'
    END AS abc_category
FROM cumulative_contribution cc
JOIN companies c ON c.id = cc.company_id
ORDER BY cc.rank;
```

### J.4 风险预警分析

#### 识别潜在违约客户
```sql
WITH customer_risk_indicators AS (
    SELECT
        fa.company_id,
        COUNT(*) AS total_assets,
        COUNT(*) FILTER (WHERE fa.is_non_performing) AS npl_count,
        AVG(fa.risk_score) AS avg_risk_score,
        SUM(fa.outstanding_amount) AS total_exposure,
        MAX(fa.maturity_date) AS nearest_maturity
    FROM financial_assets fa
    WHERE fa.is_active = TRUE
    GROUP BY fa.company_id
)
SELECT
    c.company_name,
    c.risk_level,
    cri.total_assets,
    cri.npl_count,
    ROUND(cri.npl_count::NUMERIC / cri.total_assets * 100, 2) AS npl_ratio,
    ROUND(cri.avg_risk_score, 2) AS avg_risk_score,
    cri.total_exposure,
    cri.nearest_maturity,
    CASE
        WHEN cri.npl_count > 0 AND cri.avg_risk_score > 70 THEN '高风险预警'
        WHEN cri.avg_risk_score > 70 THEN '中风险关注'
        WHEN cri.npl_count > 0 THEN '不良资产关注'
        ELSE '正常'
    END AS warning_level
FROM customer_risk_indicators cri
JOIN companies c ON c.id = cri.company_id
WHERE cri.npl_count > 0 OR cri.avg_risk_score > 60
ORDER BY cri.avg_risk_score DESC, cri.npl_count DESC;
```

#### 即将到期资产预警
```sql
SELECT
    fa.contract_no,
    c.company_name,
    v.vessel_name,
    fa.outstanding_amount,
    fa.maturity_date,
    fa.maturity_date - CURRENT_DATE AS days_to_maturity,
    fa.risk_level,
    CASE
        WHEN fa.maturity_date - CURRENT_DATE <= 30 THEN '紧急'
        WHEN fa.maturity_date - CURRENT_DATE <= 90 THEN '重要'
        ELSE '一般'
    END AS urgency_level
FROM financial_assets fa
LEFT JOIN companies c ON c.id = fa.company_id
LEFT JOIN vessels v ON v.id = fa.vessel_id
WHERE fa.is_active = TRUE
  AND fa.maturity_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
ORDER BY fa.maturity_date ASC;
```

### J.5 行业对比分析

#### 按船舶类型统计风险
```sql
SELECT
    v.vessel_type,
    COUNT(DISTINCT v.id) AS vessel_count,
    COUNT(fa.id) AS asset_count,
    SUM(fa.outstanding_amount) AS total_exposure,
    AVG(fa.risk_score) AS avg_risk_score,
    COUNT(*) FILTER (WHERE fa.risk_level = 'high') AS high_risk_count,
    ROUND(COUNT(*) FILTER (WHERE fa.risk_level = 'high')::NUMERIC / COUNT(*) * 100, 2) AS high_risk_ratio
FROM vessels v
LEFT JOIN financial_assets fa ON fa.vessel_id = v.id AND fa.is_active = TRUE
WHERE v.is_active = TRUE
GROUP BY v.vessel_type
ORDER BY total_exposure DESC;
```

#### 按国家/地区统计风险
```sql
SELECT
    c.registration_country,
    COUNT(DISTINCT c.id) AS company_count,
    COUNT(fa.id) AS asset_count,
    SUM(fa.outstanding_amount) AS total_exposure,
    AVG(c.credit_score) AS avg_credit_score,
    COUNT(*) FILTER (WHERE c.risk_level = 'high') AS high_risk_company_count
FROM companies c
LEFT JOIN financial_assets fa ON fa.company_id = c.id AND fa.is_active = TRUE
WHERE c.is_active = TRUE
GROUP BY c.registration_country
ORDER BY total_exposure DESC;
```

### J.6 相关性分析

#### 船龄与风险评分的相关性
```sql
WITH vessel_age_risk AS (
    SELECT
        v.id,
        2026 - v.build_year AS vessel_age,
        v.asset_risk_score
    FROM vessels v
    WHERE v.is_active = TRUE
      AND v.asset_risk_score IS NOT NULL
)
SELECT
    CASE
        WHEN vessel_age < 5 THEN '0-5年'
        WHEN vessel_age < 10 THEN '5-10年'
        WHEN vessel_age < 15 THEN '10-15年'
        WHEN vessel_age < 20 THEN '15-20年'
        ELSE '20年以上'
    END AS age_group,
    COUNT(*) AS vessel_count,
    ROUND(AVG(asset_risk_score), 2) AS avg_risk_score,
    ROUND(MIN(asset_risk_score), 2) AS min_risk_score,
    ROUND(MAX(asset_risk_score), 2) AS max_risk_score,
    ROUND(STDDEV(asset_risk_score), 2) AS stddev_risk_score
FROM vessel_age_risk
GROUP BY age_group
ORDER BY age_group;
```

---

## 附录 K: 报表生成 SQL

### K.1 日报

#### 每日风险概览报表
```sql
-- 每日风险概览
WITH daily_summary AS (
    SELECT
        CURRENT_DATE AS report_date,
        COUNT(*) AS total_assets,
        SUM(outstanding_amount) AS total_exposure,
        COUNT(*) FILTER (WHERE risk_level = 'high') AS high_risk_count,
        SUM(outstanding_amount) FILTER (WHERE risk_level = 'high') AS high_risk_exposure,
        COUNT(*) FILTER (WHERE is_non_performing) AS npl_count,
        SUM(outstanding_amount) FILTER (WHERE is_non_performing) AS npl_amount
    FROM financial_assets
    WHERE is_active = TRUE
)
SELECT
    report_date,
    total_assets,
    total_exposure,
    high_risk_count,
    ROUND(high_risk_count::NUMERIC / total_assets * 100, 2) AS high_risk_ratio,
    high_risk_exposure,
    ROUND(high_risk_exposure / total_exposure * 100, 2) AS high_risk_exposure_ratio,
    npl_count,
    ROUND(npl_count::NUMERIC / total_assets * 100, 2) AS npl_ratio,
    npl_amount,
    ROUND(npl_amount / total_exposure * 100, 2) AS npl_amount_ratio
FROM daily_summary;
```

### K.2 周报

#### 每周风险变化报表
```sql
WITH weekly_data AS (
    SELECT
        DATE_TRUNC('week', assessment_date) AS week,
        AVG(risk_score) AS avg_risk_score,
        COUNT(DISTINCT vessel_id) AS assessed_vessels
    FROM vessel_risk_history
    WHERE assessment_date >= CURRENT_DATE - INTERVAL '4 weeks'
    GROUP BY DATE_TRUNC('week', assessment_date)
)
SELECT
    week,
    avg_risk_score,
    assessed_vessels,
    LAG(avg_risk_score) OVER (ORDER BY week) AS prev_week_score,
    ROUND(avg_risk_score - LAG(avg_risk_score) OVER (ORDER BY week), 2) AS score_change
FROM weekly_data
ORDER BY week DESC;
```

### K.3 月报

#### 月度综合报表
```sql
-- 月度资产统计
WITH monthly_assets AS (
    SELECT
        DATE_TRUNC('month', start_date) AS month,
        COUNT(*) AS new_assets,
        SUM(principal_amount) AS new_principal
    FROM financial_assets
    WHERE start_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', start_date)
),
monthly_risk AS (
    SELECT
        DATE_TRUNC('month', assessment_date) AS month,
        AVG(risk_score) AS avg_risk_score
    FROM vessel_risk_history
    WHERE assessment_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', assessment_date)
)
SELECT
    ma.month,
    ma.new_assets,
    ma.new_principal,
    mr.avg_risk_score,
    LAG(ma.new_assets) OVER (ORDER BY ma.month) AS prev_month_assets,
    LAG(mr.avg_risk_score) OVER (ORDER BY ma.month) AS prev_month_risk
FROM monthly_assets ma
LEFT JOIN monthly_risk mr ON ma.month = mr.month
ORDER BY ma.month DESC;
```

### K.4 年报

#### 年度总结报表
```sql
SELECT
    EXTRACT(YEAR FROM start_date) AS year,
    COUNT(*) AS total_new_assets,
    SUM(principal_amount) AS total_new_principal,
    AVG(risk_score) AS avg_risk_score,
    COUNT(*) FILTER (WHERE risk_level = 'high') AS high_risk_count,
    COUNT(*) FILTER (WHERE is_non_performing) AS npl_count
FROM financial_assets
WHERE start_date >= '2020-01-01'
GROUP BY EXTRACT(YEAR FROM start_date)
ORDER BY year DESC;
```

---

## 附录 L: 数据导出模板

### L.1 Excel 导出格式

#### 客户清单导出
```sql
SELECT
    c.id AS "客户ID",
    c.company_name AS "客户名称",
    c.registration_country AS "注册国家",
    c.company_type AS "客户类型",
    c.credit_score AS "信用评分",
    c.risk_level AS "风险等级",
    COUNT(fa.id) AS "资产数量",
    COALESCE(SUM(fa.outstanding_amount), 0) AS "总敞口金额",
    COALESCE(AVG(fa.risk_score), 0) AS "平均风险评分"
FROM companies c
LEFT JOIN financial_assets fa ON fa.company_id = c.id AND fa.is_active = TRUE
WHERE c.is_active = TRUE
GROUP BY c.id, c.company_name, c.registration_country, c.company_type, c.credit_score, c.risk_level
ORDER BY "总敞口金额" DESC;
```

#### 资产明细导出
```sql
SELECT
    fa.contract_no AS "合同编号",
    c.company_name AS "客户名称",
    v.vessel_name AS "船舶名称",
    v.imo_number AS "IMO编号",
    fa.asset_type AS "资产类型",
    fa.principal_amount AS "初始本金",
    fa.outstanding_amount AS "剩余本金",
    fa.currency AS "币种",
    fa.interest_rate AS "利率",
    fa.start_date AS "起始日期",
    fa.maturity_date AS "到期日期",
    fa.risk_level AS "风险等级",
    fa.risk_score AS "风险评分",
    CASE WHEN fa.is_non_performing THEN '是' ELSE '否' END AS "是否不良"
FROM financial_assets fa
LEFT JOIN companies c ON c.id = fa.company_id
LEFT JOIN vessels v ON v.id = fa.vessel_id
WHERE fa.is_active = TRUE
ORDER BY fa.outstanding_amount DESC;
```

### L.2 CSV 批量导出

#### 批量导出命令
```sql
-- 导出客户数据
COPY (
    SELECT * FROM companies WHERE is_active = TRUE
) TO '/tmp/companies_export.csv' WITH CSV HEADER;

-- 导出船舶数据
COPY (
    SELECT * FROM vessels WHERE is_active = TRUE
) TO '/tmp/vessels_export.csv' WITH CSV HEADER;

-- 导出资产数据
COPY (
    SELECT * FROM financial_assets WHERE is_active = TRUE
) TO '/tmp/financial_assets_export.csv' WITH CSV HEADER;
```

---

## 附录 M: 故障排查 SQL

### M.1 性能问题排查

#### 查找锁等待
```sql
-- PostgreSQL
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

#### 查找长时间运行的查询
```sql
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
  AND state = 'active';
```

#### 查看表膨胀情况
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size,
    n_live_tup,
    n_dead_tup,
    ROUND(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_tuple_ratio
FROM pg_stat_user_tables
WHERE schemaname = 'silvernav'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### M.2 数据一致性检查

#### 检查外键完整性
```sql
-- 检查 financial_assets 中的 company_id 是否都存在
SELECT COUNT(*) AS orphaned_records
FROM financial_assets fa
LEFT JOIN companies c ON c.id = fa.company_id
WHERE c.id IS NULL AND fa.is_active = TRUE;

-- 检查 vessels 中的 owner_company_id 是否都存在
SELECT COUNT(*) AS orphaned_records
FROM vessels v
LEFT JOIN companies c ON c.id = v.owner_company_id
WHERE c.id IS NULL AND v.is_active = TRUE;
```

#### 检查数据逻辑一致性
```sql
-- 检查起始日期晚于到期日期的异常数据
SELECT COUNT(*) AS invalid_date_records
FROM financial_assets
WHERE start_date > maturity_date AND is_active = TRUE;

-- 检查剩余本金大于初始本金的异常数据
SELECT COUNT(*) AS invalid_amount_records
FROM financial_assets
WHERE outstanding_amount > principal_amount AND is_active = TRUE;
```

---

## 附录 N: API 接口与 SQL 映射表

| API 端点 | HTTP 方法 | 主要 SQL 查询 | 文件位置 |
|----------|-----------|---------------|----------|
| `/api/login` | POST | `SELECT ... FROM users WHERE account=%s` | main.py:528 |
| `/api/register` | POST | `INSERT INTO users ...` | main.py:635 |
| `/api/dashboard/summary` | GET | 总体风险敞口查询 | main.py:659 |
| `/api/dashboard/alerts` | GET | 高风险预警查询 | main.py:729 |
| `/api/dashboard/npl` | GET | 不良资产监控查询 | main.py:798 |
| `/api/dashboard/risk-levels` | GET | 风险等级分布查询 | main.py:844 |
| `/api/dashboard/trend` | GET | 风险趋势查询 | main.py:915 |
| `/api/dashboard/credit` | GET | 授信使用查询 | main.py:978 |
| `/api/dashboard/vessel-top` | GET | 船舶风险Top榜 | main.py:420 |
| `/api/dashboard/risk-factors` | GET | 风险因子贡献查询 | main.py:449 |
| `/api/quality/completeness` | GET | 数据完整性检查 | quality_api.py:24 |
| `/api/quality/consistency` | GET | 数据一致性检查 | quality_api.py:213 |
| `/api/quality/timeliness` | GET | 数据时效性检查 | quality_api.py:307 |
| `/api/profile/vessel/:imo` | GET | 船舶画像查询 | profile_api.py:153 |
| `/api/ml/predict` | POST | 机器学习预测 | predict_api.py:107 |

---

**文档完成**

本文档共包含 1590+ 行，涵盖了银航宝项目中所有的 SQL 查询语句，包括：
- PostgreSQL 和 ClickHouse 的表结构定义
- 主应用和各个模块的查询语句
- MongoDB 的查询语句
- 性能优化建议
- 数据分析和报表生成 SQL
- 故障排查和监控 SQL

文档持续更新中，如有新增查询请及时补充。

