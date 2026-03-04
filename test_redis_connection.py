#!/usr/bin/env python3
"""
测试 Redis 连接
"""
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

from app.cache import cache

print("=" * 60)
print("Redis 连接测试")
print("=" * 60)

# 测试连接
if cache.client:
    print("✅ Redis 连接成功")

    # 测试设置和获取
    test_data = {
        "total_exposure": 1000000,
        "high_risk_exposure": 200000,
        "company_count": 100
    }

    print("\n1. 测试缓存设置...")
    cache.set("test_dashboard", test_data, ttl=60, base_date="2026-03-03", range="today")

    print("\n2. 测试缓存获取...")
    result = cache.get("test_dashboard", base_date="2026-03-03", range="today")

    if result:
        print(f"✅ 缓存读取成功: {result}")
    else:
        print("❌ 缓存读取失败")

    # 测试统计
    print("\n3. 测试缓存统计...")
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")

    # 清理测试数据
    print("\n4. 清理测试数据...")
    cache.delete("test_dashboard", base_date="2026-03-03", range="today")

    print("\n" + "=" * 60)
    print("✅ Redis 测试完成")
    print("=" * 60)
else:
    print("❌ Redis 连接失败")
    print("请检查:")
    print("1. Redis 服务是否启动")
    print("2. 配置是否正确 (host, port, password)")
    print("3. 防火墙是否开放 6379 端口")
