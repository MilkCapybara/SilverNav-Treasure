#!/bin/bash
# 启动银航宝服务（包含船舶行为分析页面）

echo "=========================================="
echo "启动银航宝 SilverNav Treasure"
echo "=========================================="
echo ""

cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure

echo "✅ 服务启动中..."
echo ""
echo "可访问的页面："
echo "  - 登录页面: http://localhost:8000/"
echo "  - 数据大屏: http://localhost:8000/dashboard"
echo "  - 船舶行为分析: http://localhost:8000/behavior"
echo ""
echo "默认账号: root"
echo "默认密码: sunfannb0307SF?"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""
echo "=========================================="
echo ""

python3 main.py
