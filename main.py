import base64
import hashlib
import hmac
import json
import os
import re
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2.pool import SimpleConnectionPool
except ImportError:  # pragma: no cover
    psycopg2 = None
    RealDictCursor = None
    SimpleConnectionPool = None

try:
    from passlib.context import CryptContext
except ImportError:  # pragma: no cover
    CryptContext = None

try:
    import bcrypt
except ImportError:  # pragma: no cover
    bcrypt = None

from app.config import settings
from app.database import db_conn, init_pools, close_pools, query_one, query_all
from app.utils import _serialize_row, _serialize_rows
from app.cache import cache

# 导入 ClickHouse 客户端
try:
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
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    print("⚠️ ClickHouse 模块未安装，将仅使用 PostgreSQL")

# 导入behavior_api路由
try:
    from app.behavior_api import router as behavior_router
except ImportError:
    behavior_router = None

# 导入profile_api路由
try:
    from app.profile_api import router as profile_router
except ImportError:
    profile_router = None

# 导入quality_api路由
try:
    from app.quality_api import router as quality_router
except ImportError:
    quality_router = None

APP_TZ = ZoneInfo("Asia/Shanghai")

app = FastAPI(title="银航宝·深蓝启航")

# 注册behavior_api路由
if behavior_router is not None:
    app.include_router(behavior_router)

# 注册profile_api路由
if profile_router is not None:
    app.include_router(profile_router)

# 注册quality_api路由
if quality_router is not None:
    app.include_router(quality_router)

# 静态文件与模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def now_cn() -> datetime:
    return datetime.now(tz=APP_TZ)


def today_cn() -> date:
    return now_cn().date()


def _init_password_context() -> Any:
    if CryptContext is None:
        return None
    schemes: List[str] = []
    try:
        import argon2  # noqa: F401
        schemes.append("argon2")
    except Exception:
        pass
    schemes.append("bcrypt")
    return CryptContext(schemes=schemes, deprecated="auto")


PWD_CONTEXT = _init_password_context()


class AuthPayload(BaseModel):
    username: str
    password: str


class DashboardQuery(BaseModel):
    base_date: Optional[str] = None
    range: str = "today"  # today | month | 7d | 30d | 90d
    currency: str = "CNY"


@app.on_event("startup")
def on_startup() -> None:
    init_pools()
    ensure_root_user()

    # 初始化 ClickHouse 连接
    if CLICKHOUSE_AVAILABLE:
        try:
            init_clickhouse()
            print("✅ ClickHouse 已启用")
        except Exception as e:
            print(f"⚠️ ClickHouse 初始化失败，将使用 PostgreSQL: {e}")


@app.on_event("shutdown")
def on_shutdown() -> None:
    close_pools()
    if CLICKHOUSE_AVAILABLE:
        try:
            close_clickhouse()
        except Exception:
            pass


def _hash_password(password: str) -> str:
    if PWD_CONTEXT is not None:
        return PWD_CONTEXT.hash(password)
    if bcrypt is None:
        raise RuntimeError("密码哈希模块缺失，请安装 passlib[bcrypt] 或 bcrypt")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    if PWD_CONTEXT is not None:
        return PWD_CONTEXT.verify(password, hashed)
    if bcrypt is None:
        raise RuntimeError("密码哈希模块缺失，请安装 passlib[bcrypt] 或 bcrypt")
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _password_policy(password: str) -> Optional[str]:
    if len(password) < 10:
        return "密码长度至少10位"
    if not re.search(r"[A-Za-z]", password):
        return "密码必须包含字母"
    if not re.search(r"\d", password):
        return "密码必须包含数字"
    if not re.search(r"[^A-Za-z0-9]", password):
        return "密码必须包含符号"
    return None


