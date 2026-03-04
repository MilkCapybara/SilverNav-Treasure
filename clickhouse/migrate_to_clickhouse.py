#!/usr/bin/env python3
"""
银航宝 PostgreSQL 到 ClickHouse 数据迁移脚本
功能：多线程批量迁移 Dashboard 相关表数据
作者：Claude
日期：2026-02-27
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Tuple, Dict, Any

import psycopg2
from clickhouse_driver import Client
from psycopg2.extras import RealDictCursor


# ============================================================================
# 配置
# ============================================================================

# PostgreSQL 配置
PG_CONFIG = {
    'host': '1.15.225.134',
    'port': 5432,
    'database': 'silvernav_db',
    'user': 'postgres',
    'password': 'sun2137405',
    'options': '-c search_path=silvernav'
}

# ClickHouse 配置
CH_CONFIG = {
    'host': '1.15.225.134',
    'port': 8123,
    'user': 'default',
    'password': 'sun2137405',
    'database': 'silvernav'
}

# 迁移配置
BATCH_SIZE = 10000  # 每批次插入的记录数
MAX_WORKERS = 6     # 并发线程数
TABLES_TO_MIGRATE = [
    'companies',
    'vessels',
    'financial_assets',
    'vessel_risk_history',
    'risk_factor_contribution',
    'fx_rates'
]


# ============================================================================
# 工具函数
# ============================================================================

def get_pg_connection():
    """获取 PostgreSQL 连接"""
    return psycopg2.connect(**PG_CONFIG)


def get_ch_client():
    """获取 ClickHouse 客户端"""
    return Client(**CH_CONFIG)


def format_value(value):
    """格式化值以适配 ClickHouse"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, bool):
        return 1 if value else 0
    return value


def get_table_count(pg_conn, table_name: str) -> int:
    """获取 PostgreSQL 表的记录数"""
    with pg_conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cur.fetchone()[0]


def get_table_schema(table_name: str) -> List[str]:
    """获取表的列名（按 ClickHouse 表结构）"""
    schemas = {
        'companies': [
            'id', 'company_name', 'registration_country', 'company_type',
            'credit_score', 'risk_level', 'is_active', 'created_at'
        ],
        'vessels': [
            'id', 'imo_number', 'vessel_name', 'vessel_type', 'build_year',
            'flag_country', 'owner_company_id', 'asset_risk_score',
            'risk_level', 'is_active', 'created_at'
        ],
        'financial_assets': [
            'id', 'company_id', 'vessel_id', 'asset_type', 'contract_no',
            'principal_amount', 'outstanding_amount', 'currency',
            'interest_rate', 'start_date', 'maturity_date', 'risk_level',
            'risk_score', 'is_non_performing', 'is_active', 'created_at'
        ],
        'vessel_risk_history': [
            'id', 'vessel_id', 'assessment_date', 'risk_score',
            'risk_level', 'created_at'
        ],
        'risk_factor_contribution': [
            'id', 'target_type', 'target_id', 'factor_name',
            'factor_value', 'contribution', 'model_version', 'created_at'
        ],
        'fx_rates': [
            'id', 'base_currency', 'quote_currency', 'rate',
            'rate_date', 'source', 'created_at'
        ]
    }
    return schemas.get(table_name, [])


# ============================================================================
# 迁移函数
# ============================================================================

def fetch_batch(pg_conn, table_name: str, offset: int, limit: int) -> List[Tuple]:
    """从 PostgreSQL 批量读取数据"""
    columns = get_table_schema(table_name)
    if not columns:
        raise ValueError(f"未知表: {table_name}")

    column_list = ', '.join(columns)
    query = f"SELECT {column_list} FROM {table_name} ORDER BY id LIMIT %s OFFSET %s"

    with pg_conn.cursor() as cur:
        cur.execute(query, (limit, offset))
        rows = cur.fetchall()

    # 格式化数据
    formatted_rows = []
    for row in rows:
        formatted_row = tuple(format_value(v) for v in row)
        formatted_rows.append(formatted_row)

    return formatted_rows


def insert_batch(ch_client: Client, table_name: str, data: List[Tuple]) -> int:
    """批量插入数据到 ClickHouse"""
    if not data:
        return 0

    try:
        ch_client.execute(f'INSERT INTO {table_name} VALUES', data)
        return len(data)
    except Exception as e:
        print(f"❌ 插入失败: {e}")
        raise


def migrate_table_batch(
    table_name: str,
    offset: int,
    limit: int,
    batch_id: int
) -> Tuple[str, int, int, float]:
    """迁移单个批次的数据"""
    start_time = time.time()

    try:
        # 连接数据库
        pg_conn = get_pg_connection()
        ch_client = get_ch_client()

        # 读取数据
        data = fetch_batch(pg_conn, table_name, offset, limit)

        # 插入数据
        inserted = insert_batch(ch_client, table_name, data)

        # 关闭连接
        pg_conn.close()

        elapsed = time.time() - start_time
        return (table_name, batch_id, inserted, elapsed)

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 批次 {batch_id} 失败: {e}")
        return (table_name, batch_id, 0, elapsed)


