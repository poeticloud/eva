# pylint: disable=W0223,W0221,C0103

import functools
import json
import logging
import pprint

from haomo.conf import settings

import tornado.web
from tornado.web import HTTPError
from tornado.escape import json_decode
from tornado.log import app_log, gen_log


class BaseHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header("Access-Control-Allow-Methods", "*")

    def options(self):
        # no body
        self.set_status(204)
        self.finish()


if settings.getbool("CORS"):
    MainBaseHandler = BaseHandler
else:
    MainBaseHandler = tornado.web.RequestHandler


class APIRequestHandler(MainBaseHandler):

    def fail(self, error="fail", errors=None, status=400, **kwargs):
        self.set_status(status)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        d = {"status": error}
        if kwargs:
            d.update(kwargs)
        if errors:
            d["errors"] = errors
        self.write(json.dumps(d))

    def success(self, **kwargs):
        d = {"status": "success"}
        d.update(kwargs)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps(d))

    def get_body_json(self):
        if not self.request.body:
            return {}
        try:
            return json_decode(self.request.body)
        except Exception:
            raise HTTPError(400, reason="not-json-body")

    @property
    def db(self):
        return self.application.db_session()

    def on_finish(self):
        self.application.db_session.remove()

    def write_error(self, status_code, **kwargs):
        """定制出错返回
        """

        # TODO: 处理 status_code
        d = {"status_code": status_code}
        reason = kwargs.get("reason", "")
        message = kwargs.get("message", "")

        if "exc_info" in kwargs:
            exception = kwargs["exc_info"][1]
            if isinstance(exception, HTTPError) and exception.reason:
                reason = exception.reason  # HTTPError reason!
            if isinstance(exception, HTTPError) and exception.status_code:
                status_code = exception.status_code  # HTTPError status_code!
            d["exc_info"] = str(exception)

        if reason:
            if message:
                self.fail(error=reason, message=message, status=status_code)
            else:
                self.fail(error=reason, status=status_code)
        else:
            if message:
                self.fail(
                    error="exception", message=message, status=status_code, data=d)
            else:
                self.fail(errors="exception", status=status_code, data=d)

    def log_exception(self, typ, value, tb):
        """Override to customize logging of uncaught exceptions.

        By default logs instances of `HTTPError` as warnings without
        stack traces (on the ``tornado.general`` logger), and all
        other exceptions as errors with stack traces (on the
        ``tornado.application`` logger).

        .. versionadded:: 3.1
        """
        if isinstance(value, HTTPError):
            if value.log_message:
                sformat = "%d %s: " + value.log_message
                args = [value.status_code, self._request_summary()] + list(value.args)
                gen_log.warning(sformat, *args)
        else:
            app_log.error(
                "Uncaught exception %s\n%r",
                self._request_summary(),
                self.request,
                exc_info=(typ, value, tb),
            )

    def show_debug(self):
        logging.debug("--- request:\n%s", self.request)
        logging.debug("--- request headers:\n%s", self.request.headers)
        json_body = self.get_body_json()
        if json_body:
            body = pprint.pformat(json_body, indent=4)
        else:
            body = self.request.body
        logging.debug("--- request body:\n%s", body)


def authenticated(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            raise HTTPError(403, reason="need authenticated")
        return method(self, *args, **kwargs)

    return wrapper