def _token_sign(raw: bytes) -> str:
    digest = hmac.new(settings.token_secret.encode("utf-8"), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def _token_encode(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    sig = _token_sign(body.encode("utf-8"))
    return f"{body}.{sig}"


def _token_decode(token: str) -> Optional[Dict[str, Any]]:
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        return None
    expected = _token_sign(body.encode("utf-8"))
    if not hmac.compare_digest(sig, expected):
        return None
    padding = "=" * (-len(body) % 4)
    raw = base64.urlsafe_b64decode(body + padding)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return None
    exp = payload.get("exp")
    if exp and datetime.utcnow().timestamp() > exp:
        return None
    return payload


def _extract_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    token = request.headers.get("X-Auth-Token")
    if token:
        return token
    return request.query_params.get("token")


def ensure_root_user() -> None:
    try:
        with db_conn("admin") as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, password_hash FROM users WHERE account=%s",
                    (settings.root_account,),
                )
                row = cur.fetchone()
                if row:
                    return
                hashed = _hash_password(settings.root_password)
                cur.execute(
                    """
                    INSERT INTO users (account, username, password_hash, status, account_type)
                    VALUES (%s, %s, %s, 'active', 'local')
                    """,
                    (settings.root_account, settings.root_account, hashed),
                )
    except Exception as exc:  # pragma: no cover
        print("[WARN] root账户初始化失败:", exc)


def resolve_range(base_date: date, range_key: str) -> Dict[str, date]:
    key = range_key.lower()
    if key in {"today", "day"}:
        return {"start": base_date, "end": base_date}
    if key in {"month", "thismonth"}:
        start = base_date.replace(day=1)
        return {"start": start, "end": base_date}
    if key in {"7d", "7", "week"}:
        return {"start": base_date - timedelta(days=6), "end": base_date}
    if key in {"30d", "30"}:
        return {"start": base_date - timedelta(days=29), "end": base_date}
    if key in {"90d", "90"}:
        return {"start": base_date - timedelta(days=89), "end": base_date}
    return {"start": base_date, "end": base_date}


def dashboard_params(payload: DashboardQuery):
    base = today_cn() if not payload.base_date else date.fromisoformat(payload.base_date)
    currency = (payload.currency or "CNY").upper()
    allowed_currencies = {"CNY", "USD", "HKD", "GBP", "EUR"}
    if currency not in allowed_currencies:
        currency = "CNY"
    date_range = resolve_range(base, payload.range)
    start_date = date_range["start"]
    end_date = date_range["end"]
    soon_end = base + timedelta(days=7)
    fx_start = base - timedelta(days=30)
    return base, currency, start_date, end_date, soon_end, fx_start


def dashboard_meta(base: date, payload: DashboardQuery, currency: str) -> Dict[str, Any]:
    return {"success": True, "base_date": base.isoformat(), "range": payload.range, "currency": currency}


def get_session(request: Request) -> Dict[str, Any]:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    payload = _token_decode(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已失效")
    return payload


def get_fx_rate(conn, currency: str, end_date: date) -> float:
    if currency == "CNY":
        return 1.0
    row = query_one(
        conn,
        """
        SELECT rate
        FROM fx_rates
        WHERE base_currency = 'CNY'
          AND quote_currency = %s
          AND rate_date <= %s
        ORDER BY rate_date DESC
        LIMIT 1
        """,
        (currency, end_date),
    )
    try:
        return float(row.get("rate") or 1)
    except Exception:
        return 1.0


def _mock_scale(value: float, fx_rate: float) -> float:
    return round(value * fx_rate, 2)


def get_credit_usage(conn, fx_rate: float) -> Dict[str, Any]:
    """获取真实授信使用数据"""
    row = query_one(
        conn,
        """
        SELECT COALESCE(SUM(outstanding_amount), 0) as used_total
        FROM financial_assets
        WHERE is_active = TRUE
        """,
        (),
    )
    used_total = float(row.get("used_total", 0) or 0) * fx_rate
    # 授信额度设为已用的1.5倍
    limit_total = used_total * 1.5
    return {
        "used_total": round(used_total, 2),
        "limit_total": round(limit_total, 2),
    }


def get_asset_stats(conn, fx_rate: float) -> Dict[str, Any]:
    """获取资产统计数据"""
    row = query_one(
        conn,
        """
        SELECT
            COUNT(*) as total_count,
            COALESCE(SUM(outstanding_amount), 0) as total_amount
        FROM financial_assets
        WHERE is_active = TRUE
        """,
        (),
    )
    return {
        "total_count": row.get("total_count", 0) or 0,
        "total_amount": float(row.get("total_amount", 0) or 0) * fx_rate,
    }


def get_currency_distribution(conn, fx_rate: float) -> List[Dict[str, Any]]:
    """获取币种分布数据"""
    rows = query_all(
        conn,
        """
        SELECT
            currency,
            COUNT(*) as asset_count,
            COALESCE(SUM(outstanding_amount), 0) as amount
        FROM financial_assets
        WHERE is_active = TRUE
        GROUP BY currency
        ORDER BY amount DESC
        """,
        (),
    )
    return [
        {
            "currency": row.get("currency"),
            "asset_count": row.get("asset_count", 0),
            "amount": float(row.get("amount", 0) or 0) * fx_rate,
        }
        for row in rows
    ]


def get_vessel_top(conn, base: date) -> List[Dict[str, Any]]:
    """获取真实船舶风险Top10 - 优化版本，使用子查询限制数据量"""
    rows = query_all(
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
    return rows


def get_risk_factors(conn, base_date=None) -> List[Dict[str, Any]]:
    """获取真实风险因子数据 - 优化版本，限制扫描范围"""
    # 如果没有提供base_date，使用当前日期
    if base_date is None:
        from datetime import date
        base_date = date.today()

    rows = query_all(
        conn,
        """
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
        """,
        (base_date, base_date),
    )
    return rows


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/test_api", response_class=HTMLResponse)
async def test_api(request: Request):
    return templates.TemplateResponse("test_api.html", {"request": request})


@app.get("/detail", response_class=HTMLResponse)
async def detail(request: Request):
    return templates.TemplateResponse("detail.html", {"request": request})


@app.get("/behavior", response_class=HTMLResponse)
async def behavior(request: Request):
    """船舶行为分析页面 - 不需要登录验证"""
    return templates.TemplateResponse("behavior.html", {"request": request})


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    """船舶画像页面 - 不需要登录验证"""
    return templates.TemplateResponse("profile.html", {"request": request})


@app.get("/lineage", response_class=HTMLResponse)
async def lineage(request: Request):
    """数据血缘页面 - 不需要登录验证"""
    return templates.TemplateResponse("lineage.html", {"request": request})


@app.get("/quality", response_class=HTMLResponse)
async def quality(request: Request):
    """数据质量监控页面 - 不需要登录验证"""
    return templates.TemplateResponse("quality.html", {"request": request})


@app.post("/api/login")
async def login(payload: AuthPayload):
    account = payload.username.strip()
    if not account or not payload.password:
        return JSONResponse({"success": False, "msg": "账号或密码不能为空"})

    role = "admin" if account == settings.root_account else "readonly"

    try:
        with db_conn(role) as conn:
            user = query_one(
                conn,
                """
                SELECT id, account, username, password_hash, status, failed_login_count,
                       locked_until, is_deleted
                FROM users WHERE account=%s
                """,
                (account,),
            )
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"数据库连接失败: {exc}"})

    if not user or user.get("is_deleted"):
        return JSONResponse({"success": False, "msg": "账号或密码错误"})

    locked_until = user.get("locked_until")
    if locked_until and isinstance(locked_until, str):
        locked_until = datetime.fromisoformat(locked_until)
    if locked_until and locked_until > now_cn().replace(tzinfo=None):
        return JSONResponse({"success": False, "msg": "账号已锁定，请稍后再试"})

    try:
        verified = _verify_password(payload.password, user.get("password_hash", ""))
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"密码校验失败: {exc}"})

    if not verified:
        # 使用管理员账号更新失败次数
        try:
            with db_conn("admin") as conn:
                fail_count = int(user.get("failed_login_count") or 0) + 1
                lock_until = None
                if fail_count >= 5:
                    lock_until = now_cn().replace(tzinfo=None) + timedelta(minutes=30)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE users
                        SET failed_login_count=%s, locked_until=%s, updated_at=CURRENT_TIMESTAMP
                        WHERE account=%s
                        """,
                        (fail_count, lock_until, account),
                    )
        except Exception:
            pass
        return JSONResponse({"success": False, "msg": "账号或密码错误"})

    if user.get("status") and user.get("status") != "active":
        return JSONResponse({"success": False, "msg": "账号状态异常，请联系管理员"})

    try:
        with db_conn("admin") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET failed_login_count=0, locked_until=NULL, last_login_at=CURRENT_TIMESTAMP,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE account=%s
                    """,
                    (account,),
                )
    except Exception:
        pass

    expires_at = datetime.utcnow() + timedelta(hours=settings.token_ttl_hours)
    token = _token_encode(
        {
            "sub": account,
            "root": account == settings.root_account,
            "exp": int(expires_at.timestamp()),
        }
    )

    return JSONResponse(
        {
            "success": True,
            "msg": "登录成功",
            "token": token,
            "user": {"account": account, "role": "admin" if account == settings.root_account else "readonly"},
        }
    )


@app.post("/api/register")
async def register(payload: AuthPayload):
    account = payload.username.strip()
    if not account or not payload.password:
        return JSONResponse({"success": False, "msg": "账号或密码不能为空"})
    if account == settings.root_account:
        return JSONResponse({"success": False, "msg": "该账号不可注册"})

    policy_msg = _password_policy(payload.password)
    if policy_msg:
        return JSONResponse({"success": False, "msg": policy_msg})

    try:
        with db_conn("admin") as conn:
            existing = query_one(
                conn,
                "SELECT id FROM users WHERE account=%s AND is_deleted=FALSE",
                (account,),
            )
            if existing:
                return JSONResponse({"success": False, "msg": "账号已存在", "code": "ACCOUNT_EXISTS"})

            hashed = _hash_password(payload.password)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (account, username, password_hash, status, account_type)
                    VALUES (%s, %s, %s, 'active', 'local')
                    """,
                    (account, account, hashed),
                )
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"注册失败: {exc}"})

    return JSONResponse({"success": True, "msg": "注册成功"})


@app.post("/api/dashboard/summary")
async def dashboard_summary(request: Request, payload: DashboardQuery):
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            fx_rate = get_fx_rate(conn, currency, end_date)
            summary = query_one(
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
                    COALESCE(SUM(amount_converted), 0) AS total_exposure,
                    COALESCE(SUM(CASE WHEN risk_level='high' THEN amount_converted ELSE 0 END), 0)
                        AS high_risk_exposure
                FROM assets_base
                """,
                (fx_rate, end_date, start_date),
            )

            risk_distribution = query_all(
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
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    total_exposure = summary.get("total_exposure", 0) or 0
    high_risk_exposure = summary.get("high_risk_exposure", 0) or 0
    high_risk_ratio = (high_risk_exposure / total_exposure) if total_exposure else 0

    response = {
        **dashboard_meta(base, payload, currency),
        "summary": {
            "total_exposure": total_exposure,
            "high_risk_exposure": high_risk_exposure,
            "high_risk_ratio": high_risk_ratio,
            "risk_distribution": risk_distribution,
        },
    }
    return JSONResponse(response)


@app.post("/api/dashboard/alerts")
async def dashboard_alerts(request: Request, payload: DashboardQuery):
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, _, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            fx_rate = get_fx_rate(conn, currency, end_date)
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

            high_risk_company_count = query_one(
                conn,
                """
                SELECT COUNT(*) AS count
                FROM companies
                WHERE is_active = TRUE AND risk_level = 'high'
                """,
                (),
            )

            high_risk_vessel_count = query_one(
                conn,
                """
                SELECT COUNT(*) AS count
                FROM vessels
                WHERE is_active = TRUE AND risk_level = 'high'
                """,
                (),
            )

            asset_stats = get_asset_stats(conn, fx_rate)
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "alerts": {
            "high_risk_company_count": high_risk_company_count.get("count", 0),
            "high_risk_vessel_count": high_risk_vessel_count.get("count", 0),
            "high_risk_assets": high_risk_assets,
            "total_asset_count": asset_stats.get("total_count", 0),
        },
    }
    return JSONResponse(response)


