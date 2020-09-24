from datetime import timedelta

from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn
from tortoise import generate_config


class Settings(BaseSettings):
    env: str = "local"
    postgres_dsn: PostgresDsn = "postgres://postgres:eva@localhost:5432/eva"
    postgres_dsn_test: PostgresDsn = "postgres://postgres:eva@localhost:5432/eva_{}"
    sentry_dsn: AnyHttpUrl = "https://5b9fb59b1df64929a6e8cef2f570aaf7@sentry.poeticloud.com/2"

    argon2_time_cost: int = 2
    argon2_memory_cost: int = 102400
    argon2_parallelism: int = 8
    argon2_hash_len: int = 16
    argon2_salt_len: int = 16

    password_permanent: bool = True  # 密码是否永不过期
    password_age: timedelta = timedelta(days=365)  # 密码有效期（秒）
    security_code_age: timedelta = timedelta(minutes=15)  # 验证码有效期（秒）


settings = Settings()

db_config = generate_config(
    db_url=settings.postgres_dsn,
    app_modules={"models": ["app.models", "aerich.models"]},
)
