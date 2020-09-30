from typing import List, Optional
from uuid import UUID

import pydantic
from pydantic import Field

from app.models import Credential


class Schema(pydantic.BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True


class PermissionSimple(Schema):
    code: str = Field(max_length=128)
    name: str


class PermissionDetail(PermissionSimple):
    description: Optional[str]


class PermissionUpdate(Schema):
    name: Optional[str]
    description: Optional[str]


class PermissionCreate(PermissionDetail):
    ...


class RoleSimple(Schema):
    code: str = Field(max_length=128)
    name: str


class RoleDetail(RoleSimple):
    description: Optional[str]
    permissions: List[PermissionSimple]


class RoleCreate(RoleSimple):
    description: Optional[str]
    permissions: Optional[List[PermissionSimple]]


class RoleUpdate(Schema):
    name: Optional[str]
    description: Optional[str]


class IdentitySimple(Schema):
    uuid: UUID
    is_active: bool


class CredentialCreate(Schema):
    identifier: str
    identifier_type: Credential.IdentifierType
    password: Optional[str]


class IdentityCreate(Schema):
    roles: Optional[List[str]]
    is_active: bool = True
    credentials: List[CredentialCreate]


class IdentityUpdate(Schema):
    is_active: Optional[bool]


class IdentityDetail(Schema):
    uuid: UUID
    roles: Optional[List[RoleSimple]]
    is_active: bool = True
    credentials: List[CredentialCreate]
