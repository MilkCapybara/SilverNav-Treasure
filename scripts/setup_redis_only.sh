#!/bin/bash
# 快速安装和测试 Redis 集成

echo "=========================================="
echo "Redis 集成 - 快速安装"
echo "=========================================="

# 1. 安装 Python Redis 库
echo ""
echo "1. 安装 Python Redis 库..."
pip install redis

# 2. 测试 Redis 连接
echo ""
echo "2. 测试 Redis 连接..."
python3 test_redis_connection.py

# 3. 测试 Dashboard 缓存
echo ""
echo "3. 测试 Dashboard 缓存..."
echo "启动应用后，访问 http://localhost:8000/dashboard"
echo "第一次加载会慢（查询数据库），第二次加载会快（从缓存读取）"

echo ""
echo "=========================================="
echo "✅ Redis 安装完成"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 启动应用: python main.py"
echo "2. 访问 Dashboard: http://localhost:8000/dashboard"
echo "3. 刷新页面，观察加载速度变化"
echo ""
echo "查看缓存效果："
echo "- 第一次访问: 显示 'data_source: clickhouse' 或 'postgresql'"
echo "- 第二次访问: 显示 'data_source: cache'"
