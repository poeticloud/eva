from typing import List, Optional
from uuid import UUID

import pydantic
from pydantic import Field

from app.models import Credential, User


class UserSimple(pydantic.BaseModel):
    id: int
    uuid: UUID
    is_superuser: bool
    is_active: bool


class _CredentialPair(pydantic.BaseModel):
    identifier: str
    identifier_type: Credential.IdentifierType
    password: Optional[str]


class UserCreate(pydantic.BaseModel):
    name: str = Field(max_length=20)
    roles: Optional[List[str]]
    is_active: bool = True
    credentials: List[_CredentialPair]


class UserUpdate(pydantic.BaseModel):
    name: Optional[str] = Field(None, max_length=20)
    roles: Optional[List[str]]
    is_active: Optional[bool]
    credentials: Optional[List[_CredentialPair]]


class UserDetail(pydantic.BaseModel):
    id: int
    name: str = Field(max_length=20)
    roles: Optional[List[str]]
    is_active: bool = True
    credentials: List[_CredentialPair]

    @classmethod
    async def from_uuid(cls, uuid: UUID) -> "UserDetail":
        user = await User.get(uuid=uuid).prefetch_related("roles", "credentials")
        return UserDetail(
            id=user.id,
            name=user.name,
            roles=[r.name for r in user.roles],
            is_active=user.is_active,
            credentials=[
                _CredentialPair(
                    identifier=c.identifier,
                    identifier_type=c.identifier_type,
                )
                for c in user.credentials
            ],
        )
