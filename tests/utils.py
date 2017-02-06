import asyncio
import pytest
from functools import wraps

from asynces import AsyncElasticsearch
import elasticsearch


def asynctest(fun):
    if not asyncio.iscoroutinefunction(fun):
        fun = asyncio.coroutine(fun)

    @wraps(fun)
    def wrapper(test, *args, **kw):
        loop = test.loop
        ret = loop.run_until_complete(
            asyncio.wait_for(fun(test, *args, **kw), 30, loop=loop))
        return ret
    return wrapper


@pytest.mark.usefixtures('setup_test_class')
class IntegrationTest:
    loop = None

    es_host = None
    es_port = None

    @classmethod
    async def wait_es(cls):
        es = AsyncElasticsearch(
            ['{}:{}'.format(cls.es_host, cls.es_port)], loop=cls.loop)
        for i in range(40):
            try:
                await es.ping()
            except elasticsearch.ElasticsearchException:
                await asyncio.sleep(0.5, loop=cls.loop)
            else:
                break
        else:
            raise RuntimeError("es connection error")

    def elastic(self, **kwargs):
        return EsContextManager(
            self.es_host, self.es_port, loop=self.loop, **kwargs)


class EsContextManager:
    def __init__(self, host, port, *, loop, **kwargs):
        self.es = AsyncElasticsearch(
            ['{}:{}'.format(host, port)], loop=loop, **kwargs)

    async def __aenter__(self):
        return self.es

    async def __aexit__(self, exc_type, exc, tb):
        self.es.close()
