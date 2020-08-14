# pylint: disable=W0221,W0223

import os

from codebase.web import APIRequestHandler


class HealthHandler(APIRequestHandler):
    def get(self):
        self.write("OK")


class SpecHandler(APIRequestHandler):
    """
    提供 SwaggerUI YAML 文档
    """

    def get(self):

        path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), os.pardir))

        abspath = os.path.join(path, "api.yml")
        self.set_header("Content-Type", "text/plain")
        self.write(open(abspath, "rb").read())
