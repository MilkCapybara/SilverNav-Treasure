#!/usr/bin/env python3
"""
测试科幻风格下拉框功能
验证CSS和JS文件是否正确加载
"""
import os
import sys

def test_files_exist():
    """测试文件是否存在"""
    print("=" * 60)
    print("📁 测试文件存在性")
    print("=" * 60)

    base_path = "/Users/sunfanmacpro/Desktop/SilverNav-Treasure"

    files_to_check = [
        "static/css/sci-fi-select.css",
        "static/js/sci-fi-select.js",
        "SCI_FI_SELECT_GUIDE.md",
        "templates/dashboard.html",
        "templates/detail.html",
        "templates/behavior.html"
    ]

    all_exist = True
    for file in files_to_check:
        full_path = os.path.join(base_path, file)
        exists = os.path.exists(full_path)
        status = "✅" if exists else "❌"
        print(f"{status} {file}")
        if not exists:
            all_exist = False

    return all_exist

def test_css_content():
    """测试CSS文件内容"""
    print("\n" + "=" * 60)
    print("🎨 测试CSS文件内容")
    print("=" * 60)

    css_path = "/Users/sunfanmacpro/Desktop/SilverNav-Treasure/static/css/sci-fi-select.css"

    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查关键样式是否存在
        checks = [
            ("基础样式", "select.sci-fi-select"),
            ("悬停效果", ":hover"),
            ("聚焦效果", ":focus"),
            ("脉冲动画", "@keyframes pulse-glow"),
            ("扫描线动画", "@keyframes scan-line"),
            ("数据流动画", "@keyframes data-flow"),
            ("加载动画", "@keyframes loading-spin"),
            ("响应式设计", "@media"),
            ("状态样式", ".warning"),
            ("包装器样式", ".sci-fi-select-wrapper")
        ]

        all_passed = True
        for name, keyword in checks:
            exists = keyword in content
            status = "✅" if exists else "❌"
            print(f"{status} {name}: {keyword}")
            if not exists:
                all_passed = False

        # 统计信息
        lines = content.split('\n')
        print(f"\n📊 CSS文件统计:")
        print(f"   总行数: {len(lines)}")
        print(f"   文件大小: {len(content)} 字节")

        return all_passed
    except Exception as e:
        print(f"❌ 读取CSS文件失败: {e}")
        return False

def test_js_content():
    """测试JavaScript文件内容"""
    print("\n" + "=" * 60)
    print("⚡ 测试JavaScript文件内容")
    print("=" * 60)

    js_path = "/Users/sunfanmacpro/Desktop/SilverNav-Treasure/static/js/sci-fi-select.js"

    try:
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查关键功能是否存在
        checks = [
            ("初始化函数", "initSciFiSelects"),
            ("交互事件", "addSelectInteractions"),
            ("聚焦事件", "addEventListener('focus'"),
            ("改变事件", "addEventListener('change'"),
            ("脉冲效果", "classList.add('pulse')"),
            ("数据流效果", "classList.add('data-flow')"),
            ("加载状态", "classList.add('loading')"),
            ("MutationObserver", "MutationObserver"),
            ("全局API", "window.initSciFiSelect"),
            ("自定义事件", "CustomEvent")
        ]

        all_passed = True
        for name, keyword in checks:
            exists = keyword in content
            status = "✅" if exists else "❌"
            print(f"{status} {name}: {keyword}")
            if not exists:
                all_passed = False

        # 统计信息
        lines = content.split('\n')
        print(f"\n📊 JavaScript文件统计:")
        print(f"   总行数: {len(lines)}")
        print(f"   文件大小: {len(content)} 字节")

        return all_passed
    except Exception as e:
        print(f"❌ 读取JavaScript文件失败: {e}")
        return False

def test_html_integration():
    """测试HTML文件集成"""
    print("\n" + "=" * 60)
    print("🌐 测试HTML文件集成")
    print("=" * 60)

    base_path = "/Users/sunfanmacpro/Desktop/SilverNav-Treasure/templates"
    html_files = ["dashboard.html", "detail.html", "behavior.html"]

    all_passed = True
    for html_file in html_files:
        print(f"\n检查 {html_file}:")
        html_path = os.path.join(base_path, html_file)

        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查CSS和JS是否引入
            css_included = 'sci-fi-select.css' in content
            js_included = 'sci-fi-select.js' in content

            print(f"   {'✅' if css_included else '❌'} CSS文件已引入")
            print(f"   {'✅' if js_included else '❌'} JavaScript文件已引入")

            if not (css_included and js_included):
                all_passed = False
        except Exception as e:
            print(f"   ❌ 读取文件失败: {e}")
            all_passed = False

    return all_passed

def test_guide_document():
    """测试使用指南文档"""
    print("\n" + "=" * 60)
    print("📖 测试使用指南文档")
    print("=" * 60)

    guide_path = "/Users/sunfanmacpro/Desktop/SilverNav-Treasure/SCI_FI_SELECT_GUIDE.md"

    try:
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查文档章节
        sections = [
            "概述",
            "特性",
            "样式类",
            "JavaScript API",
            "应用位置",
            "使用示例",
            "配色方案",
            "动画效果",
            "响应式设计",
            "故障排除"
        ]

        all_sections_exist = True
        for section in sections:
            exists = section in content
            status = "✅" if exists else "❌"
            print(f"{status} {section}")
            if not exists:
                all_sections_exist = False

        # 统计信息
        lines = content.split('\n')
        print(f"\n📊 文档统计:")
        print(f"   总行数: {len(lines)}")
        print(f"   文件大小: {len(content)} 字节")

        return all_sections_exist
    except Exception as e:
        print(f"❌ 读取文档失败: {e}")
        return False

def main():
    print("\n" + "🚀" * 30)
    print("科幻风格下拉框 - 功能测试")
    print("🚀" * 30 + "\n")

    results = []

    # 运行所有测试
    results.append(("文件存在性", test_files_exist()))
    results.append(("CSS内容", test_css_content()))
    results.append(("JavaScript内容", test_js_content()))
    results.append(("HTML集成", test_html_integration()))
    results.append(("使用指南", test_guide_document()))

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！科幻风格下拉框已成功集成。")
        print("\n下一步:")
        print("1. 启动服务器: python3 main.py")
        print("2. 访问页面测试:")
        print("   - http://localhost:8000/dashboard")
        print("   - http://localhost:8000/detail?type=trend")
        print("   - http://localhost:8000/behavior")
        print("3. 查看使用指南: SCI_FI_SELECT_GUIDE.md")
    else:
        print("⚠️  部分测试失败，请检查上述错误信息。")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