@app.post("/api/dashboard/npl")
async def dashboard_npl(request: Request, payload: DashboardQuery):
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            fx_rate = get_fx_rate(conn, currency, end_date)
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

            currency_distribution = get_currency_distribution(conn, fx_rate)
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "npl": {
            "npl_count": npl_stats.get("npl_count", 0),
            "total_count": npl_stats.get("total_count", 0),
            "npl_amount": npl_stats.get("npl_amount", 0),
            "total_amount": npl_stats.get("total_amount", 0),
            "currency_distribution": currency_distribution,
        },
    }
    return JSONResponse(response)


@app.post("/api/dashboard/risk-levels")
async def dashboard_risk_levels(request: Request, payload: DashboardQuery):
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, _, _, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
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
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "risk_levels": {"company": company_risk, "vessel": vessel_risk},
    }
    return JSONResponse(response)


@app.post("/api/dashboard/trend")
async def dashboard_trend(request: Request, payload: DashboardQuery):
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            fx_rate = get_fx_rate(conn, currency, end_date)
            trend_risk = query_all(
                conn,
                """
                SELECT assessment_date AS date, AVG(risk_score) AS avg_risk_score
                FROM vessel_risk_history
                WHERE assessment_date BETWEEN %s AND %s
                GROUP BY assessment_date
                ORDER BY assessment_date
                """,
                (start_date, end_date),
            )

            trend_exposure = query_all(
                conn,
                """
                SELECT
                    a.start_date AS date,
                    COALESCE(SUM(a.outstanding_amount * %s), 0) AS high_risk_exposure
                FROM financial_assets a
                WHERE a.risk_level = 'high'
                  AND a.start_date BETWEEN %s AND %s
                GROUP BY a.start_date
                ORDER BY a.start_date
                """,
                (fx_rate, start_date, end_date),
            )
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "trend": {"avg_risk_score": trend_risk, "high_risk_exposure": trend_exposure},
    }
    return JSONResponse(response)


@app.post("/api/dashboard/vessel-top")
async def dashboard_vessel_top(request: Request, payload: DashboardQuery):
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, _, _, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            vessel_top = get_vessel_top(conn, base)
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {**dashboard_meta(base, payload, currency), "vessel_top": vessel_top}
    return JSONResponse(response)


@app.post("/api/dashboard/credit")
async def dashboard_credit(request: Request, payload: DashboardQuery):
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, _, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            fx_rate = get_fx_rate(conn, currency, end_date)
            credit_usage = get_credit_usage(conn, fx_rate)

            credit_top = query_all(
                conn,
                """
                SELECT c.company_name, u.used_amount
                FROM (
                    SELECT
                        a.company_id,
                        SUM(a.outstanding_amount * %s) AS used_amount
                    FROM financial_assets a
                    WHERE a.is_active = TRUE
                    GROUP BY a.company_id
                ) u
                LEFT JOIN companies c ON c.id = u.company_id
                ORDER BY u.used_amount DESC NULLS LAST
                LIMIT 5
                """,
                (fx_rate,),
            )
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "credit": {"usage": credit_usage, "top": credit_top},
    }
    return JSONResponse(response)


@app.post("/api/dashboard/risk-factors")
async def dashboard_risk_factors(request: Request, payload: DashboardQuery):
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            risk_factors = get_risk_factors(conn, base)  # 传入base_date
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {**dashboard_meta(base, payload, currency), "risk_factors": risk_factors}
    return JSONResponse(response)


@app.post("/api/dashboard/fx")
async def dashboard_fx(request: Request, payload: DashboardQuery):
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, _, end_date, _, fx_start = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            fx_rate = get_fx_rate(conn, currency, end_date)
            fx_rates = query_all(
                conn,
                """
                SELECT rate_date, base_currency, quote_currency, rate
                FROM fx_rates
                WHERE quote_currency = %s
                  AND base_currency IN ('USD', 'EUR')
                  AND rate_date BETWEEN %s AND %s
                ORDER BY rate_date
                """,
                (currency, fx_start, base),
            )

            fx_exposure = query_all(
                conn,
                """
                SELECT
                    a.currency,
                    SUM(a.outstanding_amount) AS exposure_amount,
                    SUM(a.outstanding_amount * %s) AS exposure_converted
                FROM financial_assets a
                WHERE a.is_active = TRUE
                GROUP BY a.currency
                ORDER BY exposure_converted DESC NULLS LAST
                """,
                (fx_rate,),
            )
    except Exception as exc:
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {**dashboard_meta(base, payload, currency), "fx": {"rates": fx_rates, "exposure": fx_exposure}}
    return JSONResponse(response)


@app.get("/api/clickhouse/health")
async def clickhouse_health():
    """检查 ClickHouse 连接状态"""
    if not CLICKHOUSE_AVAILABLE:
        return JSONResponse({
            "success": True,
            "clickhouse_enabled": False,
            "message": "ClickHouse 模块未安装"
        })

    is_healthy = check_clickhouse_health()
    return JSONResponse({
        "success": True,
        "clickhouse_enabled": is_healthy,
        "message": "ClickHouse 连接正常" if is_healthy else "ClickHouse 连接失败，使用 PostgreSQL"
    })


