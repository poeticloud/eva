from tornado.web import url

from codebase.controllers import (
    default,
    hydra,
)


HANDLERS = [

    url(r"/", default.SpecHandler),
    url(r"/healthz", default.HealthHandler),

    url(r"/auth/hydra/login", hydra.LoginHandler),
    url(r"/auth/hydra/consent", hydra.ConsentHandler),

]
