import enum
import uuid
from datetime import datetime

from tortoise import fields, models
from tortoise.fields import ForeignKeyNullableRelation as Fkn
from tortoise.fields import ForeignKeyRelation as Fk
from tortoise.fields import ManyToManyRelation as M2m
from tortoise.fields import ReverseRelation as Rv

from app.core import config
from app.utils import encrypt


class TimestampModelMixin:
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class Identity(TimestampModelMixin, models.Model):
    """用户 """

    id = fields.BigIntField(pk=True)
    uuid = fields.UUIDField(default=uuid.uuid4, unique=True)
    roles: M2m["Role"] = fields.ManyToManyField("models.Role", related_name="identities")
    is_active = fields.BooleanField(default=True)

    credentials: Rv["Credential"]

    class Meta:
        table = "eva_identity"

    async def has_perm(self, code: str) -> bool:
        await self.fetch_related("roles__permissions")
        for role in self.roles:
            for permission in role.permissions:
                if permission.code == code:
                    return True
        return False


class IdP(TimestampModelMixin, models.Model):
    """IdP
    第三方身份认证，如： - LDAP - Google - Github - WeChat
    其他如x509证书 cn 标识鉴别
    """

    @enum.unique
    class Type(enum.Enum):
        LDAP = "LDAP"
        OIDC = "OIDC"
        GOOGLE = "GOOGLE"
        FACEBOOK = "FACEBOOK"
        TWITTER = "TWITTER"
        GITHUB = "GITHUB"
        GITLAB = "GITLAB"
        WECHAT = "WECHAT"
        WEIBO = "WEIBO"

    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=32)
    type = fields.CharEnumField(Type, description="IdP类型")

    config = fields.JSONField(null=True, description="该IdP的详细配置")
    is_active = fields.BooleanField(default=False, description="该IdP是否启用？")

    class Meta:
        table = "eva_idp"


class Credential(TimestampModelMixin, models.Model):
    """凭证
    如：用户名、邮箱、手机号
    凭证 + 验证方式 -> 验证身份（identify）

    验证方案如：
    1. 用户名、邮箱、手机号 + 密码
    2. 邮箱 + 验证码
    3. 手机 + 验证码
    4. 第三方凭证（Google, Fackbook, Twitter, Github, WeChat, Weibo等）
    """

    @enum.unique
    class IdentifierType(enum.Enum):
        USERNAME = "USERNAME"
        EMAIL = "EMAIL"
        PHONE = "PHONE"
        IDP = "IDP"

    id = fields.BigIntField(pk=True)

    identifier = fields.CharField(max_length=64, description="凭证唯一标识，如：邮件地址,手机号,微信openid等")
    identifier_type = fields.CharEnumField(IdentifierType, description="identifier 的类型，如用户名只能对应密码认证；邮件和手机号可以有其对应的验证码认证")

    # 一个身份可以关联多个凭证
    identity: Fk["Identity"] = fields.ForeignKeyField(
        "models.Identity", ondelete=fields.CASCADE, related_name="credentials"
    )
    idp: Fkn["IdP"] = fields.ForeignKeyField("models.IdP", on_delete=fields.CASCADE, null=True)

    passwords: Rv["Password"]
    security_code: Rv["SecurityCode"]

    class Meta:
        table = "eva_credential"
        unique_together = ("identity", "identifier")


class Password(TimestampModelMixin, models.Model):
    """密码验证方式"""

    id = fields.BigIntField(pk=True)
    shadow = fields.CharField(max_length=512)
    credential: Fk["Credential"] = fields.ForeignKeyField(
        "models.Credential", ondelete=fields.CASCADE, related_name="passwords"
    )
    expires_at = fields.DatetimeField(null=True)

    class Meta:
        table = "eva_password"

    @classmethod
    def from_raw(
        cls, credential: Credential, raw_password: str, permanent=config.settings.password_permanent
    ) -> "Password":
        expires_at = None if permanent else datetime.utcnow() + config.settings.password_age
        return Password(credential=credential, shadow=encrypt.encrypt_password(raw_password), expires_at=expires_at)

    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def validate_password(self, raw_password) -> bool:
        return encrypt.check_password(self.shadow, raw_password)

    def set_password(self, raw_password):
        self.shadow = encrypt.encrypt_password(raw_password)


class SecurityCode(TimestampModelMixin, models.Model):
    """验证码验证方式

    1. 如果是邮箱，就发送邮件到邮箱地址
    2. 如果是手机号，就发送短信到手机号
    """

    id = fields.BigIntField(pk=True)

    credential: Fk["Credential"] = fields.ForeignKeyField(
        "models.Credential", on_delete=fields.CASCADE, related_name="security_codes"
    )
    expires_at = fields.DatetimeField()

    class Meta:
        table = "eva_security_code"

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at


########################################################################################################################
# RBAC
########################################################################################################################


class Role(TimestampModelMixin, models.Model):
    """
    角色与一组权限绑定，用户可以属于多个角色。
    """

    id = fields.BigIntField(pk=True)
    code = fields.CharField(max_length=128, unique=True)
    name = fields.CharField(max_length=128)
    description = fields.TextField(null=True)
    permissions: M2m["Permission"] = fields.ManyToManyField("models.Permission", related_name="roles")

    identities: Rv["Identity"]

    class Meta:
        table = "eva_role"


class Permission(TimestampModelMixin, models.Model):
    """
    提供“标识“，判断用户是否拥有某个“权限”
    """

    id = fields.BigIntField(pk=True)
    code = fields.CharField(max_length=128, unique=True)
    name = fields.CharField(max_length=128)
    description = fields.TextField(null=True)

    roles: Rv["Role"]

    class Meta:
        table = "eva_permission"
