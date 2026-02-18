import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, sum as fsum, count as fcount, current_date


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing env var: {name}")
    return value


def main() -> None:
    spark = (
        SparkSession.builder.appName("silvernav-aggregate-dashboard")
        .config("spark.jars", os.getenv("PG_JDBC_JAR", "/usr/share/java/postgresql.jar"))
        .getOrCreate()
    )

    hdfs_base = env("HDFS_BASE", "hdfs:///silvernav/raw")

    assets = spark.read.parquet(f"{hdfs_base}/financial_assets")
    companies = spark.read.parquet(f"{hdfs_base}/companies")
    vessels = spark.read.parquet(f"{hdfs_base}/vessels")

    # 仅示例：CNY 口径的快照（无需换算）
    snapshot = (
        assets.filter(col("is_active") == True)
        .agg(
            fsum(col("outstanding_amount")).alias("total_exposure"),
            fsum(col("outstanding_amount") * (col("risk_level") == "high").cast("double")).alias(
                "high_risk_exposure"
            ),
            fcount(lit(1)).alias("asset_count"),
        )
        .withColumn("snapshot_date", current_date())
        .withColumn("snapshot_type", lit("daily"))
        .withColumn("currency", lit("CNY"))
    )

    high_risk_company_count = (
        companies.filter((col("is_active") == True) & (col("risk_level") == "high"))
        .count()
    )
    high_risk_vessel_count = (
        vessels.filter((col("is_active") == True) & (col("risk_level") == "high"))
        .count()
    )

    snapshot = snapshot.withColumn("high_risk_company_count", lit(high_risk_company_count)).withColumn(
        "high_risk_vessel_count", lit(high_risk_vessel_count)
    )

    host = env("PG_HOST")
    port = env("PG_PORT", "5432")
    db = env("PG_DB")
    user = env("PG_USER")
    password = env("PG_PASSWORD")
    schema = env("PG_SCHEMA", "silvernav")

    url = f"jdbc:postgresql://{host}:{port}/{db}?currentSchema={schema}"
    props = {
        "user": user,
        "password": password,
        "driver": "org.postgresql.Driver",
        "stringtype": "unspecified",
    }

    # 写回快照表（financial_risk_snapshot）
    snapshot.select(
        "snapshot_date",
        "snapshot_type",
        "high_risk_exposure",
        "high_risk_company_count",
        "high_risk_vessel_count",
        "currency",
    ).write.jdbc(url=url, table=f"{schema}.financial_risk_snapshot", mode="append", properties=props)

    spark.stop()


if __name__ == "__main__":
    main()
