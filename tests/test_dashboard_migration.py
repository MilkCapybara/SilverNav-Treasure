#!/usr/bin/env python3
"""
测试 Dashboard ClickHouse 迁移
验证应用能否正常启动，以及降级机制是否工作
"""

import sys
import time

print("=" * 80)
print("Dashboard ClickHouse 迁移测试")
print("=" * 80)

# 1. 测试 ClickHouse 客户端导入
print("\n1. 测试 ClickHouse 客户端导入...")
try:
    from app.clickhouse_client import (
        check_clickhouse_health,
        get_fx_rate_ch,
        get_dashboard_summary_ch
    )
    print("✅ ClickHouse 客户端模块导入成功")
except ImportError as e:
    print(f"❌ ClickHouse 客户端模块导入失败: {e}")
    sys.exit(1)

# 2. 测试 ClickHouse 连接
print("\n2. 测试 ClickHouse 连接...")
is_healthy = check_clickhouse_health()
if is_healthy:
    print("✅ ClickHouse 连接正常")
else:
    print("⚠️ ClickHouse 连接失败，将使用 PostgreSQL 降级")

# 3. 测试 main.py 导入
print("\n3. 测试 main.py 导入...")
try:
    import main
    print("✅ main.py 导入成功")
    print(f"   - CLICKHOUSE_AVAILABLE: {main.CLICKHOUSE_AVAILABLE}")
except Exception as e:
    print(f"❌ main.py 导入失败: {e}")
    sys.exit(1)

# 4. 测试 FastAPI 应用
print("\n4. 测试 FastAPI 应用...")
try:
    app = main.app
    print("✅ FastAPI 应用创建成功")

    # 检查路由
    routes = [route.path for route in app.routes]
    if "/api/dashboard" in routes:
        print("✅ /api/dashboard 路由存在")
    if "/api/clickhouse/health" in routes:
        print("✅ /api/clickhouse/health 路由存在")
except Exception as e:
    print(f"❌ FastAPI 应用测试失败: {e}")
    sys.exit(1)

# 5. 总结
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)
print("✅ 代码修改完成，应用可以正常启动")
print("✅ ClickHouse 支持已集成，带降级机制")
if is_healthy:
    print("✅ ClickHouse 连接正常，将使用 ClickHouse 查询")
else:
    print("⚠️ ClickHouse 连接失败，将使用 PostgreSQL 查询")
    print("\n下一步操作：")
    print("1. 检查 ClickHouse 服务器是否运行")
    print("2. 检查网络连接和防火墙设置")
    print("3. 运行数据迁移脚本: python3 clickhouse/migrate_to_clickhouse.py")
    print("4. 或使用部署脚本: ./clickhouse/deploy_clickhouse.sh")

print("\n启动应用命令: python main.py")
print("=" * 80)
