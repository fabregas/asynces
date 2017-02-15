import aiohttp
import asyncio
import async_timeout
import elasticsearch as es

from elasticsearch.connection.base import Connection
from elasticsearch.compat import urlencode
from elasticsearch.exceptions import ConnectionTimeout, ConnectionError


class AioConnection(Connection):
    def __init__(self, host='localhost', port=9200, *, loop, **kwargs):
        super(AioConnection, self).__init__(host, port, **kwargs)
        self._loop = loop
        verify_ssl = kwargs.get('verify_ssl', False)
        self._addr = {"host": host, "port": port}
        self._session = aiohttp.ClientSession(
            loop=loop,
            connector=aiohttp.TCPConnector(
                use_dns_cache=True,
                loop=loop,
                verify_ssl=verify_ssl)
        )

    def addr(self):
        return self._addr

    async def perform_request(
            self, method, url, params=None, body=None,
            timeout=None, ignore=()):
        url = self.url_prefix + url
        if params:
            url = '{}?{}'.format(url, urlencode(params))
        full_url = self.host + url

        start = self._loop.time()
        try:
            with async_timeout.timeout(timeout, loop=self._loop):
                async with self._session.request(
                        method, full_url, data=body) as resp:
                    raw_data = await resp.text()
        except Exception as e:
            self.log_request_fail(
                method, full_url, url, body,
                self._loop.time() - start, exception=e)
            if isinstance(e, asyncio.TimeoutError):
                raise ConnectionTimeout('TIMEOUT', str(e), e)
            raise ConnectionError('N/A', str(e), e)

        duration = self._loop.time() - start
        # raise errors based on http status codes,
        # let the client handle those if needed
        if not (200 <= resp.status < 300) and resp.status not in ignore:
            self.log_request_fail(
                method, full_url, url, body, duration, resp.status, raw_data)
            self._raise_error(resp.status, raw_data)

        self.log_request_success(
            method, full_url, url, body, resp.status, raw_data, duration)

        return resp.status, resp.headers, raw_data

    def log_request_fail(self, method, full_url, path, body, duration,
                         status_code=None, response=None, exception=None):
        if es.VERSION < (5, 0):
            super().log_request_fail(method, full_url, body, duration,
                                     status_code, response, exception)
        else:
            super().log_request_fail(method, full_url, path, body, duration,
                                     status_code, response, exception)

    def close(self):
        """
        Explicitly closes session
        """
        self._session.close()
