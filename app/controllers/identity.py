from uuid import UUID

from fastapi import APIRouter, Depends

from app import schemas
from app.controllers import EvaException
from app.models import Credential, Identity, Password, Permission, Role
from app.utils.paginator import Pagination, PaginationResult

router = APIRouter()


@router.get("/identity", response_model=PaginationResult[schemas.IdentitySimple], tags=["Identity Management"])
async def list_identities(p: Pagination = Depends(Pagination)):
    queryset = Identity.all()
    return await p.apply(queryset, schemas.IdentitySimple)


@router.post("/identity", response_model=schemas.IdentityDetail, tags=["Identity Management"])
async def create_identity(body: schemas.IdentityCreate):
    roles = await Role.filter(code__in=body.role_codes).all()
    if not len(roles) == len(body.role_codes):
        diff = set(body.role_codes) - {r.name for r in roles}
        raise EvaException(message=f"specified roles {diff} not found")
    new_identity = Identity(is_active=body.is_active)
    await new_identity.save()
    await new_identity.roles.add(*roles)
    credentials = []
    for identifier_pair in body.credentials:
        c = Credential(
            identifier=identifier_pair.identifier,
            identifier_type=identifier_pair.identifier_type,
            identity=new_identity,
        )
        await c.save()
        pwd = Password.from_raw(c, identifier_pair.password)
        await pwd.save()
        credentials.append(c)
    await new_identity.fetch_related("roles__permissions")
    return await schemas.IdentityDetail.from_object(new_identity)


@router.get("/identity/{uuid}", response_model=schemas.IdentityDetail, tags=["Identity Management"])
async def retrieve_identity(uuid: UUID):
    identity = await Identity.get(uuid=uuid).prefetch_related("roles__permissions")
    return await schemas.IdentityDetail.from_object(identity)


@router.delete("/identity/{uuid}", response_model=None, tags=["Identity Management"])
async def delete_identity(uuid: UUID):
    identity = await Identity.get(uuid=uuid)
    await identity.delete()


@router.patch("/identity/{uuid}", response_model=schemas.IdentityDetail, tags=["Identity Management"])
async def update_identity(uuid: UUID, body: schemas.IdentityUpdate):
    identity = await Identity.get(uuid=uuid).prefetch_related("roles__permissions")
    if body.is_active is not None:
        identity.is_active = body.is_active
    if body.credentials is not None:
        old_ids = set(await identity.credentials.all().values_list("id", flat=True))
        new_ids = set()
        for identifier_pair in body.credentials:
            c, _ = await Credential.get_or_create(
                identifier=identifier_pair.identifier,
                identifier_type=identifier_pair.identifier_type,
                identity=identity,
            )
            if identifier_pair.password:
                pwd = await c.passwords.all().first()
                if not pwd:
                    pwd = Password.from_raw(c, identifier_pair.password)
                pwd.set_password(identifier_pair.password)
                await pwd.save()
            new_ids.add(c.id)
        await Credential.filter(id__in=(old_ids - new_ids)).delete()
    if body.roles is not None:
        old_roles = set(await identity.roles.all())
        new_roles = set(await Role.filter(code__in=[r.code for r in body.roles]).all())
        await identity.roles.remove(*(old_roles - new_roles))
        await identity.roles.add(*(new_roles - old_roles))

    await identity.save()
    return await schemas.IdentityDetail.from_object(identity)


@router.get("/role", response_model=PaginationResult[schemas.RoleSimple], tags=["Role Management"])
async def list_roles(p: Pagination = Depends(Pagination)):
    queryset = Role.all()
    return await p.apply(queryset, schemas.RoleSimple)


@router.post("/role", response_model=schemas.RoleDetail, tags=["Role Management"])
async def create_role(body: schemas.RoleCreate):
    if await Role.filter(code=body.code).exists():
        raise EvaException(message="provided role code already exists")
    role = Role(
        code=body.code,
        name=body.name,
        description=body.description,
    )
    await role.save()
    if body.permission_codes:
        permissions = await Permission.filter(code__in=body.permission_codes)
        await role.permissions.add(*permissions)
    return await schemas.RoleDetail.from_object(role)


@router.get("/role/{role_code}", response_model=schemas.RoleDetail, tags=["Role Management"])
async def delete_role(role_code: str):
    role = await Role.get(code=role_code)
    return await schemas.RoleDetail.from_object(role)


@router.delete("/role/{role_code}", response_model=None, tags=["Role Management"])
async def retrieve_role(role_code: str):
    role = await Role.get(code=role_code)
    await role.delete()


@router.patch("/role/{role_code}", response_model=schemas.RoleDetail, tags=["Role Management"])
async def update_role(role_code: str, body: schemas.RoleUpdate):
    role = await Role.get(code=role_code)
    if body.name:
        role.name = body.name
    if body.description:
        role.description = body.description
    if body.permission_codes is not None:
        old_permissions = set(await role.permissions.all())
        new_permissions = set(await Permission.filter(code__in=body.permission_codes).all())
        await role.permissions.remove(*(old_permissions - new_permissions))
        await role.permissions.add(*(new_permissions - old_permissions))
    await role.save()
    return await schemas.RoleDetail.from_object(role)


@router.get("/permission", response_model=PaginationResult[schemas.PermissionSimple], tags=["Permission Management"])
async def list_permissions(p: Pagination = Depends(Pagination)):
    return await p.apply(Permission.all(), schemas.PermissionSimple)


@router.post("/permission", response_model=schemas.PermissionDetail, tags=["Permission Management"])
async def create_permission(body: schemas.PermissionCreate):
    if await Permission.filter(code=body.code).exists():
        raise EvaException(message="provided permission code already exists")
    permission = Permission(**body.dict())
    await permission.save()
    return schemas.PermissionDetail.from_orm(permission)


@router.get("/permission/{permission_code}", response_model=schemas.PermissionDetail, tags=["Permission Management"])
async def retrieve_permission(permission_code: str):
    permission = await Permission.get(code=permission_code)
    return schemas.PermissionDetail.from_orm(permission)


@router.patch("/permission/{permission_code}", response_model=schemas.PermissionDetail, tags=["Permission Management"])
async def update_permission(permission_code: str, body: schemas.PermissionUpdate):
    permission = await Permission.get(code=permission_code)
    await permission.update_from_dict(body.dict(exclude_unset=True)).save()
    return schemas.PermissionDetail.from_orm(permission)


@router.delete("/permission/{permission_code}", response_model=None, tags=["Permission Management"])
async def delete_permission(permission_code: str):
    permission = await Permission.get(code=permission_code)
    await permission.delete()
