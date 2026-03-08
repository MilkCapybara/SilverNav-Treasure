#!/usr/bin/env python3
"""
完整数据迁移脚本 - 迁移所有表
"""
import sys
import time
import psycopg2
import clickhouse_connect
from datetime import datetime

# 配置
PG_CONFIG = {
    'host': '1.15.225.134',
    'port': 5432,
    'database': 'silvernav_db',
    'user': 'postgres',
    'password': 'sun2137405',
    'options': '-c search_path=silvernav'
}

BATCH_SIZE = 100000  # 每批 10 万条

print("=" * 80)
print("完整数据迁移到 ClickHouse")
print("=" * 80)

# 连接数据库
print("\n1. 连接数据库...")
pg_conn = psycopg2.connect(**PG_CONFIG)
ch_client = clickhouse_connect.get_client(
    host='1.15.225.134',
    port=8123,
    username='default',
    password='sun2137405',
    database='silvernav'
)
print("✅ 数据库连接成功")

# 要迁移的表（按优先级排序）
tables_to_migrate = [
    ('companies', ['id', 'company_name', 'registration_country', 'company_type', 'credit_score', 'risk_level', 'is_active', 'created_at']),
    ('vessels', ['id', 'imo_number', 'vessel_name', 'vessel_type', 'build_year', 'flag_country', 'owner_company_id', 'asset_risk_score', 'risk_level', 'is_active', 'created_at']),
    ('vessel_risk_history', ['id', 'vessel_id', 'assessment_date', 'risk_score', 'risk_level', 'created_at']),
    ('risk_factor_contribution', ['id', 'target_type', 'target_id', 'factor_name', 'factor_value', 'contribution', 'model_version', 'created_at'])
]

# 迁移每个表
for table_name, columns in tables_to_migrate:
    print(f"\n{'=' * 80}")
    print(f"迁移表: {table_name}")
    print('=' * 80)

    # 检查 PostgreSQL 记录数
    with pg_conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        pg_total = cur.fetchone()[0]

    # 检查 ClickHouse 当前记录数
    ch_current = ch_client.query(f'SELECT count() FROM {table_name}').result_rows[0][0]

    print(f"PostgreSQL: {pg_total:,} 条")
    print(f"ClickHouse: {ch_current:,} 条")

    if pg_total == 0:
        print(f"⚠️ PostgreSQL 表为空，跳过")
        continue

    if ch_current == pg_total:
        print(f"✅ 数据已完整，跳过")
        continue

    if ch_current > 0:
        print(f"⚠️ ClickHouse 表已有数据")
        print("正在清空表...")
        ch_client.command(f'TRUNCATE TABLE {table_name}')
        print("✅ 表已清空")

    # 计算批次数
    num_batches = (pg_total + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"批次大小: {BATCH_SIZE:,}")
    print(f"总批次数: {num_batches:,}")
    print()

    # 分批迁移
    column_list = ', '.join(columns)
    migrated_count = 0
    start_time = time.time()

    for batch_num in range(num_batches):
        offset = batch_num * BATCH_SIZE
        batch_start = time.time()

        # 读取一批数据
        with pg_conn.cursor() as cur:
            cur.execute(f"SELECT {column_list} FROM {table_name} ORDER BY id LIMIT {BATCH_SIZE} OFFSET {offset}")
            rows = cur.fetchall()

        if not rows:
            break

        # 格式化数据
        formatted_rows = []
        for row in rows:
            formatted_row = []
            for val in row:
                if val is None:
                    formatted_row.append(None)
                elif isinstance(val, bool):
                    formatted_row.append(1 if val else 0)
                else:
                    formatted_row.append(val)
            formatted_rows.append(formatted_row)

        # 插入到 ClickHouse
        try:
            ch_client.insert(table_name, formatted_rows, column_names=columns)
            migrated_count += len(rows)

            # 计算进度和速度
            batch_time = time.time() - batch_start
            elapsed_time = time.time() - start_time
            progress = (migrated_count / pg_total) * 100
            speed = migrated_count / elapsed_time if elapsed_time > 0 else 0
            eta = (pg_total - migrated_count) / speed if speed > 0 else 0

            print(f"批次 {batch_num + 1}/{num_batches} | "
                  f"已迁移: {migrated_count:,}/{pg_total:,} ({progress:.1f}%) | "
                  f"速度: {speed:,.0f} 条/秒 | "
                  f"预计剩余: {eta/60:.1f} 分钟")

        except Exception as e:
            print(f"❌ 批次 {batch_num + 1} 失败: {e}")
            break

    # 验证
    print()
    ch_count = ch_client.query(f'SELECT count() FROM {table_name}').result_rows[0][0]
    print(f"✅ 迁移完成")
    print(f"   PostgreSQL: {pg_total:,} 条")
    print(f"   ClickHouse: {ch_count:,} 条")

    if ch_count == pg_total:
        print(f"   ✅ 数据验证通过")
    else:
        print(f"   ⚠️ 数据不一致")

# 关闭连接
pg_conn.close()
ch_client.close()

print("\n" + "=" * 80)
print("✅ 所有数据迁移完成")
print("=" * 80)
print("\n运行以下命令查看最终状态：")
print("    python3 check_migration_progress.py")
print("\n启动应用：")
print("    python main.py")
print("=" * 80)
