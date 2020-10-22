from authlib.jose import JsonWebKey, KeySet, RSAKey
from fastapi import APIRouter

from app import schemas
from app.core.config import settings

router = APIRouter()


@router.get("/jwks.json", response_model=schemas.JSONWenKeySet)
async def json_web_key_set():
    key: RSAKey = JsonWebKey.import_key(settings.jwt_private_key.get_secret_value())
    key_set = KeySet(keys=[key])
    return key_set.as_dict()
