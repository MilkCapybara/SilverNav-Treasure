"""
Dashboard API ClickHouse 适配模块
用途：修改 main.py 中的 /api/dashboard 端点，使用 ClickHouse 查询
"""

# 在 main.py 顶部添加以下导入
from app.clickhouse_client import (
    init_clickhouse,
    close_clickhouse,
    check_clickhouse_health,
    get_fx_rate_ch,
    get_dashboard_summary_ch,
    get_dashboard_alerts_ch,
    get_dashboard_npl_ch,
    get_dashboard_risk_levels_ch,
    get_dashboard_trend_ch,
    get_dashboard_vessel_top_ch,
    get_dashboard_credit_ch,
    get_dashboard_risk_factors_ch
)

# ============================================================================
# 修改 @app.on_event("startup") 函数
# ============================================================================
@app.on_event("startup")
def on_startup() -> None:
    init_pools()
    ensure_root_user()

    # 初始化 ClickHouse 连接
    try:
        init_clickhouse()
        print("✅ ClickHouse 已启用")
    except Exception as e:
        print(f"⚠️ ClickHouse 初始化失败，将使用 PostgreSQL: {e}")


# ============================================================================
# 修改 @app.on_event("shutdown") 函数
# ============================================================================
@app.on_event("shutdown")
def on_shutdown() -> None:
    close_pools()
    close_clickhouse()


# ============================================================================
# 新增：ClickHouse 健康检查端点
# ============================================================================
@app.get("/api/clickhouse/health")
async def clickhouse_health():
    """检查 ClickHouse 连接状态"""
    is_healthy = check_clickhouse_health()
    return JSONResponse({
        "success": True,
        "clickhouse_enabled": is_healthy,
        "message": "ClickHouse 连接正常" if is_healthy else "ClickHouse 连接失败，使用 PostgreSQL"
    })


