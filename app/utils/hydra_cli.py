from typing import List, Optional

from httpx import AsyncClient


async def hydra_client(base_url: str = "http://localhost:4445") -> AsyncClient:
    async with AsyncClient(base_url=base_url) as client:
        yield HydraClient(client)


class HydraClient:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def get_login_request(self, challenge: str):
        resp = await self.client.get("/oauth2/auth/requests/login", params={"login_challenge": challenge})
        return resp.json()

    async def accept_login_request(
        self, challenge: str, subject: str, remember: Optional[bool] = None, remember_for: Optional[int] = None
    ):
        body = {"subject": subject}
        if remember is not None:
            body["remember"] = remember
            body["remember_for"] = remember_for
        resp = await self.client.put(
            "/oauth2/auth/requests/login/accept", params={"login_challenge": challenge}, json=body
        )
        return resp.json()

    async def get_consent_request(self, challenge: str):
        resp = await self.client.get("/oauth2/auth/requests/consent", params={"consent_challenge": challenge})
        return resp.json()

    async def accept_consent_request(
        self, challenge: str, grant_scope: List[str], remember: bool = None, grant_access_token_audience=None
    ):
        resp = await self.client.put(
            "/oauth2/auth/requests/consent/accept",
            params={"consent_challenge": challenge},
            json={
                "grant_scope": grant_scope,
                "remember": remember,
                "remember_for": 3600,
                "grant_access_token_audience": grant_access_token_audience,
            },
        )
        return resp.json()

    async def reject_consent_request(self, challenge: str, error: str, error_description: str):
        resp = await self.client.put(
            "/oauth2/auth/requests/consent/reject",
            params={"consent_challenge": challenge},
            json={"error": error, "error_description": error_description},
        )
        return resp.json()
