from typing import List, Optional
from uuid import UUID

import pydantic
from pydantic import Field

from app.models import Credential, Identity


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
    permission_codes: List[str]

    @classmethod
    async def from_object(cls, role):
        return RoleDetail(
            code=role.code,
            name=role.name,
            description=role.description,
            permission_codes=await role.permissions.all().values_list("code", flat=True),
        )


class RoleCreate(RoleSimple):
    description: Optional[str]
    permission_codes: Optional[List[str]]


class RoleUpdate(Schema):
    name: Optional[str]
    description: Optional[str]
    permission_codes: Optional[List[str]]


class IdentitySimple(Schema):
    uuid: UUID
    is_active: bool


class CredentialSimple(Schema):
    identifier: str
    identifier_type: Credential.IdentifierType


class CredentialCreate(CredentialSimple):
    password: Optional[str]


class IdentityCreate(Schema):
    role_codes: Optional[List[str]]
    is_active: bool = True
    credentials: List[CredentialCreate]


class IdentityUpdate(Schema):
    roles: Optional[List[RoleSimple]]
    is_active: Optional[bool]
    credentials: Optional[List[CredentialCreate]]


class IdentityDetail(Schema):
    uuid: UUID
    roles: Optional[List[RoleSimple]]
    is_active: bool = True
    credentials: List[CredentialSimple]

    @classmethod
    async def from_object(cls, identity: Identity):
        await identity.fetch_related("roles", "credentials")
        return IdentityDetail(
            uuid=identity.uuid,
            roles=[
                RoleSimple(
                    code=role.code,
                    name=role.name,
                )
                for role in identity.roles
            ],
            is_active=identity.is_active,
            credentials=[
                CredentialSimple(
                    identifier=credential.identifier,
                    identifier_type=credential.identifier_type,
                )
                for credential in identity.credentials
            ],
        )
