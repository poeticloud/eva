import logging
import sys

import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.gzip import GZipMiddleware
from tortoise.contrib.fastapi import register_tortoise

from app.controllers import hydra, user
from app.core import config

logging.root.setLevel("INFO")


def create_app():
    fast_app = FastAPI(
        debug=False,
        title="Galaxy",
        servers=[
            {"url": "http://localhost:8000", "description": "Developing environment"},
        ],
        default_response_class=ORJSONResponse,
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
    fast_app.include_router(user.router)
    fast_app.include_router(hydra.router)
    return fast_app


app = create_app()

if config.settings.env != "local":
    sentry_sdk.init(dsn=config.settings.sentry_dsn, environment=config.settings.env)
    app.add_middleware(SentryAsgiMiddleware)

if not sys.argv[0].endswith("pytest"):
    register_tortoise(app, config=config.db_config, add_exception_handlers=True, generate_schemas=False)
