"""配置模块"""
import os


class Settings:
    """应用配置"""
    db_host = os.getenv("SILVERNAV_DB_HOST", "1.15.225.134")
    db_port = int(os.getenv("SILVERNAV_DB_PORT", "5432"))
    db_name = os.getenv("SILVERNAV_DB_NAME", "silvernav_db")
    db_schema = os.getenv("SILVERNAV_DB_SCHEMA", "silvernav")

    admin_user = os.getenv("SILVERNAV_DB_ADMIN_USER", "postgres")
    admin_password = os.getenv("SILVERNAV_DB_ADMIN_PASSWORD", "sun2137405")

    read_user = os.getenv("SILVERNAV_DB_READ_USER", "wjyandghx")
    read_password = os.getenv("SILVERNAV_DB_READ_PASSWORD", "ghxandwjy")

    root_account = os.getenv("SILVERNAV_ROOT_ACCOUNT", "root")
    root_password = os.getenv("SILVERNAV_ROOT_PASSWORD", "sunfannb0307SF?")

    token_secret = os.getenv("SILVERNAV_TOKEN_SECRET", "silvernav_dev_secret_change_me")
    token_ttl_hours = int(os.getenv("SILVERNAV_TOKEN_TTL_HOURS", "12"))


settings = Settings()