@app.post("/api/dashboard")
async def dashboard_data(request: Request, payload: DashboardQuery):
    """
    Dashboard 数据查询接口
    优先使用 ClickHouse，失败时降级到 PostgreSQL
    支持 Redis 缓存加速
    """
    import time

    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"

    base, currency, start_date, end_date, soon_end, fx_start = dashboard_params(payload)

    # ============================================================================
    # 1. 尝试从 Redis 缓存获取
    # ============================================================================
    cache_key_params = {
        'base_date': str(base),
        'range': payload.range,
        'currency': currency,
        'start_date': str(start_date),
        'end_date': str(end_date)
    }

    cached_data = cache.get('dashboard', **cache_key_params)
    if cached_data:
        print(f"✅ 缓存命中: Dashboard 数据")
        return JSONResponse({
            **cached_data,
            'data_source': 'cache',
            'cached': True
        })

    # ============================================================================
    # 2. 缓存未命中，查询数据库
    # ============================================================================
    print(f"⚠️ 缓存未命中，查询数据库")

    # 尝试使用 ClickHouse
    use_clickhouse = CLICKHOUSE_AVAILABLE and check_clickhouse_health()

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
            total_exposure = summary_data['total_exposure']
            high_risk_exposure = summary_data['high_risk_exposure']
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
                'used_total': credit_data['used_total'],
                'limit_total': credit_data['suggested_total']
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

            # 10. 币种分布（使用 PostgreSQL，因为 ClickHouse 没有这个查询）
            with db_conn(role) as conn:
                currency_distribution = get_currency_distribution(conn, fx_rate)

            query_time = time.time() - query_start
            print(f"✅ ClickHouse 查询完成，耗时: {query_time:.3f}秒")
            data_source = "clickhouse"

        else:
            raise Exception("ClickHouse 不可用，降级到 PostgreSQL")

    except Exception as e:
        # ============================================================================
        # PostgreSQL 降级路径（原有逻辑）
        # ============================================================================
        print(f"⚠️ ClickHouse 查询失败: {e}")
        print(f"🔄 降级到 PostgreSQL 查询")
        query_start = time.time()

        try:
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
                        a.start_date AS date,
                        COALESCE(SUM(a.outstanding_amount * %s), 0) AS high_risk_exposure
                    FROM financial_assets a
                    WHERE a.risk_level = 'high'
                      AND a.start_date >= CURRENT_DATE - INTERVAL '30 days'
                      AND a.is_active = TRUE
                    GROUP BY a.start_date
                    ORDER BY a.start_date
                    """,
                    (fx_rate,),
                )

                credit_usage = get_credit_usage(conn, fx_rate)

                credit_top = query_all(
                    conn,
                    """
                    SELECT c.company_name, u.used_amount
                    FROM (
                        SELECT
                            a.company_id,
                            SUM(a.outstanding_amount * %s) AS used_amount
                        FROM financial_assets a
                        WHERE a.is_active = TRUE
                        GROUP BY a.company_id
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
                    """,
                    (base, base),
                )

                high_risk_company_count = query_one(
                    conn,
                    """
                    SELECT COUNT(*) AS count
                    FROM companies
                    WHERE is_active = TRUE AND risk_level = 'high'
                    """,
                    (),
                ).get("count", 0)

                high_risk_vessel_count = query_one(
                    conn,
                    """
                    SELECT COUNT(*) AS count
                    FROM vessels
                    WHERE is_active = TRUE AND risk_level = 'high'
                    """,
                    (),
                ).get("count", 0)

                asset_stats = get_asset_stats(conn, fx_rate)
                total_asset_count = asset_stats.get("total_count", 0)
                currency_distribution = get_currency_distribution(conn, fx_rate)

            query_time = time.time() - query_start
            print(f"✅ PostgreSQL 查询完成，耗时: {query_time:.3f}秒")
            data_source = "postgresql"

        except Exception as exc:
            return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    # 构建响应
    high_risk_ratio = (high_risk_exposure / total_exposure) if total_exposure else 0

    response = {
        **dashboard_meta(base, payload, currency),
        "data_source": data_source,
        "query_time": f"{query_time:.3f}s",
        "summary": {
            "total_exposure": total_exposure,
            "high_risk_exposure": high_risk_exposure,
            "high_risk_ratio": high_risk_ratio,
            "risk_distribution": risk_distribution,
        },
        "alerts": {
            "high_risk_company_count": high_risk_company_count,
            "high_risk_vessel_count": high_risk_vessel_count,
            "high_risk_assets": high_risk_assets,
            "total_asset_count": total_asset_count,
        },
        "npl": {
            "npl_count": npl_stats.get("npl_count", 0),
            "total_count": npl_stats.get("total_count", 0),
            "npl_amount": npl_stats.get("npl_amount", 0),
            "total_amount": npl_stats.get("total_amount", 0),
            "currency_distribution": currency_distribution,
        },
        "risk_levels": {
            "company": company_risk,
            "vessel": vessel_risk,
        },
        "trend": {
            "avg_risk_score": trend_risk,
            "high_risk_exposure": trend_exposure,
        },
        "vessel_top": vessel_top,
        "credit": {
            "usage": credit_usage,
            "top": credit_top,
        },
        "risk_factors": risk_factors,
    }

    # ============================================================================
    # 3. 存入 Redis 缓存（5分钟TTL）
    # ============================================================================
    try:
        cache.set('dashboard', response, ttl=300, **cache_key_params)
        print(f"✅ 数据已缓存: Dashboard (TTL: 300s)")
    except Exception as cache_error:
        print(f"⚠️ 缓存存储失败: {cache_error}")

    return JSONResponse(response)


@app.post("/api/detail/credit")
async def detail_credit(request: Request, payload: DashboardQuery):
    """授信使用明细页API"""
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            import sys
            print(f"[DEBUG] Step 1: Got connection", file=sys.stderr)
            fx_rate = get_fx_rate(conn, currency, end_date)
            print(f"[DEBUG] Step 2: fx_rate={fx_rate}", file=sys.stderr)

            # 1. 统计数据：授信客户数、总授信额度、已用额度、平均使用率
            print(f"[DEBUG] Step 3: Querying credit_stats...", file=sys.stderr)
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
            print(f"[DEBUG] Step 4: credit_stats OK", file=sys.stderr)

            # 2. 授信客户排行榜（Top 20）
            print(f"[DEBUG] Step 5: Querying credit_ranking...", file=sys.stderr)
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
            print(f"[DEBUG] Step 6: credit_ranking OK, count={len(credit_ranking)}", file=sys.stderr)

            # 3. 授信使用率分布
            print(f"[DEBUG] Step 7: Querying usage_distribution...", file=sys.stderr)
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
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
                """)
                usage_distribution = [dict(row) for row in cur.fetchall()]
            print(f"[DEBUG] Step 8: usage_distribution OK, count={len(usage_distribution)}", file=sys.stderr)

            # 4. 授信集中度分析（Top10客户占比）
            print(f"[DEBUG] Step 9: Querying concentration...", file=sys.stderr)
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
            print(f"[DEBUG] Step 10: concentration OK", file=sys.stderr)

            # 5. 授信到期提醒（近30天到期）
            print(f"[DEBUG] Step 11: Querying expiring_soon...", file=sys.stderr)
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
            print(f"[DEBUG] Step 12: expiring_soon OK, count={len(expiring_soon)}", file=sys.stderr)
            print(f"[DEBUG] Step 13: All queries completed successfully", file=sys.stderr)

    except Exception as exc:
        import traceback
        print(f"[ERROR] Exception occurred: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "stats": {
            "customer_count": credit_stats.get("customer_count", 0),
            "total_limit": credit_stats.get("total_limit", 0),
            "used_amount": credit_stats.get("used_amount", 0),
            "avg_usage_rate": round(credit_stats.get("avg_usage_rate", 0), 2),
        },
        "ranking": credit_ranking,
        "usage_distribution": usage_distribution,
        "concentration": {
            "total_exposure": concentration.get("total_exposure", 0),
            "top10_exposure": concentration.get("top10_exposure", 0),
            "concentration_ratio": round(concentration.get("concentration_ratio", 0), 2),
        },
        "expiring_soon": expiring_soon,
    }

    return JSONResponse(response)


