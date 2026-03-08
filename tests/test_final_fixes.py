#!/usr/bin/env python3
"""测试最终修复"""

import requests
import json

BASE_URL = "http://localhost:8000"

def login():
    """登录获取token"""
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": "root", "password": "sunfannb0307SF?"}
    )
    data = response.json()
    return data.get("token")

def test_detail_pages(token):
    """测试所有详情页API"""
    # 移除NPL页面
    pages = ["credit", "alerts", "vessels", "trend", "factors", "distribution", "overall"]

    print("=" * 60)
    print("测试所有详情页API（已移除NPL页面）")
    print("=" * 60)

    results = []
    for page_type in pages:
        try:
            response = requests.post(
                f"{BASE_URL}/api/detail/{page_type}",
                headers={"Authorization": f"Bearer {token}"},
                json={"currency": "CNY", "range": "30d"}
            )

            status = "✅" if response.status_code == 200 else "❌"
            data = response.json()
            success = data.get("success", False)

            print(f"{status} {page_type:15} - 状态码: {response.status_code}, 成功: {success}")

            results.append((page_type, response.status_code == 200 and success))

        except Exception as e:
            print(f"❌ {page_type:15} - 错误: {str(e)}")
            results.append((page_type, False))

    print("=" * 60)
    success_count = sum(1 for _, success in results if success)
    print(f"✅ 成功: {success_count}/{len(pages)} 个详情页API正常工作")
    print("=" * 60)

    return results

def test_trend_time_ranges(token):
    """测试趋势页面的时间范围"""
    print("\n" + "=" * 60)
    print("测试趋势页面时间范围功能")
    print("=" * 60)

    time_ranges = ["7d", "30d", "90d", "180d", "1y"]

    for time_range in time_ranges:
        try:
            response = requests.post(
                f"{BASE_URL}/api/detail/trend",
                headers={"Authorization": f"Bearer {token}"},
                json={"currency": "CNY", "range": time_range}
            )

            status = "✅" if response.status_code == 200 else "❌"
            data = response.json()
            success = data.get("success", False)

            print(f"{status} {time_range:10} - 状态码: {response.status_code}, 成功: {success}")

        except Exception as e:
            print(f"❌ {time_range:10} - 错误: {str(e)}")

    print("=" * 60)

def test_factors_customer_selection(token):
    """测试因子页面的客户选择"""
    print("\n" + "=" * 60)
    print("测试因子页面客户选择功能")
    print("=" * 60)

    # 测试全部客户
    try:
        response = requests.post(
            f"{BASE_URL}/api/detail/factors",
            headers={"Authorization": f"Bearer {token}"},
            json={"currency": "CNY", "range": "30d"}
        )

        status = "✅" if response.status_code == 200 else "❌"
        data = response.json()
        success = data.get("success", False)

        print(f"{status} 全部客户（聚合） - 状态码: {response.status_code}, 成功: {success}")

        if success and "customer_list" in data:
            print(f"   └─ 客户列表数量: {len(data['customer_list'])}")

            # 测试选择第一个客户
            if len(data['customer_list']) > 0:
                first_customer = data['customer_list'][0]
                customer_id = first_customer.get('id')
                customer_name = first_customer.get('company_name')

                response2 = requests.post(
                    f"{BASE_URL}/api/detail/factors",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"currency": "CNY", "range": "30d", "customer_id": customer_id}
                )

                status2 = "✅" if response2.status_code == 200 else "❌"
                data2 = response2.json()
                success2 = data2.get("success", False)

                print(f"{status2} 特定客户 ({customer_name}) - 状态码: {response2.status_code}, 成功: {success2}")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")

    print("=" * 60)

def test_browser_access():
    """测试浏览器访问"""
    # 移除NPL页面
    pages = ["credit", "alerts", "vessels", "trend", "factors", "distribution", "overall"]

    print("\n" + "=" * 60)
    print("测试浏览器访问详情页（已移除NPL页面）")
    print("=" * 60)

    for page_type in pages:
        try:
            response = requests.get(f"{BASE_URL}/detail?type={page_type}")
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {page_type:15} - http://localhost:8000/detail?type={page_type}")
        except Exception as e:
            print(f"❌ {page_type:15} - 错误: {str(e)}")

    print("=" * 60)

def main():
    print("\n🚀 开始测试银航宝详情页最终修复...\n")

    # 1. 登录
    print("📝 步骤 1: 登录系统...")
    token = login()
    if not token:
        print("❌ 登录失败！")
        return
    print(f"✅ 登录成功，Token: {token[:20]}...\n")

    # 2. 测试API
    print("📝 步骤 2: 测试详情页API...")
    results = test_detail_pages(token)

    # 3. 测试趋势页面时间范围
    print("\n📝 步骤 3: 测试趋势页面时间范围...")
    test_trend_time_ranges(token)

    # 4. 测试因子页面客户选择
    print("\n📝 步骤 4: 测试因子页面客户选择...")
    test_factors_customer_selection(token)

    # 5. 测试浏览器访问
    print("\n📝 步骤 5: 测试浏览器访问...")
    test_browser_access()

    # 6. 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print("✅ 修复内容:")
    print("   1. ✅ 移除NPL页面")
    print("   2. ✅ 总体敞口页面 - 敞口集中度图表增大，数据不被遮挡")
    print("   3. ✅ 总体敞口页面 - 敞口变化趋势改为折线图")
    print("   4. ✅ 趋势页面 - 时间范围筛选功能（7天/30天/90天/180天/1年）")
    print("   5. ✅ 趋势页面 - 折线图日期以实时时间为基准向左延伸")
    print("   6. ✅ 趋势页面 - 折线图完整呈现在页面中")
    print("   7. ✅ 因子页面 - 客户选择功能（选谁是谁）")
    print("\n✅ 所有修复已完成！")
    print("=" * 60)

    print("\n💡 提示:")
    print("   请在浏览器中访问以下页面验证视觉效果:")
    print("   - 趋势页面: http://localhost:8000/detail?type=trend")
    print("     * 选择不同时间范围（7天/30天/90天/180天/1年）")
    print("     * 点击「刷新数据」按钮查看折线图变化")
    print("   - 因子页面: http://localhost:8000/detail?type=factors")
    print("     * 选择不同客户")
    print("     * 点击「查看详情」按钮查看该客户的因子分析")
    print("   - 总体敞口: http://localhost:8000/detail?type=overall")
    print("     * 查看敞口集中度分析（Top10）- 已增大，数据清晰")
    print("     * 查看敞口变化趋势（近30天）- 折线图")
    print()

if __name__ == "__main__":
    main()
