import os
import pathlib

ROOT_PATH = pathlib.Path().absolute()
TEMPLATE_PATH = os.path.join(ROOT_PATH, "codebase/templates/themes/default")

DEBUG = True
CORS = False
SECRET_KEY = "ChangeThisSecretKey"
MODELS_MODULE = "codebase.models"

# http://docs.sqlalchemy.org/en/latest/core/engines.html
DB_URI = "sqlite://"
INITDB = True

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# 密码是否永不过期？
PASSWORD_PERMANENT = True
# 密码有效期（秒）
PASSWORD_AGE = 3600 * 24 * 365 * 1
# 验证码有效期（秒）
SECURITY_CODE_AGE = 60*15

# argon2
ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 102400
ARGON2_PARALLELISM = 8
ARGON2_HASH_LEN = 16
ARGON2_SALT_LEN = 16

# hydra
HYDRA_ADMIN_URL = "http://192.168.31.114:9001"
PUBLIC_URL_PREFIX = ""