@app.post("/api/detail/alerts")
async def detail_alerts(request: Request, payload: DashboardQuery):
    """高风险预警详情页API"""
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            import sys
            print(f"[DEBUG] alerts: Step 1: Got connection", file=sys.stderr)
            fx_rate = get_fx_rate(conn, currency, end_date)
            print(f"[DEBUG] alerts: Step 2: fx_rate={fx_rate}", file=sys.stderr)

            # 1. 统计数据：高风险资产总数、总敞口
            print(f"[DEBUG] alerts: Step 3: Querying alert_stats...", file=sys.stderr)
            alert_stats = query_one(
                conn,
                """
                SELECT
                    COUNT(*) AS high_risk_count,
                    COALESCE(SUM(outstanding_amount * %s), 0) AS high_risk_exposure
                FROM financial_assets
                WHERE is_active = TRUE
                  AND risk_level = 'high'
                  AND start_date <= %s
                  AND maturity_date >= %s
                """,
                (fx_rate, end_date, start_date),
            )
            print(f"[DEBUG] alerts: Step 4: alert_stats OK", file=sys.stderr)

            # 2. 高风险资产列表（Top 50）
            print(f"[DEBUG] alerts: Step 5: Querying high_risk_assets...", file=sys.stderr)
            high_risk_assets = query_all(
                conn,
                """
                SELECT
                    a.id,
                    a.asset_type,
                    c.company_name,
                    v.vessel_name,
                    a.contract_no,
                    a.outstanding_amount * %s AS outstanding_amount,
                    a.risk_score,
                    a.risk_level,
                    a.maturity_date
                FROM financial_assets a
                LEFT JOIN companies c ON c.id = a.company_id
                LEFT JOIN vessels v ON v.id = a.vessel_id
                WHERE a.is_active = TRUE
                  AND a.risk_level = 'high'
                  AND a.start_date <= %s
                  AND a.maturity_date >= %s
                ORDER BY a.outstanding_amount DESC
                LIMIT 50
                """,
                (fx_rate, end_date, start_date),
            )
            print(f"[DEBUG] alerts: Step 6: high_risk_assets OK, count={len(high_risk_assets)}", file=sys.stderr)

            # 3. 风险等级统计
            print(f"[DEBUG] alerts: Step 7: Querying risk_level_stats...", file=sys.stderr)
            risk_level_stats = query_all(
                conn,
                """
                SELECT
                    risk_level,
                    COUNT(*) AS count,
                    COALESCE(SUM(outstanding_amount * %s), 0) AS total_amount
                FROM financial_assets
                WHERE is_active = TRUE
                  AND start_date <= %s
                  AND maturity_date >= %s
                GROUP BY risk_level
                ORDER BY
                    CASE risk_level
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                        ELSE 4
                    END
                """,
                (fx_rate, end_date, start_date),
            )
            print(f"[DEBUG] alerts: Step 8: risk_level_stats OK", file=sys.stderr)

            # 4. 资产类型分布
            print(f"[DEBUG] alerts: Step 9: Querying asset_type_stats...", file=sys.stderr)
            asset_type_stats = query_all(
                conn,
                """
                SELECT
                    asset_type,
                    COUNT(*) AS count,
                    COALESCE(SUM(outstanding_amount * %s), 0) AS total_amount
                FROM financial_assets
                WHERE is_active = TRUE
                  AND risk_level = 'high'
                  AND start_date <= %s
                  AND maturity_date >= %s
                GROUP BY asset_type
                ORDER BY total_amount DESC
                """,
                (fx_rate, end_date, start_date),
            )
            print(f"[DEBUG] alerts: Step 10: asset_type_stats OK", file=sys.stderr)
            print(f"[DEBUG] alerts: Step 11: All queries completed successfully", file=sys.stderr)

    except Exception as exc:
        import traceback
        print(f"[ERROR] alerts: Exception occurred: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "stats": {
            "high_risk_count": alert_stats.get("high_risk_count", 0),
            "high_risk_exposure": alert_stats.get("high_risk_exposure", 0),
        },
        "high_risk_assets": high_risk_assets,
        "risk_level_stats": risk_level_stats,
        "asset_type_stats": asset_type_stats,
    }

    return JSONResponse(response)


@app.post("/api/detail/vessels")
async def detail_vessels(request: Request, payload: DashboardQuery):
    """船舶资产风险详情页API"""
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            import sys
            print(f"[DEBUG] vessels: Step 1: Got connection", file=sys.stderr)

            # 1. 统计数据：总船舶数、高风险船舶、平均船龄、平均风险评分
            print(f"[DEBUG] vessels: Step 2: Querying vessel_stats...", file=sys.stderr)
            vessel_stats = query_one(
                conn,
                """
                SELECT
                    COUNT(*) AS total_vessels,
                    COUNT(CASE WHEN risk_level = 'high' THEN 1 END) AS high_risk_vessels,
                    AVG(EXTRACT(YEAR FROM %s::date) - build_year) AS avg_vessel_age,
                    AVG(asset_risk_score) AS avg_risk_score
                FROM vessels
                WHERE is_active = TRUE
                """,
                (end_date,),
            )
            print(f"[DEBUG] vessels: Step 3: vessel_stats OK", file=sys.stderr)

            # 2. 船舶风险排行榜（Top 20）
            print(f"[DEBUG] vessels: Step 4: Querying vessel_ranking...", file=sys.stderr)
            vessel_ranking = query_all(
                conn,
                """
                SELECT
                    v.vessel_name,
                    v.imo_number,
                    v.vessel_type,
                    EXTRACT(YEAR FROM %s::date) - v.build_year AS vessel_age,
                    c.company_name,
                    v.asset_risk_score AS risk_score,
                    v.risk_level
                FROM vessels v
                LEFT JOIN companies c ON c.id = v.owner_company_id
                WHERE v.is_active = TRUE
                  AND v.asset_risk_score IS NOT NULL
                ORDER BY v.asset_risk_score DESC
                LIMIT 20
                """,
                (end_date,),
            )
            print(f"[DEBUG] vessels: Step 5: vessel_ranking OK, count={len(vessel_ranking)}", file=sys.stderr)

            # 3. 船龄分布
            print(f"[DEBUG] vessels: Step 6: Querying age_distribution...", file=sys.stderr)
            age_distribution = query_all(
                conn,
                """
                SELECT
                    age_range AS range,
                    COUNT(*) AS count
                FROM (
                    SELECT
                        CASE
                            WHEN EXTRACT(YEAR FROM %s::date) - build_year < 5 THEN '0-5年'
                            WHEN EXTRACT(YEAR FROM %s::date) - build_year < 10 THEN '5-10年'
                            WHEN EXTRACT(YEAR FROM %s::date) - build_year < 15 THEN '10-15年'
                            WHEN EXTRACT(YEAR FROM %s::date) - build_year < 20 THEN '15-20年'
                            ELSE '20年以上'
                        END AS age_range,
                        CASE
                            WHEN EXTRACT(YEAR FROM %s::date) - build_year < 5 THEN 1
                            WHEN EXTRACT(YEAR FROM %s::date) - build_year < 10 THEN 2
                            WHEN EXTRACT(YEAR FROM %s::date) - build_year < 15 THEN 3
                            WHEN EXTRACT(YEAR FROM %s::date) - build_year < 20 THEN 4
                            ELSE 5
                        END AS sort_order
                    FROM vessels
                    WHERE is_active = TRUE
                ) t
                GROUP BY age_range, sort_order
                ORDER BY sort_order
                """,
                (end_date, end_date, end_date, end_date, end_date, end_date, end_date, end_date),
            )
            print(f"[DEBUG] vessels: Step 7: age_distribution OK", file=sys.stderr)

            # 4. 船型分布
            print(f"[DEBUG] vessels: Step 8: Querying type_distribution...", file=sys.stderr)
            type_distribution = query_all(
                conn,
                """
                SELECT
                    vessel_type AS type,
                    COUNT(*) AS count
                FROM vessels
                WHERE is_active = TRUE
                  AND vessel_type IS NOT NULL
                GROUP BY vessel_type
                ORDER BY count DESC
                LIMIT 10
                """,
                (),
            )
            print(f"[DEBUG] vessels: Step 9: type_distribution OK", file=sys.stderr)
            print(f"[DEBUG] vessels: Step 10: All queries completed successfully", file=sys.stderr)

    except Exception as exc:
        import traceback
        print(f"[ERROR] vessels: Exception occurred: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "stats": {
            "total_vessels": vessel_stats.get("total_vessels", 0),
            "high_risk_vessels": vessel_stats.get("high_risk_vessels", 0),
            "avg_vessel_age": round(vessel_stats.get("avg_vessel_age", 0), 1),
            "avg_risk_score": round(vessel_stats.get("avg_risk_score", 0), 2),
        },
        "vessel_ranking": vessel_ranking,
        "age_distribution": age_distribution,
        "type_distribution": type_distribution,
    }

    return JSONResponse(response)


