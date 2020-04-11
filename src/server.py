#! /usr/bin/env python3


import time
import signal
import logging
from importlib import import_module

import tornado.options
from haomo.conf import settings

from codebase.app import make_app
from codebase.utils.sqlalchemy import dbc
from codebase.utils.tornado.shutdown import hook_shutdown_graceful


def main():

    dbc.wait_for_it()

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


if __name__ == "__main__":
    main()
