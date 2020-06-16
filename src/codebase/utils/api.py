# pylint: disable=R0913,C0103,R0914

import json
import logging
from urllib.parse import (
    urlencode,
    urljoin,
    urlparse,
    parse_qsl,
    urlunparse,
)

from tornado.httpclient import AsyncHTTPClient, HTTPRequest


class AsyncApi:
    """异步 Api 访问接口
    """

    access_token = None

    def __init__(self, url_prefix, default_headers=None, raw_response=False):
        self.url_prefix = url_prefix
        self.default_headers = default_headers
        self.raw_response = raw_response

    def request_pre(self, request):
        """每次执行请求前调用

        重定义此方法可以添加验证等
        """

    def request_post(self, request, response):
        """每次执行请求后调用

        重定义本方法可以修改请求返回值
        """

    async def request(
            self, url: str, method: str = "GET", headers: dict = None,
            query_params: dict = None, body: dict = None):
        if url[0] == "/":
            url = urljoin(self.url_prefix, url[1:])
        if query_params and isinstance(query_params, dict):
            url_parts = list(urlparse(url))
            query = dict(parse_qsl(url_parts[4]))
            query.update(query_params)

            url_parts[4] = urlencode(query)

            url = urlunparse(url_parts)
        if isinstance(body, dict):
            body = json.dumps(body)

        # 至多重复2次
        for _ in range(2):
            _headers = {}
            if self.default_headers:
                _headers.update(self.default_headers)
            if headers:
                _headers.update(headers)

            req = HTTPRequest(url, method=method, headers=_headers, body=body)
            self.request_pre(req)

            http_client = AsyncHTTPClient()
            # TODO: 检查标准错误
            # allow_nonstandard_methods=True
            # print(method, url, headers, body)
            resp = await http_client.fetch(req, raise_error=False)
            self.request_post(req, resp)

            if resp.code > 400:
                logging.error("%s %s : (%s) %s", method, url, resp.error, resp.body)

            if self.raw_response:
                return resp

            # TODO: 检查返回是否为 JSON 格式
            try:
                respbody = json.loads(resp.body) if resp.body else {}
            except json.JSONDecodeError as err:
                logging.error("json loads %s failed: %s", resp.body, err)
                respbody = {}

            return respbody

    async def get(self, url, query_params=None, headers=None):
        return await self.request(
            url, method="GET", query_params=query_params, headers=headers)

    async def post(self, url, query_params=None, body=None, headers=None):
        return await self.request(
            url, method="POST", query_params=query_params, body=body, headers=headers)

    async def put(self, url, query_params=None, body=None, headers=None):
        return await self.request(
            url, method="PUT", query_params=query_params, body=body, headers=headers)

    async def delete(self, url, query_params=None, headers=None):
        return await self.request(
            url, method="DELETE", query_params=query_params, headers=headers)
