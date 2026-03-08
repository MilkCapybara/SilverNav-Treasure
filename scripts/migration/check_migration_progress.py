#!/usr/bin/env python3
"""
快速查看数据迁移进度
"""
import clickhouse_connect
import psycopg2

# 连接 ClickHouse
ch_client = clickhouse_connect.get_client(
    host='1.15.225.134',
    port=8123,
    username='default',
    password='sun2137405',
    database='silvernav'
)

# 连接 PostgreSQL
pg_conn = psycopg2.connect(
    host='1.15.225.134',
    port=5432,
    database='silvernav_db',
    user='postgres',
    password='sun2137405',
    options='-c search_path=silvernav'
)

print('ClickHouse 数据迁移进度')
print('=' * 80)

tables = ['companies', 'vessels', 'financial_assets', 'fx_rates',
          'vessel_risk_history', 'risk_factor_contribution']

total_target = 0
total_current = 0

for table in tables:
    # 从 PostgreSQL 获取实际数据量
    with pg_conn.cursor() as cur:
        cur.execute(f'SELECT COUNT(*) FROM {table}')
        target = cur.fetchone()[0]

    # 从 ClickHouse 获取当前数据量
    count = ch_client.query(f'SELECT count() FROM {table}').result_rows[0][0]

    total_target += target
    total_current += count
    progress = (count / target) * 100 if target > 0 else 0

    if count >= target:
        status = '✅'
    elif count > 0:
        status = '🔄'
    else:
        status = '⏳'

    print(f'{status} {table:30}: {count:>12,} / {target:>12,} ({progress:>5.1f}%)')

print('=' * 80)
overall_progress = (total_current / total_target) * 100
print(f'总体进度: {total_current:,} / {total_target:,} ({overall_progress:.1f}%)')
print('=' * 80)

pg_conn.close()
ch_client.close()

