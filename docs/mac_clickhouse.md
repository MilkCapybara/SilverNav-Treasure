# 🚀 MacBook Pro M4 使用 Docker 部署 ClickHouse 完整指南

## 📋 目录

1. [环境准备](#环境准备)
2. [Docker 安装](#docker-安装)
3. [ClickHouse 部署](#clickhouse-部署)
4. [配置优化](#配置优化)
5. [数据导入](#数据导入)
6. [性能测试](#性能测试)
7. [常见问题](#常见问题)

---

## 🔧 环境准备

### 系统要求

- **设备**: MacBook Pro M4 (Apple Silicon)
- **操作系统**: macOS Sonoma 14.0+ 或 macOS Sequoia 15.0+
- **内存**: 建议 16GB 以上
- **磁盘空间**: 至少 20GB 可用空间
- **架构**: ARM64 (Apple Silicon)

### 检查系统信息

```bash
# 查看系统版本
sw_vers

# 查看芯片架构
uname -m
# 输出应该是: arm64

# 查看内存
sysctl hw.memsize
```

---

## 🐳 Docker 安装

### 方式一：使用 Docker Desktop（推荐）

#### 1. 下载 Docker Desktop

访问官网下载 Apple Silicon 版本：
```
https://www.docker.com/products/docker-desktop/
```

选择 **Mac with Apple silicon** 版本下载。

#### 2. 安装 Docker Desktop

```bash
# 打开下载的 .dmg 文件
# 将 Docker 拖拽到 Applications 文件夹
# 启动 Docker Desktop

# 验证安装
docker --version
docker-compose --version
```

#### 3. 配置 Docker Desktop

打开 Docker Desktop 设置：

**Resources（资源配置）**:
```
CPUs: 4-6 核（根据你的 M4 配置）
Memory: 8-12 GB
Swap: 2 GB
Disk image size: 60 GB
```

**Docker Engine（引擎配置）**:
```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "features": {
    "buildkit": true
  }
}
```

### 方式二：使用 Homebrew 安装

```bash
# 安装 Docker
brew install --cask docker

# 启动 Docker
open /Applications/Docker.app

# 验证安装
docker --version
```

---

## 🗄️ ClickHouse 部署

### 方案一：单机部署（开发/测试环境）

#### 1. 创建项目目录

```bash
# 创建 ClickHouse 工作目录
mkdir -p ~/clickhouse-docker
cd ~/clickhouse-docker

# 创建数据和配置目录
mkdir -p data logs config
```

#### 2. 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    container_name: clickhouse-server
    hostname: clickhouse
    platform: linux/arm64
    ports:
      - "8123:8123"    # HTTP 接口
      - "9000:9000"    # Native 接口
      - "9009:9009"    # 集群通信
    volumes:
      - ./data:/var/lib/clickhouse
      - ./logs:/var/log/clickhouse-server
      - ./config:/etc/clickhouse-server/config.d
    environment:
      CLICKHOUSE_DB: default
      CLICKHOUSE_USER: admin
      CLICKHOUSE_PASSWORD: clickhouse123
      CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1
    ulimits:
      nofile:
        soft: 262144
        hard: 262144
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "clickhouse-client", "--query", "SELECT 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

#### 3. 启动 ClickHouse

```bash
# 启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f clickhouse

# 检查容器状态
docker-compose ps
```

#### 4. 验证部署

```bash
# 使用 HTTP 接口测试
curl 'http://localhost:8123/?query=SELECT%20version()'

# 使用 clickhouse-client 连接
docker exec -it clickhouse-server clickhouse-client

# 在 clickhouse-client 中执行
SELECT version();
SHOW DATABASES;
```

---

### 方案二：带持久化配置的部署（生产环境）

#### 1. 创建自定义配置文件

创建 `config/users.xml`:

```xml
<?xml version="1.0"?>
<clickhouse>
    <profiles>
        <default>
            <max_memory_usage>10000000000</max_memory_usage>
            <use_uncompressed_cache>0</use_uncompressed_cache>
            <load_balancing>random</load_balancing>
        </default>
    </profiles>

    <users>
        <admin>
            <password>clickhouse123</password>
            <networks>
                <ip>::/0</ip>
            </networks>
            <profile>default</profile>
            <quota>default</quota>
        </admin>
    </users>

    <quotas>
        <default>
            <interval>
                <duration>3600</duration>
                <queries>0</queries>
                <errors>0</errors>
                <result_rows>0</result_rows>
                <read_rows>0</read_rows>
                <execution_time>0</execution_time>
            </interval>
        </default>
    </quotas>
</clickhouse>
```

创建 `config/config.xml`:

```xml
<?xml version="1.0"?>
<clickhouse>
    <logger>
        <level>information</level>
        <log>/var/log/clickhouse-server/clickhouse-server.log</log>
        <errorlog>/var/log/clickhouse-server/clickhouse-server.err.log</errorlog>
        <size>1000M</size>
        <count>10</count>
    </logger>

    <http_port>8123</http_port>
    <tcp_port>9000</tcp_port>
    <interserver_http_port>9009</interserver_http_port>

    <listen_host>::</listen_host>

    <max_connections>4096</max_connections>
    <keep_alive_timeout>3</keep_alive_timeout>
    <max_concurrent_queries>100</max_concurrent_queries>
    <uncompressed_cache_size>8589934592</uncompressed_cache_size>
    <mark_cache_size>5368709120</mark_cache_size>

    <path>/var/lib/clickhouse/</path>
    <tmp_path>/var/lib/clickhouse/tmp/</tmp_path>
    <user_files_path>/var/lib/clickhouse/user_files/</user_files_path>

    <timezone>Asia/Shanghai</timezone>
</clickhouse>
```

#### 2. 更新 docker-compose.yml

```yaml
version: '3.8'

services:
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    container_name: clickhouse-server
    hostname: clickhouse
    platform: linux/arm64
    ports:
      - "8123:8123"
      - "9000:9000"
      - "9009:9009"
    volumes:
      - ./data:/var/lib/clickhouse
      - ./logs:/var/log/clickhouse-server
      - ./config/users.xml:/etc/clickhouse-server/users.xml
      - ./config/config.xml:/etc/clickhouse-server/config.d/custom.xml
    environment:
      TZ: Asia/Shanghai
    ulimits:
      nofile:
        soft: 262144
        hard: 262144
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "clickhouse-client", "--query", "SELECT 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

#### 3. 重启服务

```bash
# 停止并删除旧容器
docker-compose down

# 启动新配置
docker-compose up -d

# 查看日志确认启动成功
docker-compose logs -f
```

---

## ⚙️ 配置优化

### M4 芯片性能优化

#### 1. 内存配置

```xml
<!-- config/memory.xml -->
<?xml version="1.0"?>
<clickhouse>
    <max_server_memory_usage>12000000000</max_server_memory_usage>
    <max_memory_usage>10000000000</max_memory_usage>
    <max_bytes_before_external_group_by>8000000000</max_bytes_before_external_group_by>
    <max_bytes_before_external_sort>8000000000</max_bytes_before_external_sort>
</clickhouse>
```

#### 2. 并发配置

```xml
<!-- config/concurrency.xml -->
<?xml version="1.0"?>
<clickhouse>
    <max_concurrent_queries>100</max_concurrent_queries>
    <max_threads>8</max_threads>
    <background_pool_size>16</background_pool_size>
    <background_schedule_pool_size>16</background_schedule_pool_size>
</clickhouse>
```

#### 3. 网络配置

```xml
<!-- config/network.xml -->
<?xml version="1.0"?>
<clickhouse>
    <max_connections>4096</max_connections>
    <keep_alive_timeout>3</keep_alive_timeout>
    <tcp_keep_alive_timeout>3</tcp_keep_alive_timeout>
</clickhouse>
```

---

## 📊 数据导入

### 方式一：从 CSV 导入

#### 1. 创建表

```sql
-- 连接到 ClickHouse
docker exec -it clickhouse-server clickhouse-client

-- 创建数据库
CREATE DATABASE IF NOT EXISTS silvernav;

-- 使用数据库
USE silvernav;

-- 创建表（以 AIS 轨迹为例）
CREATE TABLE ais_tracks (
    imo_number String,
    vessel_name String,
    timestamp DateTime,
    latitude Float64,
    longitude Float64,
    speed Float32,
    course Float32,
    status String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (imo_number, timestamp)
SETTINGS index_granularity = 8192;
```

#### 2. 导入 CSV 数据

```bash
# 准备 CSV 文件
cat > /tmp/ais_data.csv << 'EOF'
imo_number,vessel_name,timestamp,latitude,longitude,speed,course,status
IMO9000001,VESSEL_001,2026-02-01 00:00:00,31.2304,121.4737,12.5,90.0,underway
IMO9000002,VESSEL_002,2026-02-01 00:00:00,22.3193,114.1694,8.3,180.0,anchored
EOF

# 导入数据
docker exec -i clickhouse-server clickhouse-client --query="
INSERT INTO silvernav.ais_tracks FORMAT CSVWithNames
" < /tmp/ais_data.csv

# 验证导入
docker exec -it clickhouse-server clickhouse-client --query="
SELECT count(*) FROM silvernav.ais_tracks
"
```

### 方式二：从 PostgreSQL 同步

#### 1. 安装 Python 客户端

```bash
pip install clickhouse-driver psycopg2-binary
```

#### 2. 创建同步脚本

```python
# sync_pg_to_clickhouse.py
from clickhouse_driver import Client
import psycopg2
from datetime import datetime

# PostgreSQL 连接
pg_conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="silvernav_db",
    user="admin",
    password="sun2137405"
)

# ClickHouse 连接
ch_client = Client(
    host='localhost',
    port=9000,
    user='admin',
    password='clickhouse123',
    database='silvernav'
)

# 查询 PostgreSQL 数据
pg_cursor = pg_conn.cursor()
pg_cursor.execute("""
    SELECT
        imo_number,
        vessel_name,
        vessel_type,
        flag_state,
        built_year,
        gross_tonnage,
        created_at
    FROM vessels
    WHERE created_at > %s
""", (datetime(2026, 1, 1),))

# 批量插入 ClickHouse
batch_size = 10000
batch = []

for row in pg_cursor:
    batch.append(row)

    if len(batch) >= batch_size:
        ch_client.execute(
            'INSERT INTO vessels VALUES',
            batch
        )
        print(f"✅ 已同步 {len(batch)} 条数据")
        batch = []

# 插入剩余数据
if batch:
    ch_client.execute('INSERT INTO vessels VALUES', batch)
    print(f"✅ 已同步 {len(batch)} 条数据")

pg_cursor.close()
pg_conn.close()
print("🎉 数据同步完成！")
```

#### 3. 运行同步

```bash
python sync_pg_to_clickhouse.py
```

### 方式三：从 MongoDB 同步

```python
# sync_mongo_to_clickhouse.py
from clickhouse_driver import Client
from pymongo import MongoClient
from datetime import datetime

# MongoDB 连接
mongo_client = MongoClient(
    host='1.15.225.134',
    port=27017,
    username='admin',
    password='sun2137405',
    authSource='admin'
)
mongo_db = mongo_client['silvernav']

# ClickHouse 连接
ch_client = Client(
    host='localhost',
    port=9000,
    user='admin',
    password='clickhouse123',
    database='silvernav'
)

# 查询 MongoDB 数据
cursor = mongo_db.ais_tracks.find(
    {'timestamp': {'$gte': datetime(2026, 2, 1)}},
    batch_size=10000
)

# 批量插入
batch = []
batch_size = 10000
count = 0

for doc in cursor:
    batch.append((
        doc.get('imo_number'),
        doc.get('vessel_name'),
        doc.get('timestamp'),
        doc.get('latitude'),
        doc.get('longitude'),
        doc.get('speed'),
        doc.get('course'),
        doc.get('status')
    ))

    if len(batch) >= batch_size:
        ch_client.execute(
            'INSERT INTO ais_tracks VALUES',
            batch
        )
        count += len(batch)
        print(f"✅ 已同步 {count:,} 条数据")
        batch = []

# 插入剩余数据
if batch:
    ch_client.execute('INSERT INTO ais_tracks VALUES', batch)
    count += len(batch)
    print(f"✅ 已同步 {count:,} 条数据")

print(f"🎉 数据同步完成！总计: {count:,} 条")
```

---

## 🚀 性能测试

### 1. 基准测试

```sql
-- 连接到 ClickHouse
docker exec -it clickhouse-server clickhouse-client

-- 测试查询性能
SELECT
    imo_number,
    count(*) as track_count,
    avg(speed) as avg_speed,
    max(speed) as max_speed
FROM ais_tracks
WHERE timestamp >= '2026-02-01'
GROUP BY imo_number
ORDER BY track_count DESC
LIMIT 10;

-- 查看查询执行时间
-- ClickHouse 会自动显示执行时间
```

### 2. 聚合性能测试

```sql
-- 复杂聚合查询
SELECT
    toYYYYMMDD(timestamp) as date,
    imo_number,
    count(*) as points,
    avg(speed) as avg_speed,
    stddevPop(speed) as speed_stddev,
    quantile(0.5)(speed) as median_speed,
    quantile(0.95)(speed) as p95_speed
FROM ais_tracks
WHERE timestamp >= '2026-01-01'
GROUP BY date, imo_number
HAVING points > 100
ORDER BY date DESC, points DESC
LIMIT 100;
```

### 3. 性能对比

```bash
# 创建测试脚本
cat > benchmark.sh << 'EOF'
#!/bin/bash

echo "🚀 ClickHouse 性能测试"
echo "====================="

# 测试 1: 简单查询
echo "测试 1: 简单 COUNT 查询"
time docker exec clickhouse-server clickhouse-client --query="
SELECT count(*) FROM silvernav.ais_tracks
"

# 测试 2: 聚合查询
echo "测试 2: GROUP BY 聚合查询"
time docker exec clickhouse-server clickhouse-client --query="
SELECT imo_number, count(*) as cnt
FROM silvernav.ais_tracks
GROUP BY imo_number
ORDER BY cnt DESC
LIMIT 10
"

# 测试 3: 复杂分析查询
echo "测试 3: 复杂分析查询"
time docker exec clickhouse-server clickhouse-client --query="
SELECT
    toYYYYMMDD(timestamp) as date,
    count(*) as total,
    avg(speed) as avg_speed,
    quantile(0.95)(speed) as p95_speed
FROM silvernav.ais_tracks
WHERE timestamp >= '2026-02-01'
GROUP BY date
ORDER BY date
"

echo "✅ 测试完成！"
EOF

chmod +x benchmark.sh
./benchmark.sh
```

---

## 🔍 常见问题

### 问题 1: 容器启动失败

**症状**: `docker-compose up` 失败

**解决方案**:

```bash
# 检查端口占用
lsof -i :8123
lsof -i :9000

# 清理旧容器
docker-compose down -v
docker system prune -a

# 重新启动
docker-compose up -d
```

### 问题 2: 权限错误

**症状**: `Permission denied` 错误

**解决方案**:

```bash
# 修改数据目录权限
sudo chown -R $(whoami) ./data ./logs ./config

# 或者使用 Docker 用户
docker-compose down
docker-compose up -d
```

### 问题 3: 内存不足

**症状**: `Memory limit exceeded` 错误

**解决方案**:

```xml
<!-- 降低内存限制 -->
<max_memory_usage>4000000000</max_memory_usage>
<max_bytes_before_external_group_by>2000000000</max_bytes_before_external_group_by>
```

### 问题 4: M4 架构兼容性

**症状**: `exec format error`

**解决方案**:

```yaml
# 确保使用 ARM64 镜像
services:
  clickhouse:
    platform: linux/arm64
    image: clickhouse/clickhouse-server:latest
```

### 问题 5: 连接超时

**症状**: 无法连接到 ClickHouse

**解决方案**:

```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs clickhouse

# 测试网络连接
curl http://localhost:8123/ping

# 进入容器检查
docker exec -it clickhouse-server bash
clickhouse-client --query "SELECT 1"
```

---

## 📚 常用命令

### Docker 管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f clickhouse

# 查看资源使用
docker stats clickhouse-server

# 进入容器
docker exec -it clickhouse-server bash

# 备份数据
docker exec clickhouse-server clickhouse-client --query="BACKUP DATABASE silvernav TO Disk('backups', 'backup.zip')"
```

### ClickHouse 管理

```bash
# 连接客户端
docker exec -it clickhouse-server clickhouse-client

# 执行查询
docker exec clickhouse-server clickhouse-client --query="SELECT version()"

# 查看数据库
docker exec clickhouse-server clickhouse-client --query="SHOW DATABASES"

# 查看表
docker exec clickhouse-server clickhouse-client --query="SHOW TABLES FROM silvernav"

# 查看表结构
docker exec clickhouse-server clickhouse-client --query="DESCRIBE TABLE silvernav.ais_tracks"

# 优化表
docker exec clickhouse-server clickhouse-client --query="OPTIMIZE TABLE silvernav.ais_tracks FINAL"
```

---

## 🎯 最佳实践

### 1. 表设计

```sql
-- 使用合适的引擎
ENGINE = MergeTree()

-- 按时间分区
PARTITION BY toYYYYMM(timestamp)

-- 合理的排序键
ORDER BY (imo_number, timestamp)

-- 适当的索引粒度
SETTINGS index_granularity = 8192
```

### 2. 查询优化

```sql
-- 使用 PREWHERE 过滤
SELECT * FROM ais_tracks
PREWHERE timestamp >= '2026-02-01'
WHERE speed > 10;

-- 使用物化视图
CREATE MATERIALIZED VIEW ais_daily_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, imo_number)
AS SELECT
    toDate(timestamp) as date,
    imo_number,
    count() as track_count,
    avg(speed) as avg_speed
FROM ais_tracks
GROUP BY date, imo_number;
```

### 3. 数据管理

```sql
-- 定期清理旧数据
ALTER TABLE ais_tracks DROP PARTITION '202601';

-- 压缩数据
OPTIMIZE TABLE ais_tracks FINAL;

-- 检查表大小
SELECT
    table,
    formatReadableSize(sum(bytes)) as size
FROM system.parts
WHERE database = 'silvernav'
GROUP BY table;
```

---

## 🔗 相关资源

- [ClickHouse 官方文档](https://clickhouse.com/docs)
- [Docker Hub - ClickHouse](https://hub.docker.com/r/clickhouse/clickhouse-server)
- [ClickHouse Python Driver](https://github.com/mymarilyn/clickhouse-driver)
- [ClickHouse 性能优化指南](https://clickhouse.com/docs/en/operations/optimizing-performance/)

---

## 📝 总结

本指南提供了在 MacBook Pro M4 上使用 Docker 部署 ClickHouse 的完整方案，包括：

✅ Docker 环境配置
✅ ClickHouse 单机部署
✅ 性能优化配置
✅ 数据导入方案
✅ 性能测试方法
✅ 常见问题解决

通过本指南，你可以快速在 M4 芯片的 Mac 上搭建高性能的 ClickHouse OLAP 数据库，用于大数据分析和实时查询。

---

**创建时间**: 2026-02-27
**适用设备**: MacBook Pro M4 (Apple Silicon)
**ClickHouse 版本**: Latest (24.x)
**Docker 版本**: 24.0+
