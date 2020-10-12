import logging
import sys

import sentry_sdk
from fastapi import FastAPI
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from tortoise.contrib.fastapi import register_tortoise
from tortoise.exceptions import DoesNotExist, IntegrityError

from app.controllers import EvaException, hydra, identity
from app.core import config

logging.root.setLevel("INFO")


def create_app():
    fast_app = FastAPI(
        debug=False,
        title="Eva API Document",
        servers=[
            {"url": "http://localhost:8000", "description": "Developing environment"},
        ],
        default_response_class=JSONResponse,
    )
    fast_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    fast_app.add_middleware(ServerErrorMiddleware, debug=(config.settings.env == "local"))
    fast_app.add_middleware(GZipMiddleware)
    fast_app.include_router(identity.router)
    fast_app.include_router(hydra.router)
    return fast_app


app = create_app()


@app.exception_handler(EvaException)
async def eva_exception_handler(_: Request, exc: EvaException):
    return JSONResponse(status_code=400, content={"message": exc.message})


@app.exception_handler(DoesNotExist)
async def does_not_exist_exception_handler(_: Request, exc: DoesNotExist):
    return JSONResponse(status_code=404, content={"message": str(exc)})


@app.exception_handler(IntegrityError)
async def integrity_error_exception_handler(_: Request, exc: IntegrityError):  # pragma: no cover
    return JSONResponse(status_code=422, content={"detail": [{"loc": [], "msg": str(exc), "type": "IntegrityError"}]})


if config.settings.env != "local":  # pragma: no cover
    sentry_sdk.init(dsn=config.settings.sentry_dsn, environment=config.settings.env)
    app.add_middleware(SentryAsgiMiddleware)

if sys.argv == ["manage.py", "runserver"] or sys.argv[0].endswith("gunicorn"):  # pragma: no cover
    register_tortoise(app, config=config.db_config)
