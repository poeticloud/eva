from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError

from haomo.conf import settings

import hashlib
import random
import string


def _hash(salt, raw_password):
    data = "{0}{1}".format(salt, raw_password)
    return hashlib.sha512(data.encode("UTF-8")).hexdigest()


def encrypt_password(plaintext):
    ph = PasswordHasher(
        time_cost=settings.getint("ARGON2_TIME_COST"),
        memory_cost=settings.getint("ARGON2_MEMORY_COST"),
        parallelism=settings.getint("ARGON2_PARALLELISM"),
        hash_len=settings.getint("ARGON2_HASH_LEN"),
        salt_len=settings.getint("ARGON2_SALT_LEN"),
        encoding="utf-8",
        type=Type.ID,
    )
    return ph.hash(plaintext)


def check_password(raw_password, enc_password):
    ph = PasswordHasher(
        time_cost=settings.getint("ARGON2_TIME_COST"),
        memory_cost=settings.getint("ARGON2_MEMORY_COST"),
        parallelism=settings.getint("ARGON2_PARALLELISM"),
        hash_len=settings.getint("ARGON2_HASH_LEN"),
        salt_len=settings.getint("ARGON2_SALT_LEN"),
        encoding="utf-8",
        type=Type.ID,
    )
    try:
        ph.verify(enc_password, raw_password)
        return True
    except VerifyMismatchError:
        return False
