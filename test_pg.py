import psycopg2

# 数据库连接参数
conn_params = {
    "host": "1.15.225.134",
    "port": 5432,                # PostgreSQL 默认端口
    "database": "silvernav_db",
    "user": "postgres",
    "password": "sun2137405"
}

try:
    # 建立连接
    conn = psycopg2.connect(**conn_params)
    
    # 打开游标执行 SQL 语句
    cur = conn.cursor()
    
    # 设置当前会话的 schema（方式1：直接执行 SET 命令）
    cur.execute("SET search_path TO silvernav;")
    
    # 或者（方式2：在连接时通过 options 参数指定，但某些情况下可能不生效，推荐方式1）
    # conn = psycopg2.connect(**conn_params, options="-c search_path=silvernav")
    
    # 执行一个测试查询，例如列出当前 schema 下的所有表
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'silvernav'
    """)
    
    tables = cur.fetchall()
    print("当前 schema 中的表：")
    for table in tables:
        print(table[0])
    
    # 关闭游标和连接
    cur.close()
    conn.close()
    
except psycopg2.Error as e:
    print(f"数据库连接或操作失败：{e}")