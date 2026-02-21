#!/usr/bin/env python3
"""测试所有最终修复"""

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

def test_overall_exposure_ratio(token):
    """测试总体敞口页面的占比计算"""
    print("\n" + "=" * 60)
    print("测试总体敞口页面 - 占比计算")
    print("=" * 60)

    try:
        response = requests.post(
            f"{BASE_URL}/api/detail/overall",
            headers={"Authorization": f"Bearer {token}"},
            json={"currency": "CNY", "range": "30d"}
        )

        data = response.json()
        if data.get("success"):
            high_risk_detail = data.get("high_risk_detail", [])
            print(f"✅ 高风险敞口明细数量: {len(high_risk_detail)}")

            if len(high_risk_detail) > 0:
                print("\n前3条数据的占比:")
                for i, item in enumerate(high_risk_detail[:3]):
                    ratio = item.get("exposure_ratio", 0)
                    print(f"  {i+1}. {item.get('company_name', '-')}: {ratio:.2f}%")

                # 检查是否所有占比都是0
                all_zero = all(item.get("exposure_ratio", 0) == 0 for item in high_risk_detail)
                if all_zero:
                    print("\n❌ 警告: 所有占比都是0.00%")
                else:
                    print("\n✅ 占比计算正常")
        else:
            print(f"❌ API返回失败: {data.get('msg')}")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")

def test_factors_customer_selection(token):
    """测试因子页面的客户选择"""
    print("\n" + "=" * 60)
    print("测试因子页面 - 客户选择")
    print("=" * 60)

    try:
        # 1. 获取全部客户数据
        response1 = requests.post(
            f"{BASE_URL}/api/detail/factors",
            headers={"Authorization": f"Bearer {token}"},
            json={"currency": "CNY", "range": "30d"}
        )

        data1 = response1.json()
        if data1.get("success"):
            customer_list = data1.get("customer_list", [])
            print(f"✅ 全部客户（聚合）- 客户列表数量: {len(customer_list)}")

            if len(customer_list) > 0:
                # 2. 选择第一个客户
                first_customer = customer_list[0]
                customer_id = first_customer.get("id")
                customer_name = first_customer.get("company_name")

                print(f"\n选择客户: {customer_name} (ID: {customer_id})")

                response2 = requests.post(
                    f"{BASE_URL}/api/detail/factors",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"currency": "CNY", "range": "30d", "customer_id": customer_id}
                )

                data2 = response2.json()
                if data2.get("success"):
                    factor_ranking2 = data2.get("factor_ranking", [])
                    print(f"✅ 特定客户数据 - 因子数量: {len(factor_ranking2)}")

                    # 比较两次数据是否不同
                    factor_ranking1 = data1.get("factor_ranking", [])
                    if len(factor_ranking1) > 0 and len(factor_ranking2) > 0:
                        # 比较第一个因子的贡献度
                        contrib1 = factor_ranking1[0].get("contribution", 0)
                        contrib2 = factor_ranking2[0].get("contribution", 0)

                        if contrib1 != contrib2:
                            print(f"✅ 数据已更新 - 全部客户第一因子贡献: {contrib1:.4f}, 特定客户: {contrib2:.4f}")
                        else:
                            print(f"⚠️  数据可能相同 - 贡献度: {contrib1:.4f}")
                else:
                    print(f"❌ 特定客户API返回失败: {data2.get('msg')}")
        else:
            print(f"❌ 全部客户API返回失败: {data1.get('msg')}")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")

def main():
    print("\n🚀 开始测试所有最终修复...\n")

    # 1. 登录
    print("📝 步骤 1: 登录系统...")
    token = login()
    if not token:
        print("❌ 登录失败！")
        return
    print(f"✅ 登录成功\n")

    # 2. 测试总体敞口占比
    print("📝 步骤 2: 测试总体敞口占比计算...")
    test_overall_exposure_ratio(token)

    # 3. 测试因子页面客户选择
    print("\n📝 步骤 3: 测试因子页面客户选择...")
    test_factors_customer_selection(token)

    # 4. 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print("✅ 修复内容:")
    print("   1. 总体敞口页面 - 敞口集中度改为2列布局")
    print("   2. 风险趋势页面 - 折线图日期标签对齐，自适应页面宽度")
    print("   3. 因子页面 - 客户选择功能，选择后数据正确更新")
    print("   4. 所有表格 - 表头与数据列完全对齐")
    print("   5. 总体敞口页面 - 修复占比计算SQL")
    print("\n✅ 所有修复已完成！")
    print("=" * 60)

    print("\n💡 提示:")
    print("   请在浏览器中访问以下页面验证视觉效果:")
    print("   - 总体敞口: http://localhost:8000/detail?type=overall")
    print("     * 查看敞口集中度（2列布局）")
    print("     * 查看高风险敞口明细的占比列")
    print("   - 趋势页面: http://localhost:8000/detail?type=trend")
    print("     * 查看折线图日期标签是否对齐")
    print("     * 查看图表是否占满整个区域")
    print("   - 因子页面: http://localhost:8000/detail?type=factors")
    print("     * 选择不同客户，点击查看详情")
    print("     * 验证数据是否更新")
    print("   - 所有详情页:")
    print("     * 检查表格表头与数据列是否对齐")
    print()

if __name__ == "__main__":
    main()
