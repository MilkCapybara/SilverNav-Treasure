#!/usr/bin/env python3
"""
测试MongoDB连接
"""
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

from app.database import init_mongo, get_mongo_db

def test_mongo_connection():
    """测试MongoDB连接"""
    print("=" * 60)
    print("测试MongoDB连接")
    print("=" * 60)

    try:
        # 初始化MongoDB连接
        init_mongo()

        # 获取数据库实例
        db = get_mongo_db()

        # 列出所有集合
        collections = db.list_collection_names()
        print(f"\n当前数据库中的集合: {collections if collections else '(空)'}")

        # 测试插入和查询
        print("\n测试插入和查询...")
        test_collection = db['test_connection']

        # 插入测试数据
        result = test_collection.insert_one({
            "test": "hello",
            "message": "MongoDB连接测试成功！",
            "timestamp": "2026-02-21"
        })
        print(f"✅ 插入成功，文档ID: {result.inserted_id}")

        # 查询测试数据
        doc = test_collection.find_one({"test": "hello"})
        print(f"✅ 查询成功: {doc}")


        print("\n" + "=" * 60)
        print("✅ MongoDB连接测试通过！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ MongoDB连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mongo_connection()
    sys.exit(0 if success else 1)
