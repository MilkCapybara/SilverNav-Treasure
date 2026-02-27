#!/bin/bash
# Redis缓存快速部署脚本

echo "=========================================="
echo "Redis缓存快速部署"
echo "=========================================="
echo ""

# 1. 检查Redis是否已安装
echo "1. 检查Redis..."
if command -v redis-server &> /dev/null; then
    echo "✅ Redis已安装"
    redis-server --version
else
    echo "❌ Redis未安装"
    echo ""
    echo "请选择安装方式:"
    echo "  macOS: brew install redis"
    echo "  Ubuntu: sudo apt-get install redis-server"
    echo "  Docker: docker run -d -p 6379:6379 redis:latest"
    exit 1
fi

echo ""

# 2. 检查Redis是否运行
echo "2. 检查Redis服务..."
if redis-cli ping &> /dev/null; then
    echo "✅ Redis服务正在运行"
else
    echo "⚠️ Redis服务未运行，正在启动..."

    # 尝试启动Redis
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew services start redis
    else
        # Linux
        sudo systemctl start redis
    fi

    sleep 2

    if redis-cli ping &> /dev/null; then
        echo "✅ Redis服务启动成功"
    else
        echo "❌ Redis服务启动失败"
        exit 1
    fi
fi

echo ""

# 3. 安装Python依赖
echo "3. 安装Python依赖..."
pip3 install redis apscheduler -q
if [ $? -eq 0 ]; then
    echo "✅ 依赖安装成功"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

echo ""

# 4. 测试Redis连接
echo "4. 测试Redis连接..."
python3 << 'PYTHON_EOF'
import redis
try:
    client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    client.ping()
    print("✅ Redis连接测试成功")

    # 设置测试数据
    client.set('test_key', 'test_value', ex=60)
    value = client.get('test_key')
    print(f"✅ 读写测试成功: {value}")

    # 清理测试数据
    client.delete('test_key')

except Exception as e:
    print(f"❌ Redis连接失败: {e}")
    exit(1)
PYTHON_EOF

echo ""

# 5. 测试缓存模块
echo "5. 测试缓存模块..."
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
python3 app/cache.py

echo ""

# 6. 配置信息
echo "=========================================="
echo "配置信息"
echo "=========================================="
echo "Redis地址: localhost:6379"
echo "缓存TTL配置:"
echo "  - 大屏数据: 5分钟"
echo "  - 行为分析: 10分钟"
echo "  - 船舶画像: 30分钟"
echo "  - 数据血缘: 1小时"
echo ""

# 7. 启动建议
echo "=========================================="
echo "启动建议"
echo "=========================================="
echo ""
echo "方式1: 在main.py中集成缓存"
echo "  from app.cache import cache"
echo "  from app.precompute import scheduler"
echo "  scheduler.start()  # 启动预计算"
echo ""
echo "方式2: 单独运行预计算服务"
echo "  python3 app/precompute.py"
echo ""
echo "方式3: 使用systemd管理（Linux）"
echo "  sudo systemctl enable redis"
echo "  sudo systemctl start redis"
echo ""

# 8. 监控命令
echo "=========================================="
echo "监控命令"
echo "=========================================="
echo ""
echo "查看Redis状态:"
echo "  redis-cli info stats"
echo ""
echo "查看缓存键:"
echo "  redis-cli keys '*'"
echo ""
echo "查看缓存命中率:"
echo "  redis-cli info stats | grep keyspace"
echo ""
echo "清空所有缓存:"
echo "  redis-cli flushdb"
echo ""

echo "=========================================="
echo "✅ Redis缓存部署完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 在main.py中集成缓存代码"
echo "2. 启动预计算调度器"
echo "3. 测试大屏响应时间"
echo "4. 监控缓存命中率"
echo ""