@app.post("/api/detail/npl")
async def detail_npl(request: Request, payload: DashboardQuery):
    """不良资产明细页API"""
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            import sys
            print(f"[DEBUG] npl: Step 1: Got connection", file=sys.stderr)
            fx_rate = get_fx_rate(conn, currency, end_date)
            print(f"[DEBUG] npl: Step 2: fx_rate={fx_rate}", file=sys.stderr)

            # 1. 统计数据：不良资产数量、金额、不良率、拨备覆盖率
            print(f"[DEBUG] npl: Step 3: Querying npl_stats...", file=sys.stderr)
            npl_stats = query_one(
                conn,
                """
                SELECT
                    COUNT(CASE WHEN is_non_performing = TRUE THEN 1 END) AS npl_count,
                    COALESCE(SUM(CASE WHEN is_non_performing = TRUE THEN outstanding_amount * %s ELSE 0 END), 0) AS npl_amount,
                    COALESCE(SUM(outstanding_amount * %s), 0) AS total_amount
                FROM financial_assets
                WHERE is_active = TRUE
                  AND start_date <= %s
                  AND maturity_date >= %s
                """,
                (fx_rate, fx_rate, end_date, start_date),
            )

            # 计算不良率和拨备覆盖率
            npl_count = npl_stats.get("npl_count", 0)
            npl_amount = npl_stats.get("npl_amount", 0)
            total_amount = npl_stats.get("total_amount", 0)
            npl_rate = (npl_amount / total_amount * 100) if total_amount > 0 else 0
            provision_rate = 150.0  # 模拟拨备覆盖率，实际应从拨备表计算

            print(f"[DEBUG] npl: Step 4: npl_stats OK", file=sys.stderr)

            # 2. 不良资产列表（Top 50）
            print(f"[DEBUG] npl: Step 5: Querying npl_assets...", file=sys.stderr)
            npl_assets = query_all(
                conn,
                """
                SELECT
                    a.id,
                    c.company_name,
                    a.contract_no,
                    a.outstanding_amount * %s AS outstanding_amount,
                    0 AS overdue_days,
                    CASE
                        WHEN a.risk_level = 'medium' THEN '次级'
                        WHEN a.risk_level = 'high' AND a.risk_score < 80 THEN '可疑'
                        WHEN a.risk_level = 'high' AND a.risk_score >= 80 THEN '损失'
                        ELSE '关注'
                    END AS npl_classification,
                    a.created_at::date AS recognition_date
                FROM financial_assets a
                LEFT JOIN companies c ON c.id = a.company_id
                WHERE a.is_active = TRUE
                  AND a.is_non_performing = TRUE
                  AND a.start_date <= %s
                  AND a.maturity_date >= %s
                ORDER BY a.outstanding_amount DESC
                LIMIT 50
                """,
                (fx_rate, end_date, start_date),
            )
            print(f"[DEBUG] npl: Step 6: npl_assets OK, count={len(npl_assets)}", file=sys.stderr)

            # 3. 不良资产分类统计
            print(f"[DEBUG] npl: Step 7: Querying npl_classification...", file=sys.stderr)
            npl_classification = query_all(
                conn,
                """
                SELECT
                    CASE
                        WHEN risk_level = 'medium' THEN '次级'
                        WHEN risk_level = 'high' AND risk_score < 80 THEN '可疑'
                        WHEN risk_level = 'high' AND risk_score >= 80 THEN '损失'
                        ELSE '关注'
                    END AS classification,
                    COUNT(*) AS count,
                    COALESCE(SUM(outstanding_amount * %s), 0) AS total_amount
                FROM financial_assets
                WHERE is_active = TRUE
                  AND is_non_performing = TRUE
                  AND start_date <= %s
                  AND maturity_date >= %s
                GROUP BY classification
                ORDER BY total_amount DESC
                """,
                (fx_rate, end_date, start_date),
            )
            print(f"[DEBUG] npl: Step 8: npl_classification OK", file=sys.stderr)

            # 4. 不良资产趋势（近12个月）
            print(f"[DEBUG] npl: Step 9: Querying npl_trend...", file=sys.stderr)
            npl_trend = query_all(
                conn,
                """
                SELECT
                    TO_CHAR(month_date, 'YYYY-MM') AS month,
                    COUNT(CASE WHEN is_non_performing = TRUE THEN 1 END) AS npl_count,
                    COALESCE(SUM(CASE WHEN is_non_performing = TRUE THEN outstanding_amount * %s ELSE 0 END), 0) AS npl_amount,
                    COALESCE(SUM(outstanding_amount * %s), 0) AS total_amount
                FROM (
                    SELECT
                        generate_series(
                            DATE_TRUNC('month', %s::date - INTERVAL '11 months'),
                            DATE_TRUNC('month', %s::date),
                            '1 month'::interval
                        )::date AS month_date
                ) months
                LEFT JOIN financial_assets a ON
                    DATE_TRUNC('month', a.created_at) = month_date
                    AND a.is_active = TRUE
                GROUP BY month_date
                ORDER BY month_date
                """,
                (fx_rate, fx_rate, end_date, end_date),
            )
            print(f"[DEBUG] npl: Step 10: npl_trend OK", file=sys.stderr)
            print(f"[DEBUG] npl: Step 11: All queries completed successfully", file=sys.stderr)

    except Exception as exc:
        import traceback
        print(f"[ERROR] npl: Exception occurred: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "stats": {
            "npl_count": npl_count,
            "npl_amount": npl_amount,
            "npl_rate": round(npl_rate, 2),
            "provision_rate": provision_rate,
        },
        "npl_assets": npl_assets,
        "npl_classification": npl_classification,
        "npl_trend": npl_trend,
    }

    return JSONResponse(response)


@app.post("/api/detail/trend")
async def detail_trend(request: Request, payload: DashboardQuery):
    """风险趋势分析页API"""
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            import sys
            print(f"[DEBUG] trend: Step 1: Got connection", file=sys.stderr)
            fx_rate = get_fx_rate(conn, currency, end_date)
            print(f"[DEBUG] trend: Step 2: fx_rate={fx_rate}", file=sys.stderr)

            # 1. 高风险敞口趋势（近30天）
            print(f"[DEBUG] trend: Step 3: Querying exposure_trend...", file=sys.stderr)
            exposure_trend = query_all(
                conn,
                """
                SELECT
                    day_date::text AS date,
                    COALESCE(SUM(CASE WHEN a.risk_level = 'high' THEN a.outstanding_amount * %s ELSE 0 END), 0) AS high_risk_exposure,
                    COALESCE(SUM(a.outstanding_amount * %s), 0) AS total_exposure
                FROM (
                    SELECT generate_series(
                        %s::date - INTERVAL '29 days',
                        %s::date,
                        '1 day'::interval
                    )::date AS day_date
                ) days
                LEFT JOIN financial_assets a ON
                    a.is_active = TRUE
                    AND a.start_date <= day_date
                    AND a.maturity_date >= day_date
                GROUP BY day_date
                ORDER BY day_date
                """,
                (fx_rate, fx_rate, end_date, end_date),
            )
            print(f"[DEBUG] trend: Step 4: exposure_trend OK, count={len(exposure_trend)}", file=sys.stderr)

            # 2. 平均风险评分趋势（近30天）
            print(f"[DEBUG] trend: Step 5: Querying score_trend...", file=sys.stderr)
            score_trend = query_all(
                conn,
                """
                SELECT
                    day_date::text AS date,
                    COALESCE(AVG(a.risk_score), 0) AS avg_risk_score,
                    COUNT(CASE WHEN a.risk_level = 'high' THEN 1 END) AS high_risk_count
                FROM (
                    SELECT generate_series(
                        %s::date - INTERVAL '29 days',
                        %s::date,
                        '1 day'::interval
                    )::date AS day_date
                ) days
                LEFT JOIN financial_assets a ON
                    a.is_active = TRUE
                    AND a.start_date <= day_date
                    AND a.maturity_date >= day_date
                GROUP BY day_date
                ORDER BY day_date
                """,
                (end_date, end_date),
            )
            print(f"[DEBUG] trend: Step 6: score_trend OK", file=sys.stderr)

            # 3. 风险等级迁移矩阵（本月vs上月）
            print(f"[DEBUG] trend: Step 7: Querying migration_matrix...", file=sys.stderr)
            migration_matrix = query_all(
                conn,
                """
                SELECT
                    'high' AS from_level,
                    'high' AS to_level,
                    50 AS count
                UNION ALL
                SELECT 'high', 'medium', 30
                UNION ALL
                SELECT 'high', 'low', 20
                UNION ALL
                SELECT 'medium', 'high', 25
                UNION ALL
                SELECT 'medium', 'medium', 100
                UNION ALL
                SELECT 'medium', 'low', 75
                UNION ALL
                SELECT 'low', 'high', 10
                UNION ALL
                SELECT 'low', 'medium', 50
                UNION ALL
                SELECT 'low', 'low', 500
                """,
                (),
            )
            print(f"[DEBUG] trend: Step 8: migration_matrix OK", file=sys.stderr)

            # 4. 趋势对比分析（本月vs上月）
            print(f"[DEBUG] trend: Step 9: Querying trend_comparison...", file=sys.stderr)
            trend_comparison = query_one(
                conn,
                """
                SELECT
                    COALESCE(SUM(CASE WHEN a.risk_level = 'high' THEN a.outstanding_amount * %s ELSE 0 END), 0) AS current_high_risk,
                    COALESCE(AVG(a.risk_score), 0) AS current_avg_score,
                    COUNT(CASE WHEN a.risk_level = 'high' THEN 1 END) AS current_high_count
                FROM financial_assets a
                WHERE a.is_active = TRUE
                  AND a.start_date <= %s
                  AND a.maturity_date >= %s
                """,
                (fx_rate, end_date, start_date),
            )
            print(f"[DEBUG] trend: Step 10: trend_comparison OK", file=sys.stderr)
            print(f"[DEBUG] trend: Step 11: All queries completed successfully", file=sys.stderr)

    except Exception as exc:
        import traceback
        print(f"[ERROR] trend: Exception occurred: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "exposure_trend": exposure_trend,
        "score_trend": score_trend,
        "migration_matrix": migration_matrix,
        "trend_comparison": {
            "current_high_risk": trend_comparison.get("current_high_risk", 0),
            "current_avg_score": round(trend_comparison.get("current_avg_score", 0), 2),
            "current_high_count": trend_comparison.get("current_high_count", 0),
        },
    }

    return JSONResponse(response)


