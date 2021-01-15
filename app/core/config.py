import ssl
from datetime import timedelta
from typing import List, Optional, Union

from authlib.jose import RSAKey
from pydantic import AnyHttpUrl, BaseSettings, FilePath, PostgresDsn, SecretStr, root_validator
from tortoise import generate_config


class Settings(BaseSettings):
    env: str = "local"
    sentry_dsn: Optional[AnyHttpUrl] = None

    postgres_dsn: PostgresDsn = "postgres://postgres:eva@localhost:5432/eva"
    postgres_ssl: bool = False
    postgres_ca_path: Optional[FilePath]
    postgres_key_path: Optional[FilePath]
    postgres_cert_path: Optional[FilePath]

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
    jwt_access_token_expires_app_key: Union[bool, timedelta] = timedelta(days=365)
    jwt_refresh_token_expires: Union[bool, timedelta] = timedelta(days=7)
    jwt_private_key: SecretStr = RSAKey.generate_key(is_private=True).as_pem(is_private=True)

    @root_validator
    def check_ssl(cls, values):
        if values.get("postgres_ssl"):
            ca, key, cert = (
                values.get("postgres_ca_path"),
                values.get("postgres_key_path"),
                values.get("postgres_cert_path"),
            )
            if not all((ca, key, cert)):
                raise ValueError("must specify both ca_path,cert_path,key_path while set ssl=True")
        return values

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

db_config = generate_config(
    db_url=settings.postgres_dsn,
    app_modules={"models": ["app.models", "aerich.models"]},
)
if settings.postgres_ssl:
    ssl_ctx = ssl.create_default_context(cafile=str(settings.postgres_ca_path))
    ssl_ctx.load_cert_chain(certfile=settings.postgres_cert_path, keyfile=settings.postgres_key_path)
    db_config["connections"]["default"]["credentials"]["ssl"] = ssl_ctx
