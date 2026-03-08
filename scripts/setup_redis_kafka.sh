#!/bin/bash
# Redis 和 Kafka 集成安装脚本

echo "=========================================="
echo "Redis 和 Kafka 集成安装"
echo "=========================================="

# 1. 安装 Python 依赖
echo ""
echo "1. 安装 Python 依赖..."
pip install -r requirements-redis-kafka.txt

# 2. 测试 Redis 连接
echo ""
echo "2. 测试 Redis 连接..."
python3 test_redis_connection.py

# 3. 测试 Kafka 连接
echo ""
echo "3. 测试 Kafka 连接..."
python3 test_kafka_connection.py

echo ""
echo "=========================================="
echo "✅ 安装和测试完成"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 启动应用: python main.py"
echo "2. 访问 Dashboard: http://localhost:8000/dashboard"
echo "3. 查看缓存效果: 第一次加载慢，后续加载快"