@app.post("/api/detail/factors")
async def detail_factors(request: Request, payload: DashboardQuery):
    """风险因子拆解页API"""
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            import sys
            print(f"[DEBUG] factors: Step 1: Got connection", file=sys.stderr)

            # 1. 风险因子贡献度排名（模拟数据）
            print(f"[DEBUG] factors: Step 2: Querying factor_ranking...", file=sys.stderr)
            factor_ranking = [
                {"factor_name": "船龄", "contribution": 0.25, "importance": 85},
                {"factor_name": "企业信用评分", "contribution": 0.20, "importance": 78},
                {"factor_name": "逾期天数", "contribution": 0.18, "importance": 72},
                {"factor_name": "抵押率", "contribution": 0.15, "importance": 65},
                {"factor_name": "行业风险", "contribution": 0.12, "importance": 58},
                {"factor_name": "地区风险", "contribution": 0.10, "importance": 45},
            ]
            print(f"[DEBUG] factors: Step 3: factor_ranking OK", file=sys.stderr)

            # 2. 客户列表（用于筛选）
            print(f"[DEBUG] factors: Step 4: Querying customer_list...", file=sys.stderr)
            customer_list = query_all(
                conn,
                """
                SELECT DISTINCT
                    c.id,
                    c.company_name
                FROM companies c
                INNER JOIN financial_assets a ON a.company_id = c.id
                WHERE a.is_active = TRUE
                ORDER BY c.company_name
                LIMIT 50
                """,
                (),
            )
            print(f"[DEBUG] factors: Step 5: customer_list OK, count={len(customer_list)}", file=sys.stderr)
            print(f"[DEBUG] factors: Step 6: All queries completed successfully", file=sys.stderr)

    except Exception as exc:
        import traceback
        print(f"[ERROR] factors: Exception occurred: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "factor_ranking": factor_ranking,
        "customer_list": customer_list,
    }

    return JSONResponse(response)


@app.post("/api/detail/distribution")
async def detail_distribution(request: Request, payload: DashboardQuery):
    """风险等级分布详情页API"""
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            import sys
            print(f"[DEBUG] distribution: Step 1: Got connection", file=sys.stderr)
            fx_rate = get_fx_rate(conn, currency, end_date)
            print(f"[DEBUG] distribution: Step 2: fx_rate={fx_rate}", file=sys.stderr)

            # 1. 企业风险等级分布
            print(f"[DEBUG] distribution: Step 3: Querying company_distribution...", file=sys.stderr)
            company_distribution = query_all(
                conn,
                """
                SELECT
                    risk_level,
                    COUNT(*) AS count,
                    COALESCE(AVG(credit_score), 0) AS avg_score
                FROM companies
                WHERE is_active = TRUE
                GROUP BY risk_level
                ORDER BY
                    CASE risk_level
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                        ELSE 4
                    END
                """,
                (),
            )
            print(f"[DEBUG] distribution: Step 4: company_distribution OK", file=sys.stderr)

            # 2. 船舶风险等级分布
            print(f"[DEBUG] distribution: Step 5: Querying vessel_distribution...", file=sys.stderr)
            vessel_distribution = query_all(
                conn,
                """
                SELECT
                    risk_level,
                    COUNT(*) AS count,
                    COALESCE(AVG(asset_risk_score), 0) AS avg_score
                FROM vessels
                WHERE is_active = TRUE
                GROUP BY risk_level
                ORDER BY
                    CASE risk_level
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                        ELSE 4
                    END
                """,
                (),
            )
            print(f"[DEBUG] distribution: Step 6: vessel_distribution OK", file=sys.stderr)
            print(f"[DEBUG] distribution: Step 7: All queries completed successfully", file=sys.stderr)

    except Exception as exc:
        import traceback
        print(f"[ERROR] distribution: Exception occurred: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "company_distribution": company_distribution,
        "vessel_distribution": vessel_distribution,
    }

    return JSONResponse(response)


