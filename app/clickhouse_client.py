"""
ClickHouse 客户端模块
用途：封装 ClickHouse 连接和查询方法，提供 Dashboard 查询接口
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime
from decimal import Decimal

try:
    import clickhouse_connect
    from clickhouse_connect.driver import Client
except ImportError:
    clickhouse_connect = None
    Client = None

from .config import settings


# ============================================================================
# 全局 ClickHouse 客户端
# ============================================================================

CH_CLIENT: Optional[Client] = None


def init_clickhouse() -> None:
    """初始化 ClickHouse 连接"""
    global CH_CLIENT

    if clickhouse_connect is None:
        raise RuntimeError("clickhouse-connect 未安装，请运行: pip install clickhouse-connect")

    try:
        # 从环境变量或配置读取 ClickHouse 配置
        ch_host = settings.db_host  # 使用相同的服务器
        ch_port = 8123  # HTTP 接口端口
        ch_user = 'default'
        ch_password = 'sun2137405'
        ch_database = 'silvernav'

        CH_CLIENT = clickhouse_connect.get_client(
            host=ch_host,
            port=ch_port,
            username=ch_user,
            password=ch_password,
            database=ch_database
        )

        # 测试连接
        CH_CLIENT.query('SELECT 1')
        print(f"✅ ClickHouse 连接成功: {ch_host}:{ch_port}/{ch_database} (HTTP)")

    except Exception as e:
        print(f"❌ ClickHouse 连接失败: {e}")
        CH_CLIENT = None
        raise


def get_clickhouse_client() -> Optional[Client]:
    """获取 ClickHouse 客户端"""
    if CH_CLIENT is None:
        try:
            init_clickhouse()
        except Exception:
            return None
    return CH_CLIENT


def close_clickhouse() -> None:
    """关闭 ClickHouse 连接"""
    global CH_CLIENT
    if CH_CLIENT:
        CH_CLIENT.close()
        CH_CLIENT = None


# ============================================================================
# 查询辅助函数
# ============================================================================

def serialize_ch_value(value: Any) -> Any:
    """序列化 ClickHouse 返回值"""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def serialize_ch_row(row: tuple, columns: List[str]) -> Dict[str, Any]:
    """将 ClickHouse 行转换为字典"""
    return {col: serialize_ch_value(val) for col, val in zip(columns, row)}


def serialize_ch_rows(rows: List[tuple], columns: List[str]) -> List[Dict[str, Any]]:
    """将 ClickHouse 结果集转换为字典列表"""
    return [serialize_ch_row(row, columns) for row in rows]


# ============================================================================
# Dashboard 查询函数
# ============================================================================

def get_fx_rate_ch(currency: str, end_date: date) -> float:
    """获取汇率（ClickHouse 版本）"""
    if currency == 'CNY':
        return 1.0

    client = get_clickhouse_client()
    if not client:
        return 1.0

    try:
        result = client.query("""
            SELECT rate
            FROM fx_rates FINAL
            WHERE base_currency = 'CNY'
              AND quote_currency = {currency:String}
              AND rate_date <= {end_date:Date}
            ORDER BY rate_date DESC
            LIMIT 1
        """, parameters={'currency': currency, 'end_date': end_date})

        if result.result_rows and len(result.result_rows) > 0:
            return float(result.result_rows[0][0])
        return 1.0
    except Exception as e:
        print(f"⚠️ ClickHouse 汇率查询失败: {e}")
        return 1.0


def get_dashboard_summary_ch(
    start_date: date,
    end_date: date,
    fx_rate: float
) -> Dict[str, Any]:
    """
    获取 Dashboard 总体风险敞口（ClickHouse 版本）
    对应 PostgreSQL 查询：dashboard_queries.sql 指标1
    """
    client = get_clickhouse_client()
    if not client:
        raise RuntimeError("ClickHouse 客户端未初始化")

    # 查询总敞口和风险分布
    result = client.query("""
        SELECT
            risk_level,
            count() AS asset_count,
            sum(outstanding_amount * {fx_rate:Float64}) AS exposure_amount
        FROM financial_assets FINAL
        WHERE is_active = 1
          AND start_date <= {end_date:Date}
          AND maturity_date >= {start_date:Date}
        GROUP BY risk_level
    """, parameters={
        'start_date': start_date,
        'end_date': end_date,
        'fx_rate': fx_rate
    })

    # 处理结果
    total_exposure = 0.0
    high_risk_exposure = 0.0
    risk_distribution = []

    for row in result.result_rows:
        risk_level, asset_count, exposure_amount = row
        exposure_amount = float(exposure_amount) if exposure_amount else 0.0

        total_exposure += exposure_amount
        if risk_level == 'high':
            high_risk_exposure = exposure_amount

        risk_distribution.append({
            'risk_level': risk_level,
            'asset_count': int(asset_count),
            'exposure_amount': exposure_amount
        })

    return {
        'total_exposure': total_exposure,
        'high_risk_exposure': high_risk_exposure,
        'risk_distribution': risk_distribution
    }


def get_dashboard_alerts_ch(fx_rate: float) -> Dict[str, Any]:
    """
    获取高风险预警数据（ClickHouse 版本）
    对应 PostgreSQL 查询：dashboard_queries.sql 指标2
    """
    client = get_clickhouse_client()
    if not client:
        raise RuntimeError("ClickHouse 客户端未初始化")

    # 高风险企业数量
    high_risk_companies = client.query("""
        SELECT count() FROM companies FINAL
        WHERE is_active = 1 AND risk_level = 'high'
    """).result_rows[0][0]

    # 高风险船舶数量
    high_risk_vessels = client.query("""
        SELECT count() FROM vessels FINAL
        WHERE is_active = 1 AND risk_level = 'high'
    """).result_rows[0][0]

    # 高风险资产 Top10
    top_assets = client.query("""
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
    """, {'fx_rate': fx_rate})

    alert_list = []
    for row in top_assets.result_rows:
        contract_no, company_name, vessel_name, outstanding_amount, risk_score = row
        alert_list.append({
            'contract_no': contract_no or '',
            'company_name': company_name or '',
            'vessel_name': vessel_name or '',
            'outstanding_amount': float(outstanding_amount) if outstanding_amount else 0.0,
            'risk_score': float(risk_score) if risk_score else 0.0
        })

    return {
        'high_risk_company_count': int(high_risk_companies),
        'high_risk_vessel_count': int(high_risk_vessels),
        'alert_list': alert_list
    }


def get_dashboard_npl_ch(
    start_date: date,
    end_date: date,
    fx_rate: float
) -> Dict[str, Any]:
    """
    获取不良资产监控数据（ClickHouse 版本）
    对应 PostgreSQL 查询：dashboard_queries.sql 指标3
    """
    client = get_clickhouse_client()
    if not client:
        raise RuntimeError("ClickHouse 客户端未初始化")

    result = client.query("""
        SELECT
            countIf(is_non_performing = 1) AS npl_count,
            count() AS total_count,
            sumIf(outstanding_amount * {fx_rate:Float64}, is_non_performing = 1) AS npl_amount,
            sum(outstanding_amount * {fx_rate:Float64}) AS total_amount
        FROM financial_assets FINAL
        WHERE is_active = 1
          AND start_date <= {end_date:Date}
          AND maturity_date >= {start_date:Date}
    """, {
        'start_date': start_date,
        'end_date': end_date,
        'fx_rate': fx_rate
    })

    npl_count, total_count, npl_amount, total_amount = result.result_rows[0]

    return {
        'npl_count': int(npl_count),
        'total_count': int(total_count),
        'npl_amount': float(npl_amount) if npl_amount else 0.0,
        'total_amount': float(total_amount) if total_amount else 0.0
    }


def get_dashboard_risk_levels_ch() -> Dict[str, Any]:
    """
    获取风险等级分布（ClickHouse 版本）
    对应 PostgreSQL 查询：dashboard_queries.sql 指标4
    """
    client = get_clickhouse_client()
    if not client:
        raise RuntimeError("ClickHouse 客户端未初始化")

    # 企业风险分布
    company_dist = client.query("""
        SELECT risk_level, count() AS count
        FROM companies FINAL
        WHERE is_active = 1
        GROUP BY risk_level
        ORDER BY risk_level
    """)

    # 船舶风险分布
    vessel_dist = client.query("""
        SELECT risk_level, count() AS count
        FROM vessels FINAL
        WHERE is_active = 1
        GROUP BY risk_level
        ORDER BY risk_level
    """)

    return {
        'company_distribution': [
            {'risk_level': row[0], 'count': int(row[1])}
            for row in company_dist.result_rows
        ],
        'vessel_distribution': [
            {'risk_level': row[0], 'count': int(row[1])}
            for row in vessel_dist.result_rows
        ]
    }


def get_dashboard_trend_ch(
    start_date: date,
    end_date: date,
    fx_rate: float
) -> List[Dict[str, Any]]:
    """
    获取风险趋势数据（ClickHouse 版本）
    对应 PostgreSQL 查询：dashboard_queries.sql 指标5
    """
    client = get_clickhouse_client()
    if not client:
        raise RuntimeError("ClickHouse 客户端未初始化")

    # 平均风险评分趋势
    score_trend = client.query("""
        SELECT assessment_date, avg(risk_score) AS avg_risk_score
        FROM vessel_risk_history
        WHERE assessment_date BETWEEN {start_date:Date} AND {end_date:Date}
        GROUP BY assessment_date
        ORDER BY assessment_date
    """, {'start_date': start_date, 'end_date': end_date})

    # 高风险敞口走势
    exposure_trend = client.query("""
        SELECT
            start_date AS date,
            sum(outstanding_amount * {fx_rate:Float64}) AS high_risk_exposure
        FROM financial_assets FINAL
        WHERE risk_level = 'high'
          AND start_date BETWEEN {start_date:Date} AND {end_date:Date}
        GROUP BY start_date
        ORDER BY start_date
    """, {
        'start_date': start_date,
        'end_date': end_date,
        'fx_rate': fx_rate
    })

    # 合并结果
    trend_data = {}

    for row in score_trend.result_rows:
        date_val, avg_score = row
        trend_data[date_val] = {
            'date': date_val.isoformat(),
            'avg_risk_score': float(avg_score) if avg_score else 0.0,
            'high_risk_exposure': 0.0
        }

    for row in exposure_trend.result_rows:
        date_val, exposure = row
        if date_val in trend_data:
            trend_data[date_val]['high_risk_exposure'] = float(exposure) if exposure else 0.0
        else:
            trend_data[date_val] = {
                'date': date_val.isoformat(),
                'avg_risk_score': 0.0,
                'high_risk_exposure': float(exposure) if exposure else 0.0
            }

    return sorted(trend_data.values(), key=lambda x: x['date'])


def get_dashboard_vessel_top_ch() -> List[Dict[str, Any]]:
    """
    获取船舶风险 Top10（ClickHouse 版本）
    对应 PostgreSQL 查询：dashboard_queries.sql 指标7
    """
    client = get_clickhouse_client()
    if not client:
        raise RuntimeError("ClickHouse 客户端未初始化")

    result = client.query("""
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
    """)

    return [
        {
            'vessel_name': row[0] or '',
            'imo_number': row[1] or '',
            'company_name': row[2] or '',
            'risk_score': float(row[3]) if row[3] else 0.0,
            'risk_level': row[4] or ''
        }
        for row in result.result_rows
    ]


def get_dashboard_credit_ch(fx_rate: float) -> Dict[str, Any]:
    """
    获取授信使用数据（ClickHouse 版本）
    对应 PostgreSQL 查询：dashboard_queries.sql 指标6
    """
    client = get_clickhouse_client()
    if not client:
        raise RuntimeError("ClickHouse 客户端未初始化")

    # 授信使用总额
    used_total = client.query("""
        SELECT sum(outstanding_amount * {fx_rate:Float64})
        FROM financial_assets FINAL
        WHERE is_active = 1
    """, {'fx_rate': fx_rate}).result_rows[0][0]

    used_total = float(used_total) if used_total else 0.0

    # 授信使用 Top5 客户
    top_customers = client.query("""
        SELECT c.company_name, sum(a.outstanding_amount * {fx_rate:Float64}) AS used_amount
        FROM (SELECT * FROM financial_assets FINAL) AS a
        LEFT JOIN (SELECT * FROM companies FINAL) AS c ON c.id = a.company_id
        WHERE a.is_active = 1
        GROUP BY c.company_name
        ORDER BY used_amount DESC
        LIMIT 5
    """, {'fx_rate': fx_rate})

    credit_top_list = [
        {
            'company_name': row[0] or '',
            'used_amount': float(row[1]) if row[1] else 0.0
        }
        for row in top_customers.result_rows
    ]

    return {
        'used_total': used_total,
        'suggested_total': used_total * 1.5,  # 模拟建议授信额度
        'credit_top_list': credit_top_list
    }


def get_dashboard_risk_factors_ch(
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """
    获取风险因子贡献 Top5（ClickHouse 版本）
    对应 PostgreSQL 查询：dashboard_queries.sql 指标8

    注意：为了和PostgreSQL版本保持一致，使用固定的30天范围
    查询范围：end_date - 30天 到 end_date
    """
    from datetime import timedelta

    client = get_clickhouse_client()
    if not client:
        raise RuntimeError("ClickHouse 客户端未初始化")

    # 使用固定的30天范围，和PostgreSQL版本保持一致
    query_start = end_date - timedelta(days=30)
    query_end = end_date

    result = client.query("""
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
    """, {'start_date': query_start, 'end_date': query_end})

    return [
        {
            'factor_name': row[0],
            'avg_value': float(row[1]) if row[1] else 0.0,
            'total_contribution': float(row[2]) if row[2] else 0.0
        }
        for row in result.result_rows
    ]


# ============================================================================
# 健康检查
# ============================================================================

def check_clickhouse_health() -> bool:
    """检查 ClickHouse 连接健康状态"""
    try:
        client = get_clickhouse_client()
        if not client:
            return False

        result = client.query('SELECT 1')
        return result.result_rows[0][0] == 1
    except Exception:
        return False
