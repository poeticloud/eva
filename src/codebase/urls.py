from tornado.web import url

from codebase.controllers import (
    default
)


HANDLERS = [

    url(r"/healthz",
        default.HealthHandler),

]
