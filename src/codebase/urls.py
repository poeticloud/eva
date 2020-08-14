from tornado.web import url

from codebase.controllers import (
    default,
    hydra,
    user,
)


HANDLERS = [

    url(r"/", default.SpecHandler),
    url(r"/healthz", default.HealthHandler),

    url(r"/auth/hydra/login", hydra.LoginHandler),
    url(r"/auth/hydra/consent", hydra.ConsentHandler),

    url(r"/users", user.UserHandler),

]
