# asynces
[![Build Status](https://travis-ci.org/fabregas/asynces.svg?branch=master)](https://travis-ci.org/fabregas/asynces)
[![codecov](https://codecov.io/gh/fabregas/asynces/branch/master/graph/badge.svg)](https://codecov.io/gh/fabregas/asynces)


### Asyncio driver for Elasticsearch and Python 3.5+

Its goal is to create an asyncio transport for the official elasticsearch python driver.

The **asynces** package provides the AsyncElasticsearch class inherited from
the Elasticsearch class (see [elasticsearch](https://elasticsearch-py.readthedocs.io/en/master/index.html)).

All methods from the Elasticsearch class instance (see [API doc](http://elasticsearch-py.readthedocs.io/en/master/api.html))
are available in the AsyncElasticsearch class instance.

Each API method returns [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutines) that must be awaited.

Example of asynces usage:
```python
import asyncio
from asynces import AsyncElasticsearch

async def test(loop):
    es = AsyncElasticsearch('http://127.0.0.1:9200/', loop=loop)
    doc = {'hello': 'world'}
    await es.index(index='my-index', doc_type='test', body=doc, refresh=False)
    await es.indices.refresh(index="my-index")
    ret = await es.search(index='my-index')
    print(ret)
    es.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()
```

## Installation

First, you should install the latest version of [elasticsearch](https://elasticsearch-py.readthedocs.io/en/master/index.html#compatibility)
compatible with your elasticsearch server version.

After that you should install asynces package:

> pip install asynces


