#!/usr/bin/env python3
"""
合同风险分析系统 - 完整测试脚本
测试所有页面和API是否正常工作
"""
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_page_access(url, name):
    """测试页面访问"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: 访问成功")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: 无法连接到服务器")
        return False
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

def test_api(url, name, method="GET", json_data=None):
    """测试API接口"""
    try:
        if method == "POST":
            response = requests.post(url, json=json_data, timeout=5)
        else:
            response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ {name}: API正常")
                return True
            else:
                print(f"❌ {name}: {data.get('msg', '未知错误')}")
                return False
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: 无法连接到服务器")
        return False
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("  银航宝 - 合同风险分析系统完整测试")
    print("=" * 70)
    print()

    # 检查服务器是否运行
    print("🔍 检查服务器状态...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ 服务器运行中 (HTTP {response.status_code})")
    except:
        print("❌ 服务器未运行，请先启动: python3 main.py")
        sys.exit(1)

    print()
    print("-" * 70)
    print("📄 测试页面访问")
    print("-" * 70)

    pages = [
        (f"{BASE_URL}/contract-risk", "合同风险分析页面"),
        (f"{BASE_URL}/dashboard", "数据大屏"),
        (f"{BASE_URL}/behavior", "船舶行为分析"),
        (f"{BASE_URL}/profile", "船舶画像"),
        (f"{BASE_URL}/quality", "数据质量监控"),
        (f"{BASE_URL}/lineage", "数据血缘"),
        (f"{BASE_URL}/ml-predict", "智能风险预测"),
    ]

    page_results = []
    for url, name in pages:
        result = test_page_access(url, name)
        page_results.append(result)

    print()
    print("-" * 70)
    print("🔌 测试合同风险分析API")
    print("-" * 70)

    api_results = []

    # 测试统计概览API
    result = test_api(
        f"{BASE_URL}/api/contracts/stats/overview",
        "统计概览API"
    )
    api_results.append(result)

    # 测试合同搜索API
    result = test_api(
        f"{BASE_URL}/api/contracts/search",
        "合同搜索API",
        method="POST",
        json_data={"page": 1, "page_size": 10}
    )
    api_results.append(result)

    # 测试合同详情API
    result = test_api(
        f"{BASE_URL}/api/contracts/SN-2026-000001",
        "合同详情API"
    )
    api_results.append(result)

    # 测试风险趋势API
    result = test_api(
        f"{BASE_URL}/api/contracts/stats/trend",
        "风险趋势API"
    )
    api_results.append(result)

    print()
    print("=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)

    total_tests = len(page_results) + len(api_results)
    passed_tests = sum(page_results) + sum(api_results)

    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")

    if passed_tests == total_tests:
        print()
        print("🎉 所有测试通过！系统运行正常！")
        print()
        print("📋 快速访问链接:")
        print(f"  - 合同风险分析: {BASE_URL}/contract-risk")
        print(f"  - 数据大屏: {BASE_URL}/dashboard")
        print()
        return 0
    else:
        print()
        print("⚠️  部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
