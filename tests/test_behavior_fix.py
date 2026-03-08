#!/usr/bin/env python3
"""
测试behavior页面修复效果
"""
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

def test_imports():
    """测试导入是否正常"""
    print("1. 测试导入...")
    try:
        from app.behavior_api import router as behavior_router
        print("   ✅ behavior_api导入成功")
        return True
    except Exception as e:
        print(f"   ❌ behavior_api导入失败: {e}")
        return False

def test_mongodb_connection():
    """测试MongoDB连接"""
    print("\n2. 测试MongoDB连接...")
    try:
        from app.database import get_mongo_db
        db = get_mongo_db()

        # 测试ais_tracks集合
        track_count = db.ais_tracks.count_documents({})
        print(f"   ✅ MongoDB连接成功")
        print(f"   📊 ais_tracks集合有 {track_count:,} 条记录")

        # 测试获取船舶列表
        vessels = list(db.ais_tracks.aggregate([
            {"$group": {"_id": "$imo_number", "vessel_name": {"$first": "$vessel_name"}}},
            {"$limit": 5}
        ]))
        print(f"   🚢 找到 {len(vessels)} 艘船舶（示例）")
        for v in vessels[:3]:
            print(f"      - {v.get('vessel_name', 'Unknown')} ({v['_id']})")

        return True
    except Exception as e:
        print(f"   ❌ MongoDB连接失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点是否注册"""
    print("\n3. 测试API端点注册...")
    try:
        from main import app
        routes = [route.path for route in app.routes]

        behavior_routes = [
            "/api/behavior/summary",
            "/api/behavior/vessels",
            "/api/behavior/tracks",
            "/api/behavior/anomalies",
            "/api/behavior/geofence",
            "/api/behavior/statistics"
        ]

        all_registered = True
        for route in behavior_routes:
            if route in routes:
                print(f"   ✅ {route}")
            else:
                print(f"   ❌ {route} 未注册")
                all_registered = False

        return all_registered
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

def test_files_exist():
    """测试修改的文件是否存在"""
    print("\n4. 测试修改的文件...")
    import os

    files = [
        "templates/behavior.html",
        "static/js/behavior.js",
        "app/behavior_api.py",
        "main.py"
    ]

    all_exist = True
    for file in files:
        path = f"/Users/sunfanmacpro/Desktop/SilverNav-Treasure/{file}"
        if os.path.exists(path):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} 不存在")
            all_exist = False

    return all_exist

def main():
    print("=" * 60)
    print("🔍 Behavior页面修复测试")
    print("=" * 60)

    results = []
    results.append(("导入测试", test_imports()))
    results.append(("MongoDB连接", test_mongodb_connection()))
    results.append(("API端点注册", test_api_endpoints()))
    results.append(("文件检查", test_files_exist()))

    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n🎉 所有测试通过！可以启动服务器测试页面了。")
        print("\n启动命令：")
        print("  python3 main.py")
        print("\n访问地址：")
        print("  http://localhost:8000/behavior")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息。")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
