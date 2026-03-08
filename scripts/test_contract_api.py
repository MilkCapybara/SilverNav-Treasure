#!/usr/bin/env python3
"""
测试合同风险分析API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_stats_overview():
    """测试统计概览API"""
    print("\n=== 测试统计概览API ===")
    response = requests.get(f"{BASE_URL}/api/contracts/stats/overview")
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            stats = data['stats']
            print(f"✅ 总合同数: {stats['total']}")
            print(f"✅ 高风险: {stats['high_risk']} ({stats['high_risk_percent']}%)")
            print(f"✅ 中风险: {stats['medium_risk']} ({stats['medium_risk_percent']}%)")
            print(f"✅ 低风险: {stats['low_risk']} ({stats['low_risk_percent']}%)")
            print(f"✅ 平均评分: {stats['avg_score']}")
        else:
            print(f"❌ API返回失败: {data.get('msg')}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")

def test_search_contracts():
    """测试合同搜索API"""
    print("\n=== 测试合同搜索API ===")
    payload = {
        "page": 1,
        "page_size": 10
    }
    response = requests.post(
        f"{BASE_URL}/api/contracts/search",
        json=payload
    )
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print(f"✅ 找到 {data['total']} 份合同")
            print(f"✅ 当前页: {data['page']}/{data['total_pages']}")
            print(f"✅ 返回 {len(data['contracts'])} 条记录")
            if data['contracts']:
                contract = data['contracts'][0]
                print(f"\n示例合同:")
                print(f"  - 合同编号: {contract.get('contract_id')}")
                print(f"  - 船舶名称: {contract.get('vessel_name')}")
                print(f"  - 风险评分: {contract.get('risk_score')}")
                print(f"  - 风险等级: {contract.get('risk_level')}")
        else:
            print(f"❌ API返回失败: {data.get('msg')}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")

def test_contract_detail():
    """测试合同详情API"""
    print("\n=== 测试合同详情API ===")
    contract_id = "SN-2026-000001"
    response = requests.get(f"{BASE_URL}/api/contracts/{contract_id}")
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            contract = data['contract']
            print(f"✅ 合同编号: {contract.get('contract_id')}")
            print(f"✅ 船舶名称: {contract.get('vessel_name')}")
            print(f"✅ IMO编号: {contract.get('vessel_imo')}")
            print(f"✅ 企业名称: {contract.get('company_name')}")
            print(f"✅ 本金金额: ${contract.get('principal_amount')}")
            print(f"✅ 年利率: {contract.get('interest_rate')}%")
            print(f"✅ 风险评分: {contract.get('risk_score')}")
            print(f"✅ 风险等级: {contract.get('risk_level')}")
        else:
            print(f"❌ API返回失败: {data.get('msg')}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")

if __name__ == "__main__":
    print("开始测试合同风险分析API...")
    print("=" * 50)

    try:
        test_stats_overview()
        test_search_contracts()
        test_contract_detail()

        print("\n" + "=" * 50)
        print("✅ 所有测试完成!")

    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器，请确保FastAPI服务正在运行")
        print("启动命令: python3 main.py")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