def migrate_table(table_name: str) -> Dict[str, Any]:
    """迁移整个表"""
    print(f"\n{'='*80}")
    print(f"开始迁移表: {table_name}")
    print(f"{'='*80}")

    start_time = time.time()

    # 获取总记录数
    pg_conn = get_pg_connection()
    total_count = get_table_count(pg_conn, table_name)
    pg_conn.close()

    print(f"📊 总记录数: {total_count:,}")

    if total_count == 0:
        print(f"⚠️  表 {table_name} 为空，跳过迁移")
        return {
            'table': table_name,
            'total': 0,
            'migrated': 0,
            'duration': 0,
            'speed': 0
        }

    # 计算批次数
    num_batches = (total_count + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"📦 批次数: {num_batches} (每批 {BATCH_SIZE:,} 条)")

    # 多线程迁移
    migrated_count = 0
    failed_batches = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []

        # 提交所有批次任务
        for batch_id in range(num_batches):
            offset = batch_id * BATCH_SIZE
            future = executor.submit(
                migrate_table_batch,
                table_name,
                offset,
                BATCH_SIZE,
                batch_id + 1
            )
            futures.append(future)

        # 收集结果
        for future in as_completed(futures):
            table, batch_id, inserted, elapsed = future.result()
            migrated_count += inserted

            if inserted > 0:
                progress = (migrated_count / total_count) * 100
                speed = inserted / elapsed if elapsed > 0 else 0
                print(f"✅ 批次 {batch_id}/{num_batches} | "
                      f"已迁移: {migrated_count:,}/{total_count:,} ({progress:.1f}%) | "
                      f"速度: {speed:.0f} 条/秒")
            else:
                failed_batches.append(batch_id)
                print(f"❌ 批次 {batch_id}/{num_batches} 失败")

    # 统计结果
    duration = time.time() - start_time
    speed = migrated_count / duration if duration > 0 else 0

    print(f"\n{'='*80}")
    print(f"✅ 表 {table_name} 迁移完成")
    print(f"{'='*80}")
    print(f"📊 总记录数: {total_count:,}")
    print(f"✅ 成功迁移: {migrated_count:,}")
    print(f"❌ 失败批次: {len(failed_batches)}")
    print(f"⏱️  耗时: {duration:.2f} 秒")
    print(f"🚀 平均速度: {speed:.0f} 条/秒")

    if failed_batches:
        print(f"⚠️  失败批次: {failed_batches}")

    return {
        'table': table_name,
        'total': total_count,
        'migrated': migrated_count,
        'failed_batches': failed_batches,
        'duration': duration,
        'speed': speed
    }


def verify_migration(table_name: str) -> bool:
    """验证迁移结果"""
    print(f"\n🔍 验证表 {table_name} 的迁移结果...")

    try:
        # 获取 PostgreSQL 记录数
        pg_conn = get_pg_connection()
        pg_count = get_table_count(pg_conn, table_name)
        pg_conn.close()

        # 获取 ClickHouse 记录数
        ch_client = get_ch_client()
        ch_count = ch_client.execute(f'SELECT COUNT(*) FROM {table_name}')[0][0]

        print(f"📊 PostgreSQL: {pg_count:,} 条")
        print(f"📊 ClickHouse: {ch_count:,} 条")

        if pg_count == ch_count:
            print(f"✅ 验证通过: 记录数一致")
            return True
        else:
            diff = abs(pg_count - ch_count)
            print(f"⚠️  验证失败: 差异 {diff:,} 条")
            return False

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    print("="*80)
    print("银航宝 PostgreSQL → ClickHouse 数据迁移工具")
    print("="*80)
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 配置:")
    print(f"   - PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}")
    print(f"   - ClickHouse: {CH_CONFIG['host']}:{CH_CONFIG['port']}/{CH_CONFIG['database']}")
    print(f"   - 批次大小: {BATCH_SIZE:,} 条")
    print(f"   - 并发线程: {MAX_WORKERS}")
    print(f"   - 迁移表数: {len(TABLES_TO_MIGRATE)}")

    # 测试连接
    print(f"\n🔌 测试数据库连接...")
    try:
        pg_conn = get_pg_connection()
        print(f"✅ PostgreSQL 连接成功")
        pg_conn.close()

        ch_client = get_ch_client()
        ch_client.execute('SELECT 1')
        print(f"✅ ClickHouse 连接成功")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        sys.exit(1)

    # 确认迁移
    print(f"\n⚠️  即将迁移以下表:")
    for table in TABLES_TO_MIGRATE:
        print(f"   - {table}")

    confirm = input(f"\n是否继续? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ 取消迁移")
        sys.exit(0)

    # 开始迁移
    overall_start = time.time()
    results = []

    for table_name in TABLES_TO_MIGRATE:
        result = migrate_table(table_name)
        results.append(result)

        # 验证迁移
        verify_migration(table_name)

        # 短暂休息
        time.sleep(1)

    # 总结
    overall_duration = time.time() - overall_start
    total_migrated = sum(r['migrated'] for r in results)
    overall_speed = total_migrated / overall_duration if overall_duration > 0 else 0

    print(f"\n{'='*80}")
    print(f"🎉 所有表迁移完成")
    print(f"{'='*80}")
    print(f"📊 迁移统计:")
    print(f"   - 总表数: {len(results)}")
    print(f"   - 总记录数: {sum(r['total'] for r in results):,}")
    print(f"   - 成功迁移: {total_migrated:,}")
    print(f"   - 总耗时: {overall_duration:.2f} 秒")
    print(f"   - 平均速度: {overall_speed:.0f} 条/秒")

    print(f"\n📋 详细结果:")
    for r in results:
        status = "✅" if r['migrated'] == r['total'] else "⚠️"
        print(f"   {status} {r['table']}: {r['migrated']:,}/{r['total']:,} "
              f"({r['duration']:.1f}s, {r['speed']:.0f} 条/秒)")

    print(f"\n📅 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")

    # 检查是否有失败
    failed_tables = [r for r in results if r['migrated'] < r['total']]
    if failed_tables:
        print(f"\n⚠️  以下表迁移不完整:")
        for r in failed_tables:
            print(f"   - {r['table']}: {r['migrated']:,}/{r['total']:,}")
        sys.exit(1)
    else:
        print(f"\n✅ 所有表迁移成功!")
        sys.exit(0)


if __name__ == '__main__':
    main()
