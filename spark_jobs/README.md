# Spark JDBC -> HDFS -> 聚合

## 1) 安装 JDBC 驱动（Ubuntu 22.04）
推荐直接用系统包：
```
sudo apt update
sudo apt install -y libpostgresql-jdbc-java
```
默认 jar 路径通常是：
```
/usr/share/java/postgresql.jar
```

如果你想用指定版本，也可以从 PostgreSQL 官方 JDBC 页面下载 jar，放到 `/opt/jars/`，然后 `spark-submit --jars /opt/jars/postgresql.jar`。

## 2) 从 PostgreSQL 拉数据到 HDFS
设置环境变量：
```
export PG_HOST=1.15.225.134
export PG_PORT=5432
export PG_DB=silvernav_db
export PG_SCHEMA=silvernav
export PG_USER=wjyandghx
export PG_PASSWORD=ghxandwjy
export HDFS_BASE=hdfs:///silvernav/raw
export PG_JDBC_JAR=/usr/share/java/postgresql.jar
```

执行：
```
$SPARK_HOME/bin/spark-submit \
  --jars $PG_JDBC_JAR \
  /Users/sunfanmacpro/Desktop/SilverNav-Treasure/spark_jobs/pg_to_hdfs.py
```

## 3) 聚合并写回 PostgreSQL
```
$SPARK_HOME/bin/spark-submit \
  --jars $PG_JDBC_JAR \
  /Users/sunfanmacpro/Desktop/SilverNav-Treasure/spark_jobs/aggregate_dashboard.py
```

## 4) 页面渲染方式建议
- **实时大屏**：后端仍读 PostgreSQL（或物化视图/快照表）
- **重计算指标**：通过 Spark 批处理生成 `financial_risk_snapshot` 等表
- **强交互**：Spark/Presto/Trino 不适合直接驱动前端页面，最好落地到 Postgres 或缓存层
