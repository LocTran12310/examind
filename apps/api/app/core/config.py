from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://examind:examind@localhost:55442/examind"
    s3_endpoint: str = "http://localhost:59100"
    s3_access_key: str = "examind"
    s3_secret_key: str = "examind-secret"
    s3_bucket: str = "examind"
    jwt_secret: str = "change-me-in-production-please-32b"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    cookie_secure: bool = False
    superadmin_username: str = "admin"
    superadmin_password: str = "admin12345"
    ollama_url: str = "http://localhost:11434"
    app_encryption_key: str = ""
    llm_timeout_seconds: int = 120
    log_level: str = "info"
    # business calendar: timestamps are stored and sent in UTC, days are Vietnamese days
    business_tz: str = "Asia/Ho_Chi_Minh"
    login_max_failures: int = 5
    login_lock_minutes: int = 15
    login_ip_per_minute: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
