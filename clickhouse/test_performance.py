#!/usr/bin/env python3
"""
Dashboard 性能测试脚本
用途：对比 PostgreSQL 和 ClickHouse 的查询性能
"""

import time
import requests
import statistics
from datetime import datetime


def test_dashboard_query(base_url: str = "http://localhost:8000"):
    """测试 Dashboard 查询性能"""
    url = f"{base_url}/api/dashboard"
    payload = {
        "base_date": "2026-02-27",
        "range": "30d",
        "currency": "CNY"
    }

    print("="*80)
    print("Dashboard 性能测试")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试URL: {url}")
    print(f"测试参数: {payload}")
    print("")

    # 预热请求
    print("🔥 预热请求...")
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            data_source = data.get('data_source', 'unknown')
            print(f"✅ 预热成功 (数据源: {data_source})")
        else:
            print(f"❌ 预热失败: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 预热失败: {e}")
        return

    # 正式测试
    print(f"\n🚀 开始性能测试 (10次)...")
    print("-"*80)

    times = []
    data_sources = []

    for i in range(10):
        try:
            start = time.time()
            response = requests.post(url, json=payload, timeout=30)
            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                data_source = data.get('data_source', 'unknown')
                query_time = data.get('query_time', 'N/A')

                times.append(elapsed)
                data_sources.append(data_source)

                print(f"测试 {i+1:2d}/10: {elapsed:6.3f}秒 | "
                      f"数据源: {data_source:10s} | "
                      f"服务器查询: {query_time}")
            else:
                print(f"测试 {i+1:2d}/10: ❌ HTTP {response.status_code}")

        except Exception as e:
            print(f"测试 {i+1:2d}/10: ❌ {e}")

        # 短暂休息
        time.sleep(0.5)

    # 统计结果
    if times:
        print("-"*80)
        print("\n📊 性能统计:")
        print(f"  测试次数: {len(times)}")
        print(f"  数据源: {data_sources[0] if data_sources else 'unknown'}")
        print(f"  平均响应时间: {statistics.mean(times):.3f}秒")
        print(f"  最快响应时间: {min(times):.3f}秒")
        print(f"  最慢响应时间: {max(times):.3f}秒")
        print(f"  标准差: {statistics.stdev(times):.3f}秒" if len(times) > 1 else "")
        print(f"  中位数: {statistics.median(times):.3f}秒")

        # 性能评级
        avg_time = statistics.mean(times)
        if avg_time < 1:
            rating = "🌟🌟🌟🌟🌟 优秀"
        elif avg_time < 3:
            rating = "🌟🌟🌟🌟 良好"
        elif avg_time < 10:
            rating = "🌟🌟🌟 一般"
        elif avg_time < 20:
            rating = "🌟🌟 较慢"
        else:
            rating = "🌟 需要优化"

        print(f"\n  性能评级: {rating}")

        # 性能建议
        if avg_time > 5:
            print(f"\n💡 性能建议:")
            if data_sources[0] == 'postgresql':
                print(f"  - 当前使用 PostgreSQL，建议迁移到 ClickHouse")
                print(f"  - 预期性能提升: 20-40倍")
                print(f"  - 预期响应时间: <1秒")
            else:
                print(f"  - 检查 ClickHouse 服务状态")
                print(f"  - 检查网络延迟")
                print(f"  - 考虑使用物化视图")

    print("\n" + "="*80)


def test_clickhouse_health(base_url: str = "http://localhost:8000"):
    """测试 ClickHouse 健康状态"""
    url = f"{base_url}/api/clickhouse/health"

    print("\n🔍 检查 ClickHouse 健康状态...")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            clickhouse_enabled = data.get('clickhouse_enabled', False)
            message = data.get('message', '')

            if clickhouse_enabled:
                print(f"✅ {message}")
            else:
                print(f"⚠️  {message}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")


def compare_performance():
    """对比 PostgreSQL 和 ClickHouse 性能"""
    print("\n" + "="*80)
    print("性能对比测试")
    print("="*80)
    print("\n说明:")
    print("  - 如果当前使用 ClickHouse，测试会显示 ClickHouse 性能")
    print("  - 如果 ClickHouse 不可用，会自动降级到 PostgreSQL")
    print("  - 建议先测试 PostgreSQL，再迁移到 ClickHouse 后测试对比")
    print("")


if __name__ == '__main__':
    # 检查 ClickHouse 健康状态
    test_clickhouse_health()

    # 性能测试
    test_dashboard_query()

    # 对比说明
    compare_performance()