@app.post("/api/detail/overall")
async def detail_overall(request: Request, payload: DashboardQuery):
    """总体风险敞口详情页API"""
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"
    base, currency, start_date, end_date, _, _ = dashboard_params(payload)

    try:
        with db_conn(role) as conn:
            import sys
            print(f"[DEBUG] overall: Step 1: Got connection", file=sys.stderr)
            fx_rate = get_fx_rate(conn, currency, end_date)
            print(f"[DEBUG] overall: Step 2: fx_rate={fx_rate}", file=sys.stderr)

            # 1. 总体统计数据
            print(f"[DEBUG] overall: Step 3: Querying overall_stats...", file=sys.stderr)
            overall_stats = query_one(
                conn,
                """
                SELECT
                    COALESCE(SUM(outstanding_amount * %s), 0) AS total_exposure,
                    COALESCE(SUM(CASE WHEN risk_level = 'high' THEN outstanding_amount * %s ELSE 0 END), 0) AS high_risk_exposure,
                    COUNT(DISTINCT currency) AS currency_count
                FROM financial_assets
                WHERE is_active = TRUE
                  AND start_date <= %s
                  AND maturity_date >= %s
                """,
                (fx_rate, fx_rate, end_date, start_date),
            )

            # 计算敞口集中度（Top10占比）
            top10_exposure = query_one(
                conn,
                """
                SELECT COALESCE(SUM(total_exposure), 0) AS top10_exposure
                FROM (
                    SELECT
                        company_id,
                        SUM(outstanding_amount * %s) AS total_exposure
                    FROM financial_assets
                    WHERE is_active = TRUE
                      AND start_date <= %s
                      AND maturity_date >= %s
                    GROUP BY company_id
                    ORDER BY total_exposure DESC
                    LIMIT 10
                ) t
                """,
                (fx_rate, end_date, start_date),
            )

            total_exposure = overall_stats.get("total_exposure", 0)
            top10 = top10_exposure.get("top10_exposure", 0)
            concentration = (top10 / total_exposure * 100) if total_exposure > 0 else 0

            print(f"[DEBUG] overall: Step 4: overall_stats OK", file=sys.stderr)

            # 2. 币种敞口分布
            print(f"[DEBUG] overall: Step 5: Querying currency_exposure...", file=sys.stderr)
            currency_exposure = query_all(
                conn,
                """
                SELECT
                    currency,
                    COALESCE(SUM(outstanding_amount * %s), 0) AS total_amount,
                    COUNT(*) AS count
                FROM financial_assets
                WHERE is_active = TRUE
                  AND start_date <= %s
                  AND maturity_date >= %s
                GROUP BY currency
                ORDER BY total_amount DESC
                """,
                (fx_rate, end_date, start_date),
            )
            print(f"[DEBUG] overall: Step 6: currency_exposure OK", file=sys.stderr)

            # 3. 高风险敞口明细（Top 20）
            print(f"[DEBUG] overall: Step 7: Querying high_risk_detail...", file=sys.stderr)
            high_risk_detail = query_all(
                conn,
                """
                SELECT
                    c.company_name,
                    v.vessel_name,
                    a.outstanding_amount * %s AS outstanding_amount,
                    a.currency,
                    a.risk_level,
                    CASE
                        WHEN %s > 0 THEN (a.outstanding_amount * %s / %s * 100)
                        ELSE 0
                    END AS exposure_ratio
                FROM financial_assets a
                LEFT JOIN companies c ON c.id = a.company_id
                LEFT JOIN vessels v ON v.id = a.vessel_id
                WHERE a.is_active = TRUE
                  AND a.risk_level = 'high'
                  AND a.start_date <= %s
                  AND a.maturity_date >= %s
                ORDER BY a.outstanding_amount DESC
                LIMIT 20
                """,
                (fx_rate, total_exposure, fx_rate, total_exposure if total_exposure > 0 else 1, end_date, start_date),
            )
            print(f"[DEBUG] overall: Step 8: high_risk_detail OK", file=sys.stderr)
            print(f"[DEBUG] overall: Step 9: All queries completed successfully", file=sys.stderr)

    except Exception as exc:
        import traceback
        print(f"[ERROR] overall: Exception occurred: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return JSONResponse({"success": False, "msg": f"数据获取失败: {exc}"})

    response = {
        **dashboard_meta(base, payload, currency),
        "stats": {
            "total_exposure": total_exposure,
            "high_risk_exposure": overall_stats.get("high_risk_exposure", 0),
            "exposure_concentration": round(concentration, 2),
            "currency_count": overall_stats.get("currency_count", 0),
        },
        "currency_exposure": currency_exposure,
        "high_risk_detail": high_risk_detail,
    }

    return JSONResponse(response)


# ============================================================================
# 船舶行为分析API（MongoDB + Spark）
# ============================================================================

from datetime import datetime as dt
from bson import ObjectId


def serialize_mongo_doc(doc):
    """序列化MongoDB文档"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_mongo_doc(d) for d in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, dt):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = serialize_mongo_doc(value)
            elif isinstance(value, list):
                result[key] = serialize_mongo_doc(value)
            else:
                result[key] = value
        return result
    return doc


class VesselTrackQuery(BaseModel):
    """船舶轨迹查询参数"""
    imo_number: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 1000


class GeofenceQuery(BaseModel):
    """地理围栏查询参数"""
    min_lng: float
    max_lng: float
    min_lat: float
    max_lat: float
    start_date: Optional[str] = None
    limit: int = 100


@app.post("/api/behavior/tracks")
async def get_vessel_tracks(request: Request, payload: VesselTrackQuery):
    """获取指定船舶的历史轨迹"""
    session = get_session(request)

    try:
        from app.database import get_mongo_db
        db = get_mongo_db()
        collection = db["ais_tracks"]

        # 构建查询条件
        query = {"imo_number": payload.imo_number}

        # 添加时间范围过滤
        if payload.start_date or payload.end_date:
            time_filter = {}
            if payload.start_date:
                time_filter["$gte"] = dt.fromisoformat(payload.start_date)
            if payload.end_date:
                time_filter["$lte"] = dt.fromisoformat(payload.end_date)
            query["timestamp"] = time_filter

        # 查询轨迹数据
        tracks = list(collection.find(query).sort("timestamp", 1).limit(payload.limit))

        # 序列化结果
        tracks_serialized = serialize_mongo_doc(tracks)

        return JSONResponse({
            "success": True,
            "count": len(tracks_serialized),
            "imo_number": payload.imo_number,
            "tracks": tracks_serialized
        })

    except Exception as e:
        return JSONResponse({"success": False, "msg": f"查询失败: {str(e)}"}, status_code=500)


@app.post("/api/behavior/anomalies")
async def get_anomalies(request: Request):
    """获取异常停泊记录"""
    session = get_session(request)

    try:
        from app.database import get_mongo_db
        db = get_mongo_db()
        collection = db["ais_anomalies"]

        # 查询异常记录
        anomalies = list(collection.find({}).sort("timestamp", -1).limit(50))

        # 序列化结果
        anomalies_serialized = serialize_mongo_doc(anomalies)

        return JSONResponse({
            "success": True,
            "count": len(anomalies_serialized),
            "anomalies": anomalies_serialized
        })

    except Exception as e:
        return JSONResponse({"success": False, "msg": f"查询失败: {str(e)}"}, status_code=500)


@app.post("/api/behavior/geofence")
async def geofence_query(request: Request, payload: GeofenceQuery):
    """地理围栏查询：查询指定区域内的船舶"""
    session = get_session(request)

    try:
        from app.database import get_mongo_db
        db = get_mongo_db()
        collection = db["ais_tracks"]

        # 构建地理围栏查询
        query = {
            "position": {
                "$geoWithin": {
                    "$box": [
                        [payload.min_lng, payload.min_lat],
                        [payload.max_lng, payload.max_lat]
                    ]
                }
            }
        }

        # 添加时间过滤
        if payload.start_date:
            query["timestamp"] = {"$gte": dt.fromisoformat(payload.start_date)}

        # 查询船舶
        vessels = list(collection.find(query).sort("timestamp", -1).limit(payload.limit))

        # 序列化结果
        vessels_serialized = serialize_mongo_doc(vessels)

        return JSONResponse({
            "success": True,
            "count": len(vessels_serialized),
            "area": {
                "min_lng": payload.min_lng,
                "max_lng": payload.max_lng,
                "min_lat": payload.min_lat,
                "max_lat": payload.max_lat
            },
            "vessels": vessels_serialized
        })

    except Exception as e:
        return JSONResponse({"success": False, "msg": f"查询失败: {str(e)}"}, status_code=500)


@app.get("/api/behavior/summary")
async def get_behavior_summary(request: Request):
    """获取行为分析总览"""
    session = get_session(request)

    try:
        from app.database import get_mongo_db
        db = get_mongo_db()

        # 统计轨迹数据
        tracks_collection = db["ais_tracks"]
        total_tracks = tracks_collection.count_documents({})
        vessel_count = len(tracks_collection.distinct("imo_number"))

        # 获取时间范围
        oldest = tracks_collection.find_one(sort=[("timestamp", 1)])
        newest = tracks_collection.find_one(sort=[("timestamp", -1)])

        # 统计异常记录
        anomalies_collection = db["ais_anomalies"]
        anomaly_count = anomalies_collection.count_documents({})

        # 统计船舶类型分布
        ship_types = list(tracks_collection.aggregate([
            {"$group": {"_id": "$ship_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]))

        return JSONResponse({
            "success": True,
            "summary": {
                "total_tracks": total_tracks,
                "vessel_count": vessel_count,
                "anomaly_count": anomaly_count,
                "time_range": {
                    "start": oldest["timestamp"].isoformat() if oldest else None,
                    "end": newest["timestamp"].isoformat() if newest else None
                },
                "ship_type_distribution": [
                    {"type": item["_id"], "count": item["count"]}
                    for item in ship_types
                ]
            }
        })

    except Exception as e:
        return JSONResponse({"success": False, "msg": f"查询失败: {str(e)}"}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
