# pylint: disable=W0221,W0223
from typing import List, Optional

import pydantic

from codebase.models.authz import Role
from codebase.web import APIRequestHandler, has_role
from codebase.models.auth import Credential, IdentifierType, Identity, Password

from haomo.conf import settings


class IdentifierPair(pydantic.BaseModel):
    identifier: str
    identifier_type: IdentifierType


class UserHandler(APIRequestHandler):
    @has_role(settings.ADMIN_ROLE_CODE)
    def post(self):
        """创建用户"""

        class Body(pydantic.BaseModel):
            identifiers: List[IdentifierPair]
            password: Optional[str]
            roles: Optional[List[str]]
            is_active: Optional[bool] = True

        body = Body.parse_obj(self.get_body_json())

        # 检查用户是否已经存在
        for pair in body.identifiers:
            credential = (
                self.db.query(Credential)
                .filter(
                    Credential.identifier == pair.identifier,
                    Credential.identifier_type == pair.identifier_type,
                )
                .first()
            )
            if credential:
                return self.fail(f"用户<{pair.identifier}>已经存在")

        # 创建用户 # 设置角色
        identity = Identity(is_active=body.is_active)
        if body.roles:
            roles = self.db.query(Role).filter(Role.code.in_(body.roles)).all()
            identity.roles = roles

        self.db.add(identity)
        self.db.commit()

        for pair in body.identifiers:
            credential = Credential(
                identifier=pair.identifier,
                identifier_type=pair.identifier_type,
                identity=identity,
            )
            self.db.add(credential)
            self.db.commit()
            if body.password:
                password = Password(credential=credential, password=body.password)
                self.db.add(password)
                self.db.commit()

        return self.success(data={"uid": str(identity.uuid)})


class UserResetPasswordHandler(APIRequestHandler):
    @has_role(settings.ADMIN_ROLE_CODE)
    def post(self, uid):
        class Body(pydantic.BaseModel):
            old_password: str
            new_password: str
            identifier_type: IdentifierType

        body = Body.parse_obj(self.get_body_json())

        # 检查用户是否存在
        credential = (
            self.db.query(Credential)
            .join(Credential.identity)
            .filter(
                Identity.uuid == uid, Credential.identifier_type == body.identifier_type
            )
            .first()
        )
        if not credential:
            return self.fail(f"指定的用户不存在")

        matched = None
        for pwd in credential.passwords:
            if pwd.validate_password(body.old_password):
                matched = pwd
                break
        if not matched:
            return self.fail("旧密码不匹配")
        matched.set_password(body.new_password)
        self.db.commit()
        return self.success()


class UserDetailHandler(APIRequestHandler):
    @has_role(settings.ADMIN_ROLE_CODE)
    def patch(self, uid):
        class Body(pydantic.BaseModel):
            roles: Optional[List[str]]
            identifiers: Optional[List[IdentifierPair]]
            is_active: Optional[bool]

        body = Body.parse_obj(self.get_body_json())

        identity = self.db.query(Identity).filter(Identity.uuid == uid).first()
        if not identity:
            return self.fail("指定的用户不存在")

        # 更新用户的角色
        if body.roles:
            roles = self.db.query(Role).filter(Role.code.in_(body.roles))
            identity.roles = roles

        # 更新用户identifier信息
        if body.identifiers:
            for pair in body.identifiers:
                credential = (
                    self.db.query(Credential)
                    .join(Credential.identity)
                    .filter(
                        Identity.uuid == uid,
                        Credential.identifier_type == pair.identifier_type,
                    )
                    .first()
                )
                credential.identifier = pair.identifier

        # 更新用户活动状态
        if body.is_active is not None:
            identity.is_active = body.is_active

        self.db.commit()
        return self.success()

    def delete(self, uid):
        identity = self.db.query(Identity).filter(Identity.uuid == uid).first()
        if not identity:
            return self.fail("指定的用户不存在")
        self.db.delete(identity)
        self.db.commit()
        return self.success()
