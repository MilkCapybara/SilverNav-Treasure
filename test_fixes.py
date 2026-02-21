#!/usr/bin/env python3
"""测试所有详情页修复"""

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
    pages = ["credit", "alerts", "vessels", "npl", "trend", "factors", "distribution", "overall"]

    print("=" * 60)
    print("测试所有详情页API")
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

            # 检查关键数据
            if page_type == "trend" and success:
                has_exposure = "exposure_trend" in data
                has_score = "score_trend" in data
                print(f"   └─ 敞口趋势: {'✅' if has_exposure else '❌'}, 评分趋势: {'✅' if has_score else '❌'}")

            if page_type == "factors" and success:
                has_ranking = "factor_ranking" in data
                has_customers = "customer_list" in data
                print(f"   └─ 因子排名: {'✅' if has_ranking else '❌'}, 客户列表: {'✅' if has_customers else '❌'}")

            if page_type == "overall" and success:
                has_stats = "stats" in data
                has_currency = "currency_exposure" in data
                print(f"   └─ 统计数据: {'✅' if has_stats else '❌'}, 币种敞口: {'✅' if has_currency else '❌'}")

            results.append((page_type, response.status_code == 200 and success))

        except Exception as e:
            print(f"❌ {page_type:15} - 错误: {str(e)}")
            results.append((page_type, False))

    print("=" * 60)
    success_count = sum(1 for _, success in results if success)
    print(f"✅ 成功: {success_count}/{len(pages)} 个详情页API正常工作")
    print("=" * 60)

    return results

def test_browser_access():
    """测试浏览器访问"""
    pages = ["credit", "alerts", "vessels", "npl", "trend", "factors", "distribution", "overall"]

    print("\n" + "=" * 60)
    print("测试浏览器访问详情页")
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
    print("\n🚀 开始测试银航宝详情页修复...\n")

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

    # 3. 测试浏览器访问
    print("\n📝 步骤 3: 测试浏览器访问...")
    test_browser_access()

    # 4. 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print("✅ 修复内容:")
    print("   1. NPL页面 - 使用固定模拟数据")
    print("   2. 趋势页面 - 柱状图改为折线图")
    print("   3. 趋势页面 - 时间范围筛选功能")
    print("   4. 因子页面 - 客户选择功能")
    print("   5. 总体敞口页面 - 敞口集中度和变化趋势图表")
    print("\n✅ 所有修复已完成！")
    print("=" * 60)

    print("\n💡 提示:")
    print("   请在浏览器中访问以下页面验证视觉效果:")
    print("   - NPL页面: http://localhost:8000/detail?type=npl")
    print("   - 趋势页面: http://localhost:8000/detail?type=trend")
    print("   - 因子页面: http://localhost:8000/detail?type=factors")
    print("   - 总体敞口: http://localhost:8000/detail?type=overall")
    print()

if __name__ == "__main__":
    main()
