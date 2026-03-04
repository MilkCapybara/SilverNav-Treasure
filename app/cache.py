"""
Redis缓存层实现
用于加速大屏查询，将响应时间从20s降到2s以内
"""
import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib

# Redis连接配置
from .config import settings

REDIS_CONFIG = {
    'host': settings.redis_host,
    'port': settings.redis_port,
    'db': settings.redis_db,
    'password': settings.redis_password,
    'decode_responses': True,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'retry_on_timeout': True
}

# 缓存TTL配置（秒）
CACHE_TTL = {
    'dashboard': 300,      # 大屏数据：5分钟
    'behavior': 600,       # 行为分析：10分钟
    'profile': 1800,       # 船舶画像：30分钟
    'lineage': 3600,       # 数据血缘：1小时
}

class RedisCache:
    """Redis缓存管理器"""

    def __init__(self):
        self.client = None
        self._connect()

    def _connect(self):
        """连接Redis"""
        try:
            self.client = redis.Redis(**REDIS_CONFIG)
            self.client.ping()
            print("✅ Redis连接成功")
        except Exception as e:
            print(f"⚠️ Redis连接失败: {e}")
            self.client = None

    def _generate_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键"""
        # 将参数排序后生成唯一键
        params = sorted(kwargs.items())
        param_str = json.dumps(params, ensure_ascii=False)
        hash_str = hashlib.md5(param_str.encode()).hexdigest()[:8]
        return f"{prefix}:{hash_str}:{param_str}"

    def get(self, prefix: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """获取缓存"""
        if not self.client:
            return None

        try:
            key = self._generate_key(prefix, **kwargs)
            cached = self.client.get(key)

            if cached:
                print(f"✅ 缓存命中: {prefix}")
                return json.loads(cached)
            else:
                print(f"⚠️ 缓存未命中: {prefix}")
                return None
        except Exception as e:
            print(f"❌ 缓存读取失败: {e}")
            return None

    def set(self, prefix: str, data: Dict[Any, Any], ttl: Optional[int] = None, **kwargs):
        """设置缓存"""
        if not self.client:
            return

        try:
            key = self._generate_key(prefix, **kwargs)
            ttl = ttl or CACHE_TTL.get(prefix, 300)

            self.client.setex(
                key,
                ttl,
                json.dumps(data, ensure_ascii=False, default=str)
            )
            print(f"✅ 缓存设置成功: {prefix} (TTL: {ttl}s)")
        except Exception as e:
            print(f"❌ 缓存设置失败: {e}")

    def delete(self, prefix: str, **kwargs):
        """删除缓存"""
        if not self.client:
            return

        try:
            key = self._generate_key(prefix, **kwargs)
            self.client.delete(key)
            print(f"✅ 缓存删除成功: {prefix}")
        except Exception as e:
            print(f"❌ 缓存删除失败: {e}")

    def clear_pattern(self, pattern: str):
        """清除匹配模式的所有缓存"""
        if not self.client:
            return

        try:
            keys = self.client.keys(f"{pattern}*")
            if keys:
                self.client.delete(*keys)
                print(f"✅ 清除缓存: {len(keys)} 个键")
        except Exception as e:
            print(f"❌ 清除缓存失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.client:
            return {}

        try:
            info = self.client.info('stats')
            return {
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            print(f"❌ 获取统计失败: {e}")
            return {}

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """计算缓存命中率"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round(hits / total * 100, 2)


# 全局缓存实例
cache = RedisCache()


# 缓存装饰器
def cached(prefix: str, ttl: Optional[int] = None):
    """缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 尝试从缓存获取
            cached_data = cache.get(prefix, **kwargs)
            if cached_data is not None:
                return cached_data

            # 缓存未命中，执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            if result is not None:
                cache.set(prefix, result, ttl, **kwargs)

            return result
        return wrapper
    return decorator


# 使用示例
if __name__ == "__main__":
    # 测试连接
    print("=" * 60)
    print("Redis缓存测试")
    print("=" * 60)

    # 测试设置和获取
    test_data = {
        "total_exposure": 1000000,
        "high_risk_exposure": 200000,
        "company_count": 100
    }

    cache.set("dashboard", test_data, base_date="2026-02-25", range="today", currency="CNY")

    result = cache.get("dashboard", base_date="2026-02-25", range="today", currency="CNY")
    print(f"\n获取结果: {result}")

    # 测试统计
    stats = cache.get_stats()
    print(f"\n缓存统计: {stats}")

    print("\n" + "=" * 60)
    print("✅ Redis缓存测试完成")
    print("=" * 60)
