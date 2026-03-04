#!/bin/bash

# ============================================================================
# 银航宝 ClickHouse 部署和数据迁移脚本
# 用途：一键完成 ClickHouse 部署、建表、数据迁移
# ============================================================================

set -e  # 遇到错误立即退出

echo "============================================================================"
echo "银航宝 ClickHouse 部署和数据迁移"
echo "============================================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# 步骤 1: 检查 ClickHouse 连接
# ============================================================================
echo "📡 步骤 1/5: 检查 ClickHouse 连接..."
if clickhouse-client --host=1.15.225.134 --port=9000 --user=default --password=sun2137405 --query="SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ ClickHouse 连接成功${NC}"
else
    echo -e "${RED}❌ ClickHouse 连接失败${NC}"
    echo "请检查:"
    echo "  1. ClickHouse 服务是否启动"
    echo "  2. 网络连接是否正常"
    echo "  3. 用户名密码是否正确"
    exit 1
fi

# ============================================================================
# 步骤 2: 安装 Python 依赖
# ============================================================================
echo ""
echo "📦 步骤 2/5: 安装 Python 依赖..."
if pip show clickhouse-driver > /dev/null 2>&1; then
    echo -e "${GREEN}✅ clickhouse-driver 已安装${NC}"
else
    echo "正在安装 clickhouse-driver..."
    pip install clickhouse-driver
fi

if pip show psycopg2-binary > /dev/null 2>&1; then
    echo -e "${GREEN}✅ psycopg2-binary 已安装${NC}"
else
    echo "正在安装 psycopg2-binary..."
    pip install psycopg2-binary
fi

# ============================================================================
# 步骤 3: 创建 ClickHouse 数据库和表
# ============================================================================
echo ""
echo "🗄️  步骤 3/5: 创建 ClickHouse 数据库和表..."

if [ -f "clickhouse/create_tables.sql" ]; then
    echo "正在执行建表脚本..."
    clickhouse-client \
        --host=1.15.225.134 \
        --port=9000 \
        --user=default \
        --password=sun2137405 \
        --multiquery < clickhouse/create_tables.sql

    echo -e "${GREEN}✅ 数据库和表创建成功${NC}"
else
    echo -e "${RED}❌ 找不到建表脚本: clickhouse/create_tables.sql${NC}"
    exit 1
fi

# ============================================================================
# 步骤 4: 数据迁移
# ============================================================================
echo ""
echo "🚀 步骤 4/5: 开始数据迁移..."
echo "⚠️  这可能需要几分钟时间，请耐心等待..."
echo ""

if [ -f "clickhouse/migrate_to_clickhouse.py" ]; then
    python3 clickhouse/migrate_to_clickhouse.py

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 数据迁移成功${NC}"
    else
        echo -e "${RED}❌ 数据迁移失败${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ 找不到迁移脚本: clickhouse/migrate_to_clickhouse.py${NC}"
    exit 1
fi

# ============================================================================
# 步骤 5: 验证数据
# ============================================================================
echo ""
echo "🔍 步骤 5/5: 验证数据..."

echo "检查各表记录数:"
clickhouse-client \
    --host=1.15.225.134 \
    --port=9000 \
    --user=default \
    --password=sun2137405 \
    --query="
    SELECT
        table AS 表名,
        formatReadableQuantity(total_rows) AS 记录数,
        formatReadableSize(total_bytes) AS 数据大小
    FROM system.tables
    WHERE database = 'silvernav'
      AND table IN ('companies', 'vessels', 'financial_assets', 'vessel_risk_history', 'risk_factor_contribution', 'fx_rates')
    ORDER BY table
    FORMAT PrettyCompact
    "

echo ""
echo -e "${GREEN}✅ 验证完成${NC}"

# ============================================================================
# 完成
# ============================================================================
echo ""
echo "============================================================================"
echo -e "${GREEN}🎉 ClickHouse 部署和数据迁移完成！${NC}"
echo "============================================================================"
echo ""
echo "下一步操作:"
echo "  1. 修改 main.py，应用 ClickHouse 查询"
echo "  2. 重启应用: python main.py"
echo "  3. 访问 Dashboard 测试性能"
echo ""
echo "性能对比:"
echo "  - PostgreSQL: ~20秒"
echo "  - ClickHouse: <1秒 (预期)"
echo ""
echo "============================================================================"
