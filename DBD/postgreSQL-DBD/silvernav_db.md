## 数据库 ER 图

```mermaid
erDiagram
    USERS {
        bigint id PK
        varchar account UNIQUE
        varchar username
        varchar password_hash
        varchar status
        varchar account_type
        int failed_login_count
        timestamp locked_until
        timestamp last_login_at
        boolean is_deleted
        timestamp created_at
        timestamp updated_at
    }
    COMPANIES {
        bigint id PK
        varchar company_name
        varchar registration_country
        varchar company_type
        numeric credit_score
        varchar risk_level
        boolean is_active
        timestamp created_at
    }
    VESSELS {
        bigint id PK
        varchar imo_number UNIQUE
        varchar vessel_name
        varchar vessel_type
        int build_year
        varchar flag_country
        bigint owner_company_id FK
        numeric asset_risk_score
        varchar risk_level
        boolean is_active
        timestamp created_at
    }
    VESSEL-RISK-HISTORY {
        bigint id PK
        bigint vessel_id FK
        date assessment_date
        numeric risk_score
        varchar risk_level
        timestamp created_at
    }
    RISK-FACTOR-CONTRIBUTION {
        bigint id PK
        varchar target_type
        bigint target_id
        varchar factor_name
        numeric factor_value
        numeric contribution
        varchar model_version
        timestamp created_at
    }
    FINANCIAL-RISK-SNAPSHOT {
        bigint id PK
        date snapshot_date
        varchar snapshot_type
        numeric high_risk_exposure
        int high_risk_company_count
        int high_risk_vessel_count
        varchar currency
        timestamp created_at
    }
    CREDIT-RISK-ASSESSMENT {
        bigint id PK
        bigint company_id FK
        numeric credit_score
        numeric asset_quality_score
        numeric suggested_credit_min
        numeric suggested_credit_max
        date assessment_date
        varchar assessment_version
        timestamp created_at
    }
    FX-RATES {
        bigint id PK
        varchar base_currency
        varchar quote_currency
        numeric rate
        date rate_date
        varchar source
        timestamp created_at
    }

    VESSELS }o--|| COMPANIES : "owner_company_id"
    VESSEL-RISK-HISTORY }o--|| VESSELS : "vessel_id"
    CREDIT-RISK-ASSESSMENT }o--|| COMPANIES : "company_id"