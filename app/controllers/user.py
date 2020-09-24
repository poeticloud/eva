from uuid import UUID

from fastapi import APIRouter, Depends
from tortoise import transactions

from app import schemas
from app.models import Credential, Password, Role, User
from app.utils.paginator import Pagination, PaginationResult

router = APIRouter()


@router.get("/user", response_model=PaginationResult[schemas.UserSimple])
async def list_users(p: Pagination = Depends(Pagination)):
    queryset = User.all()
    ret = await p.apply(queryset)
    ret.results = [
        schemas.UserSimple(
            id=u.id,
            uuid=u.uuid,
            is_superuser=u.is_superuser,
            is_active=u.is_active,
        )
        for u in ret.results
    ]
    return ret


@router.post("/user", response_model=schemas.UserDetail)
@transactions.atomic()
async def create_user(body: schemas.UserCreate):
    new_user = User(name=body.name, is_active=body.is_active)
    await new_user.save()
    credentials = []
    for identifier_pair in body.credentials:
        c = Credential(
            identifier=identifier_pair.identifier, identifier_type=identifier_pair.identifier_type, user=new_user
        )
        await c.save()
        pwd = Password.from_raw(c, identifier_pair.password)
        await pwd.save()
        credentials.append(c)
    return await schemas.UserDetail.from_uuid(new_user.uuid)


@router.get("/user/{uuid}", response_model=schemas.UserDetail)
async def retrieve_user(uuid: UUID):
    return await schemas.UserDetail.from_uuid(uuid)


@router.delete("/user/{uuid}", response_model=None)
async def delete_user(uuid: UUID):
    user = await User.get(uuid=uuid)
    await user.delete()


@router.patch("/user/{uuid}", response_model=schemas.UserDetail)
@transactions.atomic()
async def update_user(uuid: int, body: schemas.UserUpdate):
    user = await User.get(uuid=uuid)
    if body.name:
        user.name = body.name
    if body.is_active:
        user.is_active = body.is_active
    if body.credentials:
        old_ids = set(await user.credentials.all().values_list("id", flat=True))
        new_ids = set()
        for identifier_pair in body.credentials:
            c, _ = await Credential.get_or_create(
                identifier=identifier_pair.identifier, identifier_type=identifier_pair.identifier_type, user=user
            )
            if identifier_pair.password:
                pwd = await c.passwords.all().first()
                pwd.set_password(identifier_pair.password)
                await pwd.save()
            new_ids.add(c.id)
        await Credential.filter(id__in=(old_ids - new_ids)).delete()
    if body.roles:
        roles = await Role.filter(name__in=body.roles)
        await user.roles.add(*roles)
    await user.save()
