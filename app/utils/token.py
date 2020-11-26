import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Sequence, Union

from authlib.jose import JsonWebKey, jwt
from authlib.jose.errors import JoseError
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN
from tortoise import timezone

from app.controllers import EvaException
from app.core.config import settings


class AuthJWT:
    def __init__(
        self,
        private_key=settings.jwt_private_key.get_secret_value(),
        issuer: Optional[str] = settings.jwt_issuer,
        audience: Optional[Union[str, Sequence[str]]] = settings.jwt_audience,
    ):
        self.private_key = private_key
        self.issuer = issuer
        self.audience = audience

    def _create_token(
        self,
        type_token: str,
        exp_time: Optional[int],
        *,
        custom_claims,
    ) -> str:

        # Data section
        claims = {
            "iat": timezone.now(),
            "nbf": timezone.now(),
            "jti": str(uuid.uuid4()),
            "type": type_token,
            **custom_claims,
        }

        if exp_time:
            claims["exp"] = exp_time
        if self.issuer:
            claims["iss"] = self.issuer
        if self.audience:
            claims["aud"] = self.audience

        key = JsonWebKey.import_key(self.private_key)
        headers = {"alg": "RS256", "kid": key.thumbprint()}
        return jwt.encode(header=headers, payload=claims, key=key)

    @staticmethod
    def _get_expired_time(
        type_token: str, identifier_type=None, expires_time: Optional[Union[timedelta, bool]] = None
    ) -> Optional[datetime]:
        """
        如果设置为False，则永不过期
        如果没设置或者设置为True，则设置为默认值
        如果特殊设置了expires_time, 则设置为对应的expires_time
        """

        if expires_time is False:
            return None
        if expires_time is True or expires_time is None:
            if identifier_type == "APP_KEY":
                ret = settings.jwt_access_token_expires_app_key
            else:
                if type_token == "access":
                    ret = settings.jwt_access_token_expires
                elif type_token == "refresh":
                    ret = settings.jwt_refresh_token_expires
                else:
                    raise NotImplementedError

        else:
            ret = expires_time

        return timezone.now() + ret

    def create_access_token(
        self,
        expires_time: Optional[Union[timedelta, int, bool]] = None,
        *,
        custom_claims,
    ) -> str:
        return self._create_token(
            type_token="access",
            exp_time=self._get_expired_time("access", custom_claims["identifier_type"], expires_time),
            custom_claims=custom_claims,
        )

    def create_refresh_token(
        self,
        expires_time: Optional[Union[timedelta, int, bool]] = None,
        *,
        custom_claims,
    ) -> str:
        return self._create_token(
            type_token="refresh",
            exp_time=self._get_expired_time("refresh", custom_claims["identifier_type"], expires_time),
            custom_claims=custom_claims,
        )

    def verify_token(self, encoded_token: str) -> Dict[str, Union[str, int, bool]]:
        try:
            return jwt.decode(encoded_token, key=self.private_key)
        except JoseError as err:
            raise EvaException(status_code=403, message=err.error)


auth_jwt = AuthJWT()


class TokenRequired(HTTPBearer):
    def __init__(self, *, token_type: str = "access", **kwargs):
        super().__init__(**kwargs)
        self.token_type = token_type

    async def __call__(self, request: Request) -> Dict[str, Union[str, int, bool]]:
        token_pair = await super().__call__(request)
        token = auth_jwt.verify_token(token_pair.credentials)
        if not token["type"] == self.token_type:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="invalid token type")
        return token
