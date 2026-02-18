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

APP_TZ = ZoneInfo("Asia/Shanghai")

app = FastAPI(title="银航宝·深蓝启航")

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


@app.on_event("shutdown")
def on_shutdown() -> None:
    close_pools()


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


def get_risk_factors(conn) -> List[Dict[str, Any]]:
    """获取真实风险因子数据 - 优化版本，限制扫描范围"""
    rows = query_all(
        conn,
        """
        SELECT
            factor_name,
            AVG(factor_value) as avg_value,
            SUM(contribution) as total_contribution
        FROM risk_factor_contribution
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY factor_name
        ORDER BY SUM(ABS(contribution)) DESC
        LIMIT 5
        """,
        (),
    )
    return rows


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/detail", response_class=HTMLResponse)
async def detail(request: Request):
    return templates.TemplateResponse("detail.html", {"request": request})


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
            risk_factors = get_risk_factors(conn)
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


@app.post("/api/dashboard")
async def dashboard_data(request: Request, payload: DashboardQuery):
    session = get_session(request)
    role = "admin" if session.get("root") else "readonly"

    base, currency, start_date, end_date, soon_end, fx_start = dashboard_params(payload)

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

            # Vessel top query - simplified to use vessel table directly for speed
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

            # Trend queries - optimized to 30 days for faster response
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

            # Risk factors query - optimized to 7 days for faster response
            risk_factors = query_all(
                conn,
                """
                SELECT
                    factor_name,
                    AVG(factor_value) as avg_value,
                    SUM(contribution) as total_contribution
                FROM risk_factor_contribution
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY factor_name
                ORDER BY SUM(ABS(contribution)) DESC
                LIMIT 5
                """,
                (),
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
            currency_distribution = get_currency_distribution(conn, fx_rate)

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
        "alerts": {
            "high_risk_company_count": high_risk_company_count.get("count", 0),
            "high_risk_vessel_count": high_risk_vessel_count.get("count", 0),
            "high_risk_assets": high_risk_assets,
            "total_asset_count": asset_stats.get("total_count", 0),
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

    return JSONResponse(response)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
