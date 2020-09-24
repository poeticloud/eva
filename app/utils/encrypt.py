from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings


def encrypt_password(raw_password):
    ph = PasswordHasher(
        time_cost=settings.argon2_time_cost,
        memory_cost=settings.argon2_memory_cost,
        parallelism=settings.argon2_parallelism,
        hash_len=settings.argon2_hash_len,
        salt_len=settings.argon2_salt_len,
        encoding="utf-8",
        type=Type.ID,
    )
    return ph.hash(raw_password)


def check_password(hashed_password, raw_password) -> bool:
    ph = PasswordHasher(
        time_cost=settings.argon2_time_cost,
        memory_cost=settings.argon2_memory_cost,
        parallelism=settings.argon2_parallelism,
        hash_len=settings.argon2_hash_len,
        salt_len=settings.argon2_salt_len,
        encoding="utf-8",
        type=Type.ID,
    )
    try:
        ph.verify(hashed_password, raw_password)
        return True
    except VerifyMismatchError:
        return False
