"""配置模块"""
import os


class Settings:
    """应用配置"""
    # PostgreSQL配置
    db_host = os.getenv("SILVERNAV_DB_HOST", "1.15.225.134")
    db_port = int(os.getenv("SILVERNAV_DB_PORT", "5432"))
    db_name = os.getenv("SILVERNAV_DB_NAME", "silvernav_db")
    db_schema = os.getenv("SILVERNAV_DB_SCHEMA", "silvernav")

    admin_user = os.getenv("SILVERNAV_DB_ADMIN_USER", "postgres")
    admin_password = os.getenv("SILVERNAV_DB_ADMIN_PASSWORD", "sun2137405")

    read_user = os.getenv("SILVERNAV_DB_READ_USER", "wjyandghx")
    read_password = os.getenv("SILVERNAV_DB_READ_PASSWORD", "ghxandwjy")

    # MongoDB配置
    mongo_host = os.getenv("SILVERNAV_MONGO_HOST", "1.15.225.134")
    mongo_port = int(os.getenv("SILVERNAV_MONGO_PORT", "27017"))
    mongo_db = os.getenv("SILVERNAV_MONGO_DB", "silvernav")
    mongo_user = os.getenv("SILVERNAV_MONGO_USER", "admin")
    mongo_password = os.getenv("SILVERNAV_MONGO_PASSWORD", "sun2137405")
    mongo_auth_source = os.getenv("SILVERNAV_MONGO_AUTH_SOURCE", "admin")

    # 认证配置
    root_account = os.getenv("SILVERNAV_ROOT_ACCOUNT", "root")
    root_password = os.getenv("SILVERNAV_ROOT_PASSWORD", "sunfannb0307SF?")

    token_secret = os.getenv("SILVERNAV_TOKEN_SECRET", "silvernav_dev_secret_change_me")
    token_ttl_hours = int(os.getenv("SILVERNAV_TOKEN_TTL_HOURS", "12"))

    # Redis配置
    redis_host = os.getenv("SILVERNAV_REDIS_HOST", "1.15.225.134")
    redis_port = int(os.getenv("SILVERNAV_REDIS_PORT", "6379"))
    redis_db = int(os.getenv("SILVERNAV_REDIS_DB", "0"))
    redis_password = os.getenv("SILVERNAV_REDIS_PASSWORD", "sun2137405")

    # Kafka配置
    kafka_bootstrap_servers = os.getenv("SILVERNAV_KAFKA_SERVERS", "1.15.225.134:9092")
    kafka_ais_topic = os.getenv("SILVERNAV_KAFKA_AIS_TOPIC", "ais.raw")
    kafka_alert_topic = os.getenv("SILVERNAV_KAFKA_ALERT_TOPIC", "alerts.realtime")


settings = Settings()
