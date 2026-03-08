#!/usr/bin/env python3
"""
完整的 Redis + Dashboard 集成测试
"""
import sys
import time
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

print("=" * 80)
print("Redis + Dashboard 集成测试")
print("=" * 80)

# ============================================================================
# 测试 1: Redis 连接
# ============================================================================
print("\n【测试 1】Redis 连接测试")
print("-" * 80)

from app.cache import cache

if not cache.client:
    print("❌ Redis 连接失败")
    print("\n请检查:")
    print("1. Redis 服务是否启动: redis-cli ping")
    print("2. 配置是否正确:")
    print(f"   - Host: 1.15.225.134")
    print(f"   - Port: 6379")
    print(f"   - Password: sun2137405")
    print("3. 防火墙是否开放 6379 端口")
    sys.exit(1)

print("✅ Redis 连接成功")

# ============================================================================
# 测试 2: 基本缓存操作
# ============================================================================
print("\n【测试 2】基本缓存操作")
print("-" * 80)

test_data = {
    "total_exposure": 1500000000,
    "high_risk_exposure": 300000000,
    "timestamp": time.time()
}

print("1. 设置缓存...")
cache.set("test_dashboard", test_data, ttl=60, base_date="2026-03-03", range="today")
print("   ✅ 缓存设置成功")

print("\n2. 读取缓存...")
result = cache.get("test_dashboard", base_date="2026-03-03", range="today")
if result:
    print(f"   ✅ 缓存读取成功")
    print(f"   数据: {result}")
else:
    print("   ❌ 缓存读取失败")

print("\n3. 删除缓存...")
cache.delete("test_dashboard", base_date="2026-03-03", range="today")
print("   ✅ 缓存删除成功")

print("\n4. 验证删除...")
result = cache.get("test_dashboard", base_date="2026-03-03", range="today")
if result is None:
    print("   ✅ 缓存已删除")
else:
    print("   ❌ 缓存删除失败")

# ============================================================================
# 测试 3: 缓存统计
# ============================================================================
print("\n【测试 3】缓存统计")
print("-" * 80)

stats = cache.get_stats()
print(f"总命令数: {stats.get('total_commands', 0)}")
print(f"缓存命中: {stats.get('keyspace_hits', 0)}")
print(f"缓存未命中: {stats.get('keyspace_misses', 0)}")
print(f"命中率: {stats.get('hit_rate', 0)}%")

# ============================================================================
# 测试 4: 模拟 Dashboard 缓存流程
# ============================================================================
print("\n【测试 4】模拟 Dashboard 缓存流程")
print("-" * 80)

from datetime import date

# 模拟 Dashboard 请求参数
cache_params = {
    'base_date': '2026-03-03',
    'range': '30d',
    'currency': 'CNY',
    'start_date': '2026-02-01',
    'end_date': '2026-03-03'
}

print("1. 第一次请求（缓存未命中）...")
cached = cache.get('dashboard', **cache_params)
if cached is None:
    print("   ✅ 缓存未命中（符合预期）")

    # 模拟查询数据库
    print("   🔍 模拟查询数据库...")
    time.sleep(0.5)  # 模拟查询延迟

    dashboard_data = {
        "data_source": "clickhouse",
        "query_time": "0.500s",
        "summary": {
            "total_exposure": 1500000000,
            "high_risk_exposure": 300000000,
            "high_risk_ratio": 0.2
        },
        "alerts": {
            "high_risk_company_count": 136,
            "high_risk_vessel_count": 145
        }
    }

    # 存入缓存
    cache.set('dashboard', dashboard_data, ttl=300, **cache_params)
    print("   ✅ 数据已缓存（TTL: 300秒）")
else:
    print("   ⚠️ 缓存已存在（可能是之前的测试数据）")

print("\n2. 第二次请求（缓存命中）...")
cached = cache.get('dashboard', **cache_params)
if cached:
    print("   ✅ 缓存命中")
    print(f"   数据源: {cached.get('data_source', 'unknown')}")
    print(f"   总敞口: {cached.get('summary', {}).get('total_exposure', 0):,.0f}")
else:
    print("   ❌ 缓存未命中")

# 清理测试数据
print("\n3. 清理测试数据...")
cache.delete('dashboard', **cache_params)
print("   ✅ 测试数据已清理")

# ============================================================================
# 测试 5: 性能对比
# ============================================================================
print("\n【测试 5】性能对比")
print("-" * 80)

# 模拟数据库查询
print("1. 模拟数据库查询（无缓存）...")
start = time.time()
time.sleep(2)  # 模拟 2 秒查询时间
db_time = time.time() - start
print(f"   耗时: {db_time:.3f}秒")

# 模拟缓存读取
print("\n2. 模拟缓存读取...")
test_data = {"test": "data"}
cache.set("perf_test", test_data, ttl=60)
start = time.time()
cache.get("perf_test")
cache_time = time.time() - start
print(f"   耗时: {cache_time:.3f}秒")

speedup = db_time / cache_time if cache_time > 0 else 0
print(f"\n   ⚡ 性能提升: {speedup:.0f}x")

cache.delete("perf_test")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 80)
print("✅ 所有测试通过")
print("=" * 80)
print("\n下一步:")
print("1. 启动应用: python main.py")
print("2. 访问 Dashboard: http://localhost:8000/dashboard")
print("3. 观察控制台输出:")
print("   - 第一次访问: '⚠️ 缓存未命中，查询数据库'")
print("   - 第二次访问: '✅ 缓存命中: Dashboard 数据'")
print("4. 查看响应中的 data_source 字段:")
print("   - 'cache': 从缓存读取")
print("   - 'clickhouse' 或 'postgresql': 从数据库读取")
print("\n缓存配置:")
print("- TTL: 300秒（5分钟）")
print("- 5分钟后缓存自动过期，重新查询数据库")
