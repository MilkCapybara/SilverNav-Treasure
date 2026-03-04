#!/usr/bin/env python3
"""
使用 HTTP 接口执行 ClickHouse 建表脚本
"""

import requests
from requests.auth import HTTPBasicAuth

# ClickHouse HTTP 配置
CH_HOST = '1.15.225.134'
CH_PORT = 8123
CH_USER = 'default'
CH_PASSWORD = 'sun2137405'
CH_DATABASE = 'silvernav'

def execute_query(query, database='default'):
    """执行 ClickHouse 查询"""
    url = f'http://{CH_HOST}:{CH_PORT}/'
    params = {'query': query}
    if database != 'default':
        params['database'] = database

    response = requests.post(
        url,
        params=params,
        auth=HTTPBasicAuth(CH_USER, CH_PASSWORD),
        timeout=30
    )

    if response.status_code == 200:
        return True, response.text
    else:
        return False, response.text

# 创建数据库
print('📊 创建 ClickHouse 数据库...')
success, result = execute_query('CREATE DATABASE IF NOT EXISTS silvernav')
if success:
    print('✅ 数据库创建成功')
else:
    print(f'❌ 数据库创建失败: {result}')
    exit(1)

# 读取建表脚本
print('\n🗄️  读取建表脚本...')
with open('clickhouse/create_tables.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# 分割 SQL 语句
sql_statements = []
current_statement = []
in_comment = False

for line in sql_content.split('\n'):
    line = line.strip()

    # 跳过空行和注释
    if not line or line.startswith('--'):
        continue

    # 跳过 USE 语句
    if line.upper().startswith('USE '):
        continue

    # 跳过 SET 语句
    if line.upper().startswith('SET '):
        continue

    current_statement.append(line)

    # 如果行以分号结尾，表示一个完整的语句
    if line.endswith(';'):
        statement = ' '.join(current_statement).strip()
        if statement and not statement.startswith('--'):
            sql_statements.append(statement)
        current_statement = []

print(f'📋 共解析出 {len(sql_statements)} 条 SQL 语句')

# 执行每个 SQL 语句
print('\n🚀 开始执行建表语句...')
success_count = 0
error_count = 0
skip_count = 0

for i, statement in enumerate(sql_statements, 1):
    try:
        # 提取对象名称
        obj_name = 'unknown'
        if 'CREATE TABLE' in statement:
            parts = statement.split('CREATE TABLE')[1].split('(')[0].strip().split()
            obj_name = parts[-1] if parts else 'unknown'
            obj_type = '表'
        elif 'CREATE MATERIALIZED VIEW' in statement:
            parts = statement.split('CREATE MATERIALIZED VIEW')[1].split('ENGINE')[0].strip().split()
            obj_name = parts[-1] if parts else 'unknown'
            obj_type = '物化视图'
        elif 'ALTER TABLE' in statement:
            parts = statement.split('ALTER TABLE')[1].split('ADD')[0].strip().split()
            obj_name = parts[-1] if parts else 'unknown'
            obj_type = '索引'
        else:
            obj_type = '语句'

        # 执行语句
        success, result = execute_query(statement, CH_DATABASE)

        if success:
            print(f'  ✅ {obj_type} {obj_name} 创建成功')
            success_count += 1
        else:
            # 检查是否是"已存在"错误
            if 'already exists' in result or 'EXISTS' in result:
                print(f'  ⚠️  {obj_type} {obj_name} 已存在，跳过')
                skip_count += 1
            else:
                print(f'  ❌ {obj_type} {obj_name} 创建失败: {result[:100]}')
                error_count += 1

    except Exception as e:
        print(f'  ❌ 执行失败: {str(e)[:100]}')
        error_count += 1

print(f'\n{"="*80}')
print(f'✅ 建表完成')
print(f'{"="*80}')
print(f'  成功: {success_count} 个')
print(f'  跳过: {skip_count} 个')
print(f'  失败: {error_count} 个')

# 检查创建的表
print(f'\n📋 检查创建的表...')
success, result = execute_query('SHOW TABLES', CH_DATABASE)
if success:
    tables = result.strip().split('\n')
    print(f'当前有 {len(tables)} 个表:')
    for table in tables:
        if table:
            print(f'  - {table}')
else:
    print(f'❌ 查询表列表失败: {result}')

print(f'\n{"="*80}')
print('🎉 ClickHouse 建表完成！')
print('下一步: 运行数据迁移脚本')
print('  python3 clickhouse/migrate_to_clickhouse.py')
print(f'{"="*80}')
