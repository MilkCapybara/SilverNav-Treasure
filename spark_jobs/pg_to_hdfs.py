import os
from pyspark.sql import SparkSession


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing env var: {name}")
    return value


def main() -> None:
    spark = (
        SparkSession.builder.appName("silvernav-pg-to-hdfs")
        .config("spark.jars", os.getenv("PG_JDBC_JAR", "/usr/share/java/postgresql.jar"))
        .getOrCreate()
    )

    host = env("PG_HOST")
    port = env("PG_PORT", "5432")
    db = env("PG_DB")
    user = env("PG_USER")
    password = env("PG_PASSWORD")
    schema = env("PG_SCHEMA", "silvernav")
    hdfs_base = env("HDFS_BASE", "hdfs:///silvernav/raw")

    url = f"jdbc:postgresql://{host}:{port}/{db}?currentSchema={schema}"

    props = {
        "user": user,
        "password": password,
        "driver": "org.postgresql.Driver",
        "fetchsize": "10000",
    }

    tables = [
        "financial_assets",
        "asset_repayment_schedule",
        "companies",
        "vessels",
        "vessel_risk_history",
        "credit_risk_assessment",
        "risk_factor_contribution",
        "fx_rates",
    ]

    for table in tables:
        df = spark.read.jdbc(url=url, table=f"{schema}.{table}", properties=props)
        df.write.mode("overwrite").parquet(f"{hdfs_base}/{table}")
        print(f"Wrote {table} to {hdfs_base}/{table}")

    spark.stop()


if __name__ == "__main__":
    main()
