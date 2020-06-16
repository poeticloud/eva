# pylint: disable=W0221,W0223

import tornado.web

from haomo.conf import settings
from codebase.utils.api import AsyncApi

hydry_api = AsyncApi(url_prefix=settings.HYDRA_ADMIN_URL)


class BaseHandler(tornado.web.RequestHandler):

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

        items = ["Item 1", "Item 2", "Item 3"]
        self.render(
            "login.html",
            challenge=challenge,
            title="My title",
            items=items,
            text=text)

    async def post(self):
        challenge = self.get_body_argument("challenge")
        resp = await hydry_api.get("/oauth2/auth/requests/login", query_params={
            "login_challenge": challenge})
        print(f"{resp=}")

        print(f"{self.request.body=}")

        username = self.get_body_argument("username")
        password = self.get_body_argument("password")
        print(f"{challenge=}")
        print(f"{username=}")
        print(f"{password=}")

        resp = await hydry_api.put("/oauth2/auth/requests/login/accept", query_params={
            "login_challenge": challenge}, body={
                "subject": username,
                "remember": True,
                "remember_for": 3600,
            })
        print(f"{resp=}")

        url = resp["redirect_to"]
        self.redirect(url)


class ConsentHandler(BaseHandler):

    async def get(self):

        challenge = self.get_argument("consent_challenge")
        resp = await hydry_api.get("/oauth2/auth/requests/consent", query_params={
            "consent_challenge": challenge})
        print(f"{resp=}")

        self.render(
            "consent.html",
            title="Hydra Consent",
            requested_scope=resp["requested_scope"],
            challenge=challenge,
            text=resp)

    async def post(self):
        challenge = self.get_argument("challenge")
        resp = await hydry_api.get("/oauth2/auth/requests/consent", query_params={
            "consent_challenge": challenge})
        print(f"{resp=}")

        print(f"{self.request.body=}")

        grant_scope = self.get_body_arguments("grant_scope")
        print(f"{challenge=}")
        print(f"{grant_scope=}")

        resp = await hydry_api.put("/oauth2/auth/requests/consent/accept", query_params={
            "consent_challenge": challenge}, body={
                "grant_scope": grant_scope,
                "remember": True,
                "remember_for": 3600,
        })
        print(f"{resp=}")

        url = resp["redirect_to"]
        self.redirect(url)
