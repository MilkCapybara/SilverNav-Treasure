#!/usr/bin/env python3
"""
快速验证脚本 - 测试真实数据API
"""
import sys
import time
import requests
from datetime import datetime

def test_api(url, name):
    """测试API端点"""
    try:
        print(f"  测试 {name}...", end=" ")
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ 成功")
                return True, data
            else:
                print(f"❌ 失败: {data.get('error', '未知错误')}")
                return False, None
        else:
            print(f"❌ HTTP {response.status_code}")
            return False, None
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败（应用未启动？）")
        return False, None
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False, None

def main():
    print("🧪 银航宝监控API验证")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # 检查应用是否启动
    print("\n📡 检查应用状态...")
    try:
        response = requests.get(base_url, timeout=5)
        print("  ✅ 应用已启动")
    except:
        print("  ❌ 应用未启动，请先运行: python main.py")
        sys.exit(1)

    # 测试监控API
    print("\n🔍 测试实时监控API")
    print("-" * 60)

    success, data = test_api(f"{base_url}/api/monitor/metrics", "监控指标")
    if success and data:
        metrics = data['data']
        print(f"    • CPU使用率: {metrics.get('cpu_usage', 0):.1f}%")
        print(f"    • 内存使用率: {metrics.get('memory_usage', 0):.1f}%")
        print(f"    • PG活跃连接: {metrics.get('pg_active', 0)}")
        print(f"    • Mongo活跃连接: {metrics.get('mongo_active', 0)}")

    test_api(f"{base_url}/api/monitor/api-stats", "API统计")
    test_api(f"{base_url}/api/monitor/alerts", "告警信息")

    # 测试质量API
    print("\n🎯 测试数据质量API")
    print("-" * 60)

    success, data = test_api(f"{base_url}/api/quality/metrics", "质量指标")
    if success and data:
        metrics = data['data']
        print(f"    • 综合质量分: {metrics.get('overall_score', 0)}")
        print(f"    • 完整性: {metrics.get('completeness', 0)}%")
        print(f"    • 准确性: {metrics.get('accuracy', 0)}%")
        print(f"    • 时效性: {metrics.get('timeliness', 0)}%")
        print(f"    • 一致性: {metrics.get('consistency', 0)}%")

        if 'tables' in metrics:
            print(f"    • 检查表数量: {len(metrics['tables'])}")

    success, data = test_api(f"{base_url}/api/quality/rules", "质量规则")
    if success and data:
        rules = data['data']
        print(f"    • 规则数量: {len(rules)}")
        passed = sum(1 for r in rules if r.get('status') == 'pass')
        print(f"    • 通过规则: {passed}/{len(rules)}")

    success, data = test_api(f"{base_url}/api/quality/timeliness", "时效性")
    if success and data:
        timeliness = data['data']
        print(f"    • 数据源数量: {len(timeliness)}")

    # 测试页面访问
    print("\n🌐 测试页面访问")
    print("-" * 60)

    pages = [
        ("/monitor", "实时监控大屏"),
        ("/quality", "数据质量监控"),
        ("/dashboard", "总览大屏")
    ]

    for path, name in pages:
        try:
            print(f"  测试 {name}...", end=" ")
            response = requests.get(f"{base_url}{path}", timeout=5)
            if response.status_code == 200:
                print("✅ 可访问")
            else:
                print(f"❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ 失败: {e}")

    print("\n" + "=" * 60)
    print("✅ 验证完成！")
    print("\n📍 访问地址:")
    print(f"  • 实时监控大屏: {base_url}/monitor")
    print(f"  • 数据质量监控: {base_url}/quality")
    print(f"  • 总览大屏: {base_url}/dashboard")

if __name__ == "__main__":
    main()
