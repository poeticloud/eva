# pylint: disable=W0221,W0223

import logging

from sqlalchemy import and_

from codebase.web import APIRequestHandler

from haomo.conf import settings
from codebase.utils.api import AsyncApi
from codebase.models.auth import Credential, IdentifierType, Identity, Password

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


class LoginHandler(BaseHandler):

    async def get(self):

        challenge = self.get_argument("login_challenge")
        resp = await hydry_api.get("/oauth2/auth/requests/login", query_params={
            "login_challenge": challenge})
        text = resp
        print(text)

        url = f"{settings.WEBAUTH_URL_PREFIX}/#/login?challenge={challenge}"
        self.redirect(url)
        # items = ["Item 1", "Item 2", "Item 3"]
        # self.render(
        #     "login.html",
        #     challenge=challenge,
        #     title="My title",
        #     items=items,
        #     text=text)

    async def post(self):
        body = self.get_body_json()

        if "challenge" not in body:
            self.fail("no challenge")
            return

        challenge = body["challenge"]
        resp = await hydry_api.get("/oauth2/auth/requests/login", query_params={
            "login_challenge": challenge})
        print(f"{resp=}")

        username = body.get("username")
        password = body.get("password")

        # 查找用户 (目前仅支持用户名标识符)
        credential = self.db.query(Credential).filter(and_(
            Credential.identifier == username,
            Credential.identifier_type == IdentifierType.USERNAME)).first()
        if not credential:
            logging.error("用户 %s 不存在", username)
            self.fail("用户不存在或密码错误")
            return

        for item in credential.passwords:
            if item.validate_password(password):
                resp = await hydry_api.put("/oauth2/auth/requests/login/accept", query_params={
                    "login_challenge": challenge}, body={
                        "subject": username,
                        "remember": True,
                        "remember_for": 3600,
                    })
                print(f"{resp=}")

                url = resp.get("redirect_to")
                self.success(redirect_to=url)
                return

        self.fail("用户不存在或密码错误")


class ConsentHandler(BaseHandler):

    async def get(self):

        challenge = self.get_argument("consent_challenge")
        resp = await hydry_api.get("/oauth2/auth/requests/consent", query_params={
            "consent_challenge": challenge})
        print(f"{resp=}")

        url = f"{settings.WEBAUTH_URL_PREFIX}/#/consent?challenge={challenge}"
        self.redirect(url)
        # self.render(
        #     "consent.html",
        #     title="Hydra Consent",
        #     requested_scope=resp["requested_scope"],
        #     challenge=challenge,
        #     text=resp)

    async def post(self):
        body = self.get_body_json()

        challenge = body.get("challenge")
        if not challenge:
            self.fail("no challenge")
            return

        resp = await hydry_api.get("/oauth2/auth/requests/consent", query_params={
            "consent_challenge": challenge})
        print(f"{resp=}")

        print(f"{self.request.body=}")

        grant_scope = body.get("grant_scope")
        print(f"{challenge=}")
        print(f"{grant_scope=}")

        resp = await hydry_api.put("/oauth2/auth/requests/consent/accept", query_params={
            "consent_challenge": challenge}, body={
                "grant_scope": grant_scope,
                "remember": True,
                "remember_for": 3600,
        })
        print(f"{resp=}")

        url = resp.get("redirect_to")
        self.success(redirect_to=url)
        # self.redirect(url)
