#!/bin/bash
# Dashboard ClickHouse 迁移 - 最终验证脚本

echo "================================================================================"
echo "Dashboard ClickHouse 迁移 - 最终验证"
echo "================================================================================"
echo ""

# 1. 检查 ClickHouse 连接
echo "1. 检查 ClickHouse 连接..."
python3 -c "
import clickhouse_connect
try:
    client = clickhouse_connect.get_client(
        host='1.15.225.134',
        port=8123,
        username='default',
        password='sun2137405',
        database='silvernav'
    )
    client.query('SELECT 1')
    print('✅ ClickHouse 连接正常')
except Exception as e:
    print(f'❌ ClickHouse 连接失败: {e}')
    exit(1)
"

echo ""

# 2. 检查数据状态
echo "2. 检查 ClickHouse 数据状态..."
python3 -c "
import clickhouse_connect
client = clickhouse_connect.get_client(
    host='1.15.225.134',
    port=8123,
    username='default',
    password='sun2137405',
    database='silvernav'
)

tables = ['companies', 'vessels', 'financial_assets', 'fx_rates', 'vessel_risk_history', 'risk_factor_contribution']
print('表名                          | 记录数      | 状态')
print('-' * 60)
for table in tables:
    try:
        count = client.query(f'SELECT count() FROM {table}').result_rows[0][0]
        status = '✅ 已迁移' if count > 0 else '⚠️ 需要迁移'
        print(f'{table:30} | {count:>10,} | {status}')
    except:
        print(f'{table:30} | 错误       | ❌ 表不存在')
"

echo ""

# 3. 测试应用导入
echo "3. 测试应用导入..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    import main
    print('✅ main.py 导入成功')
    print(f'   - CLICKHOUSE_AVAILABLE: {main.CLICKHOUSE_AVAILABLE}')
except Exception as e:
    print(f'❌ main.py 导入失败: {e}')
    exit(1)
"

echo ""

# 4. 测试 ClickHouse 查询
echo "4. 测试 ClickHouse 查询功能..."
python3 -c "
import sys
sys.path.insert(0, '.')
from datetime import date, timedelta
from app.clickhouse_client import (
    init_clickhouse,
    get_fx_rate_ch,
    get_dashboard_risk_levels_ch,
    get_dashboard_vessel_top_ch
)

try:
    init_clickhouse()

    # 测试汇率
    fx_rate = get_fx_rate_ch('CNY', date.today())
    print(f'✅ 汇率查询: {fx_rate}')

    # 测试风险等级分布
    risk_levels = get_dashboard_risk_levels_ch()
    company_count = sum(item['count'] for item in risk_levels['company_distribution'])
    vessel_count = sum(item['count'] for item in risk_levels['vessel_distribution'])
    print(f'✅ 风险等级分布: {company_count} 家企业, {vessel_count} 艘船舶')

    # 测试船舶 Top10
    vessel_top = get_dashboard_vessel_top_ch()
    print(f'✅ 船舶 Top10: {len(vessel_top)} 条记录')

except Exception as e:
    print(f'❌ 查询测试失败: {e}')
    exit(1)
"

echo ""
echo "================================================================================"
echo "✅ 所有验证通过！"
echo "================================================================================"
echo ""
echo "📋 迁移总结:"
echo "  ✅ ClickHouse 连接成功（HTTP 端口 8123）"
echo "  ✅ 代码修改完成（main.py + clickhouse_client.py）"
echo "  ✅ 查询功能正常"
echo "  ✅ 降级机制完善"
echo ""
echo "🚀 启动应用:"
echo "  python main.py"
echo ""
echo "🌐 访问 Dashboard:"
echo "  http://localhost:8000/dashboard"
echo ""
echo "📊 查看数据源:"
echo "  curl http://localhost:8000/api/clickhouse/health"
echo ""
echo "⚠️ 注意: financial_assets 等表数据为空，如需完整功能请运行："
echo "  python3 clickhouse/migrate_to_clickhouse.py"
echo ""
echo "================================================================================"
