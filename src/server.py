#! /usr/bin/env python3

import logging
from importlib import import_module

import tornado.options

from codebase.models.auth import Identity, Credential, IdentifierType, Password
from codebase.models.authz import Role
from haomo.conf import settings

from codebase.app import make_app
from codebase.utils.sqlalchemy import dbc
from codebase.utils.tornado.shutdown import hook_shutdown_graceful


def main():

    dbc.wait_for_it()
    init_db()

    # sync database
    if settings.getbool("INITDB"):
        import_module(settings.MODELS_MODULE)
        dbc.create_all()

    # Create app
    app = make_app()
    server = tornado.httpserver.HTTPServer(app, xheaders=True)

    # Parse options
    tornado.options.define("port", default=3000, help="listen port", type=int)
    if app.settings["debug"]:
        tornado.options.options.logging = "debug"
    tornado.options.parse_command_line()

    port = tornado.options.options.port
    sockets = tornado.netutil.bind_sockets(port)

    # Shutdown the tornado server gracefully
    hook_shutdown_graceful(server)

    server.add_sockets(sockets)
    logging.info(f"{settings.APP_NAME} is running at %d", port)
    tornado.ioloop.IOLoop.instance().start()


def init_db():
    db = dbc.session

    if db.query(Credential).filter(
        Credential.identifier_type == IdentifierType.USERNAME,
        Credential.identifier == settings.ADMIN_USERNAME,
    ).first():
        return

    # 创建初始化用户
    identity = Identity()
    db.add(identity)
    db.commit()

    credential = Credential(
        identifier=settings.ADMIN_USERNAME,
        identifier_type=IdentifierType.USERNAME,
        identity=identity,
    )
    db.add(credential)
    db.commit()

    password = Password(credential=credential, password=settings.ADMIN_PASSWORD)
    db.add(password)
    db.commit()

    role = Role(code=settings.ADMIN_ROLE_CODE, name=settings.ADMIN_ROLE_NAME)
    db.add(role)
    db.commit()

    identity.roles.append(role)
    db.commit()


if __name__ == "__main__":
    main()