# ============================================================================
# 修改 @app.post("/api/dashboard") 函数
# 使用 ClickHouse 查询，失败时降级到 PostgreSQL
# ============================================================================
@app.post("/api/dashboard")
async def dashboard_data(request: Request, payload: DashboardQuery):
    """
    Dashboard 数据查询接口
    优先使用 ClickHouse，失败时降级到 PostgreSQL
    """
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"

    base, currency, start_date, end_date, soon_end, fx_start = dashboard_params(payload)

    # 尝试使用 ClickHouse
    use_clickhouse = check_clickhouse_health()

    try:
        if use_clickhouse:
            # ============================================================================
            # ClickHouse 查询路径（快速）
            # ============================================================================
            print(f"🚀 使用 ClickHouse 查询 Dashboard 数据")
            query_start = time.time()

            # 获取汇率
            fx_rate = get_fx_rate_ch(currency, end_date)

            # 1. 总体风险敞口 + 风险分布
            summary_data = get_dashboard_summary_ch(start_date, end_date, fx_rate)
            summary = {
                "total_exposure": summary_data['total_exposure'],
                "high_risk_exposure": summary_data['high_risk_exposure']
            }
            risk_distribution = summary_data['risk_distribution']

            # 2. 高风险预警
            alerts_data = get_dashboard_alerts_ch(fx_rate)
            high_risk_assets = alerts_data['alert_list']
            high_risk_company_count = alerts_data['high_risk_company_count']
            high_risk_vessel_count = alerts_data['high_risk_vessel_count']

            # 3. 不良资产监控
            npl_stats = get_dashboard_npl_ch(start_date, end_date, fx_rate)

            # 4. 风险等级分布
            risk_levels_data = get_dashboard_risk_levels_ch()
            company_risk = risk_levels_data['company_distribution']
            vessel_risk = risk_levels_data['vessel_distribution']

            # 5. 船舶风险 Top10
            vessel_top = get_dashboard_vessel_top_ch()

            # 6. 风险趋势（近30天）
            trend_data = get_dashboard_trend_ch(
                end_date - timedelta(days=30),
                end_date,
                fx_rate
            )
            trend_risk = [{'date': d['date'], 'avg_risk_score': d['avg_risk_score']} for d in trend_data]
            trend_exposure = [{'date': d['date'], 'high_risk_exposure': d['high_risk_exposure']} for d in trend_data]

            # 7. 授信使用
            credit_data = get_dashboard_credit_ch(fx_rate)
            credit_usage = {
                'used': credit_data['used_total'],
                'suggested': credit_data['suggested_total']
            }
            credit_top = credit_data['credit_top_list']

            # 8. 风险因子贡献
            risk_factors = get_dashboard_risk_factors_ch(start_date, end_date)

            # 9. 资产总数和高风险资产数
            total_asset_count = sum(row['asset_count'] for row in risk_distribution)
            high_risk_asset_count = sum(
                row['asset_count'] for row in risk_distribution
                if row['risk_level'] == 'high'
            )

            query_time = time.time() - query_start
            print(f"✅ ClickHouse 查询完成，耗时: {query_time:.3f}秒")

            # 构建响应
            response_data = {
                "success": True,
                "data_source": "clickhouse",
                "query_time": f"{query_time:.3f}s",
                "summary": summary,
                "risk_distribution": risk_distribution,
                "high_risk_assets": high_risk_assets,
                "high_risk_company_count": high_risk_company_count,
                "high_risk_vessel_count": high_risk_vessel_count,
                "high_risk_asset_count": high_risk_asset_count,
                "total_asset_count": total_asset_count,
                "npl_stats": npl_stats,
                "company_risk": company_risk,
                "vessel_risk": vessel_risk,
                "vessel_top": vessel_top,
                "trend_risk": trend_risk,
                "trend_exposure": trend_exposure,
                "credit_usage": credit_usage,
                "credit_top": credit_top,
                "risk_factors": risk_factors,
                "currency": currency
            }

            return JSONResponse(response_data)

        else:
            raise Exception("ClickHouse 不可用，降级到 PostgreSQL")

    except Exception as e:
        # ============================================================================
        # PostgreSQL 降级路径（原有逻辑）
        # ============================================================================
        print(f"⚠️ ClickHouse 查询失败: {e}")
        print(f"🔄 降级到 PostgreSQL 查询")
        query_start = time.time()

        # 原有的 PostgreSQL 查询逻辑（保持不变）
        with db_conn(role) as conn:
            fx_rate = get_fx_rate(conn, currency, end_date)

            # Optimized: Combine summary and risk_distribution into single query
            summary_and_distribution = query_all(
                conn,
                """
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
                """,
                (fx_rate, end_date, start_date),
            )

            # Calculate summary from distribution results
            total_exposure = sum(float(row.get("exposure_amount", 0) or 0) for row in summary_and_distribution)
            high_risk_exposure = sum(
                float(row.get("exposure_amount", 0) or 0)
                for row in summary_and_distribution
                if row.get("risk_level") == "high"
            )
            summary = {
                "total_exposure": total_exposure,
                "high_risk_exposure": high_risk_exposure
            }
            risk_distribution = summary_and_distribution

            high_risk_assets = query_all(
                conn,
                """
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
                ORDER BY a.outstanding_amount DESC NULLS LAST
                LIMIT 10
                """,
                (fx_rate, currency),
            )

            npl_stats = query_one(
                conn,
                """
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
                """,
                (fx_rate, end_date, start_date),
            )

            company_risk = query_all(
                conn,
                """
                SELECT risk_level, COUNT(*) AS count
                FROM companies
                WHERE is_active = TRUE
                GROUP BY risk_level
                ORDER BY risk_level
                """,
                (),
            )

            vessel_risk = query_all(
                conn,
                """
                SELECT risk_level, COUNT(*) AS count
                FROM vessels
                WHERE is_active = TRUE
                GROUP BY risk_level
                ORDER BY risk_level
                """,
                (),
            )

            vessel_top = query_all(
                conn,
                """
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
                ORDER BY v.asset_risk_score DESC NULLS LAST
                LIMIT 10
                """,
                (),
            )

            trend_risk = query_all(
                conn,
                """
                SELECT assessment_date AS date, AVG(risk_score) AS avg_risk_score
                FROM vessel_risk_history
                WHERE assessment_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY assessment_date
                ORDER BY assessment_date
                """,
                (),
            )

            trend_exposure = query_all(
                conn,
                """
                SELECT
                    start_date AS date,
                    COALESCE(SUM(outstanding_amount * %s), 0) AS high_risk_exposure
                FROM financial_assets
                WHERE risk_level = 'high'
                  AND start_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY start_date
                ORDER BY start_date
                """,
                (fx_rate,),
            )

            credit_usage_result = query_one(
                conn,
                """
                SELECT COALESCE(SUM(outstanding_amount * %s), 0) AS used_total
                FROM financial_assets
                WHERE is_active = TRUE
                """,
                (fx_rate,),
            )
            used_total = float(credit_usage_result.get("used_total", 0) or 0)
            credit_usage = {
                "used": used_total,
                "suggested": used_total * 1.5
            }

            credit_top = query_all(
                conn,
                """
                SELECT c.company_name, u.used_amount
                FROM (
                    SELECT company_id, SUM(outstanding_amount * %s) AS used_amount
                    FROM financial_assets
                    WHERE is_active = TRUE
                    GROUP BY company_id
                ) u
                LEFT JOIN companies c ON c.id = u.company_id
                ORDER BY u.used_amount DESC NULLS LAST
                LIMIT 5
                """,
                (fx_rate,),
            )

            risk_factors = query_all(
                conn,
                """
                SELECT factor_name,
                       AVG(factor_value) AS avg_value,
                       SUM(contribution) AS total_contribution
                FROM risk_factor_contribution
                WHERE created_at::date BETWEEN %s AND %s
                GROUP BY factor_name
                ORDER BY ABS(SUM(contribution)) DESC NULLS LAST
                LIMIT 5
                """,
                (start_date, end_date),
            )

            high_risk_company_count = query_one(
                conn,
                "SELECT COUNT(*) AS count FROM companies WHERE is_active = TRUE AND risk_level = 'high'",
                (),
            ).get("count", 0)

            high_risk_vessel_count = query_one(
                conn,
                "SELECT COUNT(*) AS count FROM vessels WHERE is_active = TRUE AND risk_level = 'high'",
                (),
            ).get("count", 0)

            total_asset_count = sum(int(row.get("asset_count", 0) or 0) for row in risk_distribution)
            high_risk_asset_count = sum(
                int(row.get("asset_count", 0) or 0)
                for row in risk_distribution
                if row.get("risk_level") == "high"
            )

            query_time = time.time() - query_start
            print(f"✅ PostgreSQL 查询完成，耗时: {query_time:.3f}秒")

            return JSONResponse({
                "success": True,
                "data_source": "postgresql",
                "query_time": f"{query_time:.3f}s",
                "summary": summary,
                "risk_distribution": risk_distribution,
                "high_risk_assets": high_risk_assets,
                "high_risk_company_count": high_risk_company_count,
                "high_risk_vessel_count": high_risk_vessel_count,
                "high_risk_asset_count": high_risk_asset_count,
                "total_asset_count": total_asset_count,
                "npl_stats": npl_stats,
                "company_risk": company_risk,
                "vessel_risk": vessel_risk,
                "vessel_top": vessel_top,
                "trend_risk": trend_risk,
                "trend_exposure": trend_exposure,
                "credit_usage": credit_usage,
                "credit_top": credit_top,
                "risk_factors": risk_factors,
                "currency": currency
            })
