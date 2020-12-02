from typing import Dict

from fastapi import APIRouter, Depends

from app import schemas
from app.controllers import EvaException
from app.models import Credential, Identity
from app.utils.token import TokenRequired, auth_jwt

router = APIRouter()

token_required = TokenRequired(scheme_name="JWT")
refresh_token_required = TokenRequired(scheme_name="JWT", token_type="refresh")


@router.post("/obtain", response_model=schemas.AccessToken)
async def obtain_jwt_token(body: schemas.TokenObtain):
    credential = await Credential.filter(identifier_type=body.identifier_type, identifier=body.identifier).first()
    if not credential:
        raise EvaException(message="The credential is not correct")
    succeed = False
    async for pwd in credential.passwords:
        if pwd.validate_password(body.password):
            succeed = True
            break
    if not succeed:
        raise EvaException(message="The credential is not correct")

    await credential.fetch_related("identity")
    identity: Identity = credential.identity
    claims = {
        "sub": str(identity.uuid),
        "roles": await identity.roles.all().values_list("code", flat=True),
        "identifier_type": credential.identifier_type.name,
    }
    return schemas.AccessToken(
        access_token=auth_jwt.create_access_token(custom_claims=claims),
        refresh_token=auth_jwt.create_refresh_token(custom_claims=claims),
    )


@router.post("/refresh", response_model=schemas.RefreshToken)
async def refresh_jwt_token(token: Dict = Depends(refresh_token_required)):
    uuid = token["sub"]
    identity = await Identity.get(uuid=uuid)
    if not identity or not identity.is_active:
        raise EvaException(message="invalid identity")
    claims = {
        "sub": uuid,
        "roles": await identity.roles.all().values_list("code", flat=True),
        "identifier_type": token["identifier_type"],
    }
    return schemas.RefreshToken(
        access_token=auth_jwt.create_access_token(custom_claims=claims),
    )
