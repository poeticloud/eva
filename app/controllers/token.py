from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import schemas
from app.controllers import EvaException
from app.models import Credential, Identity, Role
from app.utils.token import AuthJWT

router = APIRouter()

token_required = HTTPBearer(scheme_name="JWT")


@router.post("/obtain", response_model=schemas.AccessToken)
async def obtain_jwt_token(body: schemas.TokenObtain):
    credential = await Credential.filter(identifier_type=body.identifier_type, identifier=body.identifier).first()
    if not credential:
        raise EvaException(message="The credential is not correct")
    succeed = True
    async for pwd in credential.passwords:
        if pwd.validate_password(body.password):
            succeed = True
            break
    if not succeed:
        raise EvaException(message="The credential is not correct")

    await credential.fetch_related("identity")
    identity: Identity = credential.identity
    roles = await identity.roles.all().values_list("code", flat=True)
    uuid = str(identity.uuid)
    claims = {"sub": uuid, "roles": roles}
    auth_jwt = AuthJWT()
    return schemas.AccessToken(
        access_token=auth_jwt.create_access_token(custom_claims=claims),
        refresh_token=auth_jwt.create_refresh_token(custom_claims=claims),
    )


@router.post("/refresh", response_model=schemas.RefreshToken)
async def refresh_jwt_token(token: HTTPAuthorizationCredentials = Depends(token_required)):
    auth_jwt = AuthJWT()
    token = auth_jwt.verify_token(token.credentials)
    uuid = token["sub"]
    roles = await Role.filter(identities__uuid=uuid).values_list("code", flat=True)
    claims = {"sub": uuid, "roles": roles}
    return schemas.RefreshToken(
        refresh_token=auth_jwt.create_refresh_token(custom_claims=claims),
    )
