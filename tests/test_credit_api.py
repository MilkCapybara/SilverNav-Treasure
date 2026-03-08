#!/usr/bin/env python3
"""测试授信详情API的所有SQL查询"""
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

from app.database import init_pools, db_conn, query_one, query_all
from datetime import date, timedelta

# 初始化连接池
init_pools()

# 模拟API参数
currency = "CNY"
end_date = date.today()
start_date = end_date - timedelta(days=30)
fx_rate = 1.0

print("=" * 60)
print("测试授信详情API的所有SQL查询")
print("=" * 60)

try:
    with db_conn("admin") as conn:
        # 1. 测试授信统计查询
        print("\n[1/5] 测试授信统计查询...")
        credit_stats = query_one(
            conn,
            """
            WITH credit_data AS (
                SELECT
                    a.company_id,
                    SUM(a.principal_amount * %s) AS total_limit,
                    SUM(a.outstanding_amount * %s) AS used_amount
                FROM financial_assets a
                WHERE a.is_active = TRUE
                  AND a.start_date <= %s
                  AND a.maturity_date >= %s
                GROUP BY a.company_id
            )
            SELECT
                COUNT(DISTINCT company_id) AS customer_count,
                COALESCE(SUM(total_limit), 0) AS total_limit,
                COALESCE(SUM(used_amount), 0) AS used_amount,
                CASE
                    WHEN SUM(total_limit) > 0
                    THEN (SUM(used_amount) / SUM(total_limit)) * 100
                    ELSE 0
                END AS avg_usage_rate
            FROM credit_data
            """,
            (fx_rate, fx_rate, end_date, start_date),
        )
        print(f"✓ 授信客户数: {credit_stats.get('customer_count', 0)}")
        print(f"✓ 总授信额度: {credit_stats.get('total_limit', 0):,.2f}")
        print(f"✓ 已用额度: {credit_stats.get('used_amount', 0):,.2f}")
        print(f"✓ 平均使用率: {credit_stats.get('avg_usage_rate', 0):.2f}%")

        # 2. 测试授信客户排行榜
        print("\n[2/5] 测试授信客户排行榜...")
        credit_ranking = query_all(
            conn,
            """
            SELECT
                c.company_name,
                c.risk_level,
                SUM(a.principal_amount * %s) AS credit_limit,
                SUM(a.outstanding_amount * %s) AS used_amount,
                CASE
                    WHEN SUM(a.principal_amount) > 0
                    THEN (SUM(a.outstanding_amount) / SUM(a.principal_amount)) * 100
                    ELSE 0
                END AS usage_rate
            FROM financial_assets a
            LEFT JOIN companies c ON c.id = a.company_id
            WHERE a.is_active = TRUE
              AND a.start_date <= %s
              AND a.maturity_date >= %s
            GROUP BY c.id, c.company_name, c.risk_level
            ORDER BY used_amount DESC
            LIMIT 20
            """,
            (fx_rate, fx_rate, end_date, start_date),
        )
        print(f"✓ 返回 {len(credit_ranking)} 条记录")
        if credit_ranking:
            print(f"✓ Top 1: {credit_ranking[0]['company_name']} - 已用额度: {credit_ranking[0]['used_amount']:,.2f}")

        # 3. 测试授信使用率分布
        print("\n[3/5] 测试授信使用率分布...")
        usage_distribution = query_all(
            conn,
            """
            WITH credit_usage AS (
                SELECT
                    a.company_id,
                    CASE
                        WHEN SUM(a.principal_amount) > 0
                        THEN (SUM(a.outstanding_amount) / SUM(a.principal_amount)) * 100
                        ELSE 0
                    END AS usage_rate
                FROM financial_assets a
                WHERE a.is_active = TRUE
                GROUP BY a.company_id
            )
            SELECT
                CASE
                    WHEN usage_rate < 50 THEN '0-50%'
                    WHEN usage_rate < 80 THEN '50-80%'
                    WHEN usage_rate < 100 THEN '80-100%'
                    ELSE '>100%'
                END AS range,
                COUNT(*) AS count
            FROM credit_usage
            GROUP BY
                CASE
                    WHEN usage_rate < 50 THEN '0-50%'
                    WHEN usage_rate < 80 THEN '50-80%'
                    WHEN usage_rate < 100 THEN '80-100%'
                    ELSE '>100%'
                END
            ORDER BY range
            """,
            (),
        )
        print(f"✓ 使用率分布:")
        for item in usage_distribution:
            print(f"  - {item['range']}: {item['count']} 家企业")

        # 4. 测试授信集中度分析
        print("\n[4/5] 测试授信集中度分析...")
        concentration = query_one(
            conn,
            """
            WITH total_credit AS (
                SELECT SUM(a.outstanding_amount * %s) AS total
                FROM financial_assets a
                WHERE a.is_active = TRUE
            ),
            top10_credit AS (
                SELECT SUM(used_amount) AS top10_total
                FROM (
                    SELECT
                        a.company_id,
                        SUM(a.outstanding_amount * %s) AS used_amount
                    FROM financial_assets a
                    WHERE a.is_active = TRUE
                    GROUP BY a.company_id
                    ORDER BY used_amount DESC
                    LIMIT 10
                ) t
            )
            SELECT
                COALESCE(tc.total, 0) AS total_exposure,
                COALESCE(t10.top10_total, 0) AS top10_exposure,
                CASE
                    WHEN tc.total > 0
                    THEN (t10.top10_total / tc.total) * 100
                    ELSE 0
                END AS concentration_ratio
            FROM total_credit tc, top10_credit t10
            """,
            (fx_rate, fx_rate),
        )
        print(f"✓ 总敞口: {concentration.get('total_exposure', 0):,.2f}")
        print(f"✓ Top10敞口: {concentration.get('top10_exposure', 0):,.2f}")
        print(f"✓ 集中度: {concentration.get('concentration_ratio', 0):.2f}%")

        # 5. 测试授信到期提醒
        print("\n[5/5] 测试授信到期提醒...")
        expiring_soon = query_all(
            conn,
            """
            SELECT
                c.company_name,
                a.contract_no,
                a.outstanding_amount * %s AS outstanding_amount,
                a.maturity_date,
                a.maturity_date - CURRENT_DATE AS days_to_maturity,
                a.risk_level
            FROM financial_assets a
            LEFT JOIN companies c ON c.id = a.company_id
            WHERE a.is_active = TRUE
              AND a.maturity_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
            ORDER BY a.maturity_date ASC
            LIMIT 20
            """,
            (fx_rate,),
        )
        print(f"✓ 近30天到期: {len(expiring_soon)} 条记录")
        if expiring_soon:
            print(f"✓ 最近到期: {expiring_soon[0]['company_name']} - {expiring_soon[0]['days_to_maturity']}天后")

        print("\n" + "=" * 60)
        print("✅ 所有SQL查询测试成功！")
        print("=" * 60)

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
