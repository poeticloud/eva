# pylint: disable=W0221,W0223

import logging

import pydantic
from sqlalchemy import and_

from codebase.web import APIRequestHandler

from haomo.conf import settings
from codebase.utils.api import AsyncApi
from codebase.models.auth import Credential, IdentifierType, Identity

hydry_api = AsyncApi(url_prefix=settings.HYDRA_ADMIN_URL)


class BaseHandler(APIRequestHandler):
    @property
    def request_uri(self):
        """返回合适的 URI

        1. 如果设置了URI前缀（部署时指定），则绑定该前缀
        2. 如果无URI前缀，则使用 request.path 即可
        """
        if settings.PUBLIC_URL_PREFIX:
            return settings.PUBLIC_URL_PREFIX + self.request.path
        return self.request.path


class DefaultLoginHandler(BaseHandler):
    async def get(self):

        challenge = self.get_argument("login_challenge")
        resp = await hydry_api.get(
            "/oauth2/auth/requests/login", query_params={"login_challenge": challenge}
        )
        text = resp
        print(text)

        url = f"{settings.WEBAUTH_URL_PREFIX}/#/login?challenge={challenge}"
        items = ["Item 1", "Item 2", "Item 3"]
        await self.render(
            "login.html", challenge=challenge, title="My title", items=items, text=text
        )

    async def post(self):
        # TODO: 1. 错误重定向

        challenge = self.get_argument("challenge")
        if not challenge:
            return self.fail("no challenge")

        resp = await hydry_api.get(
            "/oauth2/auth/requests/login", query_params={"login_challenge": challenge}
        )
        logging.debug(f"{resp=}")

        username = self.get_argument("username")
        password = self.get_argument("password")

        # 查找用户 (目前仅支持用户名标识符)
        credential = (
            self.db.query(Credential)
            .filter(
                and_(
                    Credential.identifier == username,
                    Credential.identifier_type == IdentifierType.USERNAME,
                )
            )
            .first()
        )
        if not credential:
            logging.error("用户 %s 不存在", username)
            return self.fail("用户不存在或密码错误")

        for item in credential.passwords:
            if item.validate_password(password):
                resp = await hydry_api.put(
                    "/oauth2/auth/requests/login/accept",
                    query_params={"login_challenge": challenge},
                    body={
                        "subject": str(credential.identity.uuid),
                        "remember": False,
                        # "remember_for": 3600,
                    },
                )
                logging.info(f"{resp=}")

                url = resp.get("redirect_to")
                self.redirect(url)
                return

        return self.fail("用户不存在或密码错误")


class DefaultConsentHandler(BaseHandler):
    async def get(self):

        challenge = self.get_argument("consent_challenge")
        resp = await hydry_api.get(
            "/oauth2/auth/requests/consent",
            query_params={"consent_challenge": challenge},
        )
        print(f"{resp=}")

        url = f"{settings.WEBAUTH_URL_PREFIX}/#/consent?challenge={challenge}"
        self.render(
            "consent.html",
            title="Hydra Consent",
            requested_scope=resp["requested_scope"],
            challenge=challenge,
            text=resp,
        )

    async def post(self):
        body = self.get_body_json()
        challenge = self.get_argument("challenge")
        if not challenge:
            self.fail("no challenge")
            return

        resp = await hydry_api.get(
            "/oauth2/auth/requests/consent",
            query_params={"consent_challenge": challenge},
        )
        print(f"{resp=}")

        print(f"{self.request.body=}")

        grant_scope = body.get("grant_scope")
        print(f"{challenge=}")
        print(f"{grant_scope=}")

        resp = await hydry_api.put(
            "/oauth2/auth/requests/consent/accept",
            query_params={"consent_challenge": challenge},
            body={"grant_scope": grant_scope, "remember": True, "remember_for": 3600},
        )
        print(f"{resp=}")

        url = resp.get("redirect_to")
        self.redirect(url)


class LoginHandler(BaseHandler):
    async def get(self):

        challenge = self.get_argument("login_challenge")
        resp = await hydry_api.get(
            "/oauth2/auth/requests/login", query_params={"login_challenge": challenge}
        )
        text = resp
        print(text)

        url = f"{settings.WEBAUTH_URL_PREFIX}/#/login?challenge={challenge}"
        self.redirect(url)

    async def post(self):
        class Req(pydantic.BaseModel):
            challenge: str
            identifier: str
            identifier_type: IdentifierType
            password: str

        body = Req.parse_obj(self.get_body_json())

        resp = await hydry_api.get(
            "/oauth2/auth/requests/login",
            query_params={"login_challenge": body.challenge},
        )
        logging.info(f"{resp=}")
        if "error" in resp:
            return self.fail(f"交换登录信息失败：{resp}")

        # 查找用户 (目前仅支持用户名标识符)
        credential = (
            self.db.query(Credential)
            .filter(
                and_(
                    Credential.identifier == body.identifier,
                    Credential.identifier_type == body.identifier_type,
                )
            )
            .first()
        )
        if not credential:
            logging.error("用户 %s 不存在", body.identifier)
            return self.fail("用户不存在或密码错误")

        # TODO: 如果用户被禁用等，需要 reject hydry
        if not credential.identity.is_active:
            return self.fail("该用户已被禁用")

        for item in credential.passwords:
            if item.validate_password(body.password):
                resp = await hydry_api.put(
                    "/oauth2/auth/requests/login/accept",
                    query_params={"login_challenge": body.challenge},
                    body={
                        "subject": str(credential.identity.uuid),
                        "remember": False,
                        # "remember_for": 3600,
                    },
                )
                logging.info(f"{resp=}")

                url = resp.get("redirect_to")
                if not url:
                    return self.fail("系统错误，请刷新重试")
                return self.success(redirect_to=url)

        self.fail("用户不存在或密码错误")


class ConsentHandler(BaseHandler):
    async def get(self):

        challenge = self.get_argument("consent_challenge")
        resp = await hydry_api.get(
            "/oauth2/auth/requests/consent",
            query_params={"consent_challenge": challenge},
        )
        logging.debug(f"{resp=}")

        url = f"{settings.WEBAUTH_URL_PREFIX}/#/consent?challenge={challenge}"
        self.redirect(url)

    async def post(self):
        body = self.get_body_json()

        challenge = body.get("challenge")
        if not challenge:
            self.fail("no challenge")
            return

        resp = await hydry_api.get(
            "/oauth2/auth/requests/consent",
            query_params={"consent_challenge": challenge},
        )
        logging.debug(f"{resp=}")

        # TODO: check subject, identity 是否存在
        subject = resp.get("subject")
        identity = self.db.query(Identity).filter_by(uuid=subject).first()
        if identity:
            roles = [item.code for item in identity.roles]

        logging.debug(f"{self.request.body=}")

        grant_scope = body.get("grant_scope")
        logging.debug(f"{challenge=}")
        logging.debug(f"{grant_scope=}")
        # TODO: 检查用户是否有这些 scope ? (目前来看都是 hydra 创建 client 时设定的)

        resp = await hydry_api.put(
            "/oauth2/auth/requests/consent/accept",
            query_params={"consent_challenge": challenge},
            body={
                "grant_scope": grant_scope,
                "remember": True,
                "remember_for": 3600,
                "session": {"id_token": {"roles": roles}},
            },
        )
        logging.debug(f"{resp=}")

        url = resp.get("redirect_to")
        self.success(redirect_to=url)
