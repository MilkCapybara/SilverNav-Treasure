"""数据库连接模块"""
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2.pool import SimpleConnectionPool
except ImportError:
    psycopg2 = None
    RealDictCursor = None
    SimpleConnectionPool = None

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
except ImportError:
    MongoClient = None
    ConnectionFailure = None

from .config import settings


ADMIN_POOL: Optional["SimpleConnectionPool"] = None
READ_POOL: Optional["SimpleConnectionPool"] = None
MONGO_CLIENT: Optional["MongoClient"] = None
MONGO_CLIENT: Optional[MongoClient] = None


def _require_db() -> None:
    """检查数据库驱动是否已安装"""
    if psycopg2 is None or RealDictCursor is None or SimpleConnectionPool is None:
        raise RuntimeError(
            "数据库驱动未安装，请安装 psycopg2-binary 后再启动服务。"
        )


@contextmanager
def db_conn(role: str):
    """数据库连接上下文管理器"""
    _require_db()
    pool = ADMIN_POOL if role == "admin" else READ_POOL
    if pool is None:
        raise RuntimeError("数据库连接池尚未初始化")
    conn = pool.getconn()
    try:
        # 测试连接是否有效
        with conn.cursor() as test_cur:
            test_cur.execute("SELECT 1")
        yield conn
        conn.commit()
    except psycopg2.OperationalError as e:
        # 连接已关闭，尝试重新获取
        print(f"⚠️ 数据库连接已关闭，尝试重新连接: {e}")
        pool.putconn(conn, close=True)
        conn = pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.putconn(conn)
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def init_pools() -> None:
    """初始化数据库连接池"""
    global ADMIN_POOL, READ_POOL
    _require_db()
    # 增加超时设置和连接保活参数
    base_options = (
        f"-c search_path={settings.db_schema} "
        f"-c statement_timeout=60000 "  # 增加到60秒
        f"-c idle_in_transaction_session_timeout=120000"  # 空闲事务超时2分钟
    )
    ADMIN_POOL = SimpleConnectionPool(
        2,  # 增加最小连接数
        10,  # 增加最大连接数
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.admin_user,
        password=settings.admin_password,
        options=base_options,
        connect_timeout=10,  # 增加连接超时
        keepalives=1,  # 启用TCP keepalive
        keepalives_idle=30,  # 30秒后开始发送keepalive
        keepalives_interval=10,  # 每10秒发送一次
        keepalives_count=5,  # 最多5次失败后断开
    )
    READ_POOL = SimpleConnectionPool(
        2,  # 增加最小连接数
        10,  # 增加最大连接数
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.read_user,
        password=settings.read_password,
        options=base_options,
        connect_timeout=10,  # 增加连接超时
        keepalives=1,  # 启用TCP keepalive
        keepalives_idle=30,  # 30秒后开始发送keepalive
        keepalives_interval=10,  # 每10秒发送一次
        keepalives_count=5,  # 最多5次失败后断开
    )


def close_pools() -> None:
    """关闭数据库连接池"""
    global ADMIN_POOL, READ_POOL, MONGO_CLIENT
    if ADMIN_POOL:
        ADMIN_POOL.closeall()
    if READ_POOL:
        READ_POOL.closeall()
    if MONGO_CLIENT:
        MONGO_CLIENT.close()


def init_mongo() -> None:
    """初始化MongoDB连接"""
    global MONGO_CLIENT
    if MongoClient is None:
        raise RuntimeError("pymongo未安装，请运行: pip install pymongo")

    try:
        # 构建MongoDB连接URI
        mongo_uri = (
            f"mongodb://{settings.mongo_user}:{settings.mongo_password}"
            f"@{settings.mongo_host}:{settings.mongo_port}"
            f"/{settings.mongo_db}?authSource={settings.mongo_auth_source}"
        )

        MONGO_CLIENT = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
            maxPoolSize=10,
            minPoolSize=1
        )

        # 测试连接
        MONGO_CLIENT.admin.command('ping')
        print(f"✅ MongoDB连接成功: {settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}")
    except Exception as e:
        print(f"❌ MongoDB连接失败: {e}")
        MONGO_CLIENT = None
        raise


def get_mongo_db():
    """获取MongoDB数据库实例"""
    if MONGO_CLIENT is None:
        init_mongo()
    if MONGO_CLIENT is None:
        raise RuntimeError("MongoDB未连接")
    return MONGO_CLIENT[settings.mongo_db]


def query_one(conn, sql: str, params: tuple) -> Dict[str, Any]:
    """执行查询并返回单行结果"""
    from .utils import _serialize_row
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    return _serialize_row(row)


def query_all(conn, sql: str, params: tuple) -> List[Dict[str, Any]]:
    """执行查询并返回所有结果"""
    from .utils import _serialize_rows
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return _serialize_rows(rows)
