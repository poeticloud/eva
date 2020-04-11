# pylint: disable=W0221,W0223

from codebase.web import APIRequestHandler


class HealthHandler(APIRequestHandler):
    def get(self):
        self.write("OK")
