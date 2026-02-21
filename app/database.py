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
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def init_pools() -> None:
    """初始化数据库连接池"""
    global ADMIN_POOL, READ_POOL
    _require_db()
    base_options = f"-c search_path={settings.db_schema} -c statement_timeout=30000"
    ADMIN_POOL = SimpleConnectionPool(
        1,
        5,
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.admin_user,
        password=settings.admin_password,
        options=base_options,
        connect_timeout=5,
    )
    READ_POOL = SimpleConnectionPool(
        1,
        5,
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.read_user,
        password=settings.read_password,
        options=base_options,
        connect_timeout=5,
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
