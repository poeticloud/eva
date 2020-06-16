# pylint: disable=R0902,R0913,W0613,R0903

"""
TODO:

1. 支持 one-time password (OTP)
2. 支持自定义的用户属性(profile/trait)。属性组？
"""

import datetime
import uuid
import string
import enum

from sqlalchemy_utils import UUIDType
from eva.conf import settings
from eva.utils.time_ import utc_rfc3339_string
from sqlalchemy import (
    event,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Text,
    JSON,
    Enum,
    Boolean
)
from sqlalchemy.orm import relationship

from codebase.utils.sqlalchemy import dbc
from codebase.utils.enc import check_password, encrypt_password

from . import Base


@enum.unique
class IdentifierType(enum.Enum):
    USERNAME = enum.auto()
    EMAIL = enum.auto()
    PHONE = enum.auto()
    IDP = enum.auto()


@enum.unique
class IdPType(enum.Enum):
    LDAP = enum.auto()
    OIDC = enum.auto()
    GOOGLE = enum.auto()
    FACEBOOK = enum.auto()
    TWITTER = enum.auto()
    GITHUB = enum.auto()
    GITLAB = enum.auto()
    WECHAT = enum.auto()
    WEIBO = enum.auto()


class Identity(Base):
    """身份
    """

    __tablename__ = "eva_identity"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUIDType(), default=uuid.uuid4, unique=True)
    created = Column(DateTime(), default=datetime.datetime.utcnow)


class IdP(Base):
    """IdP

    第三方身份认证，如：
    - LDAP
    - Google
    - Github
    - WeChat

    其他如x509证书 cn 标识鉴别
    """

    __tablename__ = "eva_idp"

    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    type = Column(
        Enum(IdPType), nullable=False,
        doc="IdP类型")

    config = Column(
        JSON,
        doc="该IdP的详细配置")

    is_active = Column(
        Boolean, default=False,
        doc="该IdP是否启用？")

    created = Column(DateTime(), default=datetime.datetime.utcnow)
    updated = Column(DateTime(), default=datetime.datetime.utcnow)


class Credential(Base):
    """凭证

    如：用户名、邮箱、手机号
    
    凭证 + 验证方式 -> 验证身份（identify）

    验证方案如：
    1. 用户名、邮箱、手机号 + 密码
    2. 邮箱 + 验证码
    3. 手机 + 验证码
    4. 第三方凭证（Google, Fackbook, Twitter, Github, WeChat, Weibo等）
    """

    __tablename__ = "eva_credential"

    id = Column(Integer, primary_key=True)

    identifier = Column(
        String(64), nullable=False,
        doc="凭证唯一标识，如：邮件地址,手机号,微信openid等")
    identifier_type = Column(
        Enum(IdentifierType), nullable=False,
        doc="identifier 的类型，如用户名只能对应密码认证；邮件和手机号可以有其对应的验证码认证")

    # 一个身份可以关联多个凭证
    identity_id = Column(Integer, ForeignKey("eva_identity.id"))
    identity = relationship("Identity", backref="credentials")

    idp_id = Column(
        Integer, ForeignKey("eva_idp.id"), nullable=True,
        doc="如果第三方认证方式")
    idp = relationship("IdP")

    created = Column(DateTime(), default=datetime.datetime.utcnow)


class Password(Base):
    """密码验证方式
    """

    __tablename__ = "eva_password"

    id = Column(Integer, primary_key=True)
    shadow = Column(String(512), nullable=False)

    credential_id = Column(Integer, ForeignKey("eva_credential.id"))
    credential = relationship("Credential")

    updated = Column(DateTime(), default=datetime.datetime.utcnow)
    expires_in = Column(DateTime())

    def __init__(self, credential, password, permanent=settings.PASSWORD_PERMANENT):
        self.credential_id = credential.id
        self.shadow = encrypt_password(password)
        if not permanent:
            self.expires_in = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=settings.getint("PASSWORD_AGE"))

    @property
    def is_expired(self):
        if not self.expires_in:
            return False
        return datetime.datetime.utcnow() > self.expires_in

    def validate_password(self, raw_password):
        return check_password(raw_password, self.shadow)

    def set_password(self, raw_password):
        self.shadow = encrypt_password(raw_password)


class SecurityCode(Base):
    """验证码验证方式

    1. 如果是邮箱，就发送邮件到邮箱地址
    2. 如果是手机号，就发送短信到手机号
    """

    __tablename__ = "eva_securitycode"

    id = Column(Integer, primary_key=True)
    shadow = Column(String(512), nullable=False)

    # FIXME: 关联 credential 还是 identity ？
    credential_id = Column(Integer, ForeignKey("eva_credential.id"))
    credential = relationship("Credential")

    created = Column(DateTime(), default=datetime.datetime.utcnow)
    expires_in = Column(DateTime())

    def __init__(self, credential, code):
        self.credential_id = credential.id
        self.shadow = encrypt_password(code)
        self.expires_in = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=settings.getint("SECURITY_CODE_AGE"))

    @property
    def is_expired(self):
        return datetime.datetime.utcnow() > self.expires_in

    def validate_code(self, code):
        return check_password(code, self.shadow)

    def set_code(self, code):
        self.shadow = encrypt_password(code)
