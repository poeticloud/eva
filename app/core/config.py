from datetime import timedelta
from typing import List, Optional, Union

from authlib.jose import RSAKey
from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, SecretStr
from tortoise import generate_config


class Settings(BaseSettings):
    env: str = "local"
    postgres_dsn: PostgresDsn = "postgres://postgres:eva@localhost:5432/eva"
    postgres_dsn_test: PostgresDsn = "postgres://eva:eva@localhost:15432/eva_{}"
    sentry_dsn: Optional[AnyHttpUrl] = None

    argon2_time_cost: int = 2
    argon2_memory_cost: int = 102400
    argon2_parallelism: int = 8
    argon2_hash_len: int = 16
    argon2_salt_len: int = 16

    password_permanent: bool = True  # 密码是否永不过期
    password_age: timedelta = timedelta(days=365)  # 密码有效期（秒）
    security_code_age: timedelta = timedelta(minutes=15)  # 验证码有效期（秒）

    hydra_admin_host: AnyHttpUrl = "http://localhost:4445"
    hydra_public_host: AnyHttpUrl = "http://localhost:4444"

    jwt_audience: Optional[List[str]]
    jwt_issuer: Optional[str]
    jwt_access_token_expires: Union[bool, timedelta] = timedelta(hours=2)
    jwt_refresh_token_expires: Union[bool, timedelta] = timedelta(days=7)
    jwt_private_key: SecretStr = RSAKey.generate_key(is_private=True).as_pem(is_private=True)


settings = Settings()

db_config = generate_config(db_url=settings.postgres_dsn, app_modules={"models": ["app.models", "aerich.models"]})
test_db_config = generate_config(db_url=settings.postgres_dsn_test, app_modules={"models": ["app.models"]})
