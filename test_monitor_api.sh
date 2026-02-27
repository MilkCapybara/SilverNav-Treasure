#!/bin/bash

# 测试新页面的真实数据API

echo "🧪 测试银航宝监控API"
echo "================================"

# 启动应用（后台运行）
echo "📦 启动应用..."
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
python main.py > /tmp/silvernav_test.log 2>&1 &
APP_PID=$!

# 等待应用启动
echo "⏳ 等待应用启动（5秒）..."
sleep 5

# 测试监控API
echo ""
echo "🔍 测试监控API..."
echo "--------------------------------"

echo "1. 测试 /api/monitor/metrics"
curl -s http://localhost:8000/api/monitor/metrics | python -m json.tool | head -20

echo ""
echo "2. 测试 /api/monitor/api-stats"
curl -s http://localhost:8000/api/monitor/api-stats | python -m json.tool | head -15

echo ""
echo "3. 测试 /api/monitor/alerts"
curl -s http://localhost:8000/api/monitor/alerts | python -m json.tool | head -15

# 测试质量API
echo ""
echo "🔍 测试质量API..."
echo "--------------------------------"

echo "1. 测试 /api/quality/metrics"
curl -s http://localhost:8000/api/quality/metrics | python -m json.tool | head -30

echo ""
echo "2. 测试 /api/quality/rules"
curl -s http://localhost:8000/api/quality/rules | python -m json.tool | head -20

echo ""
echo "3. 测试 /api/quality/timeliness"
curl -s http://localhost:8000/api/quality/timeliness | python -m json.tool | head -15

# 停止应用
echo ""
echo "🛑 停止应用..."
kill $APP_PID 2>/dev/null

echo ""
echo "================================"
echo "✅ 测试完成！"
echo ""
echo "📝 完整日志: /tmp/silvernav_test.log"
