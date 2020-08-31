# pylint: disable=W0221,W0223

from sqlalchemy import and_

from codebase.web import APIRequestHandler, has_role
from codebase.models.auth import Credential, IdentifierType, Identity, Password

from haomo.conf import settings


class UserHandler(APIRequestHandler):
    @has_role(settings.ADMIN_ROLE_CODE)
    def post(self):
        """创建用户"""
        body = self.get_body_json()

        if "identifier" not in body:
            return self.fail("请提供用户唯一标识符")

        identifier = body["identifier"]
        identifier_type = body.get("identifier_type", "USERNAME")

        if identifier_type not in [x.name for x in IdentifierType]:
            return self.fail("无效的用户标识符类型")

        identifier_type = IdentifierType[identifier_type]

        # TODO: 校验 identifier 格式是否正确

        # 检查用户是否已经存在
        credential = (
            self.db.query(Credential)
            .filter(
                and_(
                    Credential.identifier == identifier,
                    Credential.identifier_type == identifier_type,
                )
            )
            .first()
        )
        if credential:
            return self.fail(f"用户<{identifier}>已经存在")

        # 创建用户
        identity = Identity()
        self.db.add(identity)
        self.db.commit()

        credential = Credential(
            identifier=identifier, identifier_type=identifier_type, identity=identity
        )
        self.db.add(credential)
        self.db.commit()

        # 保存密码
        raw_password = body.get("password")
        if raw_password:
            password = Password(credential=credential, password=raw_password)
            self.db.add(password)
            self.db.commit()

        return self.success(data={"uid": str(identity.uuid)})


class UserResetPasswordHandler(APIRequestHandler):
    @has_role(settings.ADMIN_ROLE_CODE)
    def post(self, uid):
        body = self.get_body_json()
        new_password = body.get("new_password")
        old_password = body.get("old_password")

        identifier_type = body.get("identifier_type", "USERNAME")

        if identifier_type not in [x.name for x in IdentifierType]:
            return self.fail("无效的用户标识符类型")

        identifier_type = IdentifierType[identifier_type]

        # 检查用户是否存在
        credential = (
            self.db.query(Credential)
            .join(Credential.identity)
            .filter(Identity.uuid == uid, Credential.identifier_type == identifier_type)
            .first()
        )
        if not credential:
            return self.fail(f"指定的用户不存在")

        matched = None
        for pwd in credential.passwords:
            if pwd.validate_password(old_password):
                matched = pwd
                break
        if not matched:
            return self.fail("旧密码不匹配")
        matched.set_password(new_password)
        self.db.commit()
        return self.success()
