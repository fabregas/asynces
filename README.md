# asynces
### Asyncio driver for Elasticsearch and Python 3.5+

**asynces** package provide AsyncElasticsearch class inherited from
Elasticsearch class from official python driver
[elasticsearch](https://elasticsearch-py.readthedocs.io/en/master/index.html)

All methods from Elasticsearch class instance are available in AsyncElasticsearch
class intance. Every API method returns [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutines)
that must be awaited.

For example:
```python
import asyncio
from asynces import AsyncElasticsearch

async def test(loop):
    es = AsyncElasticsearch('http://127.0.0.1:9200/', loop=loop)
    ret = await es.search(index='my-index')
    print(ret)
    es.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()
```

## Install

First, you should install proper version on [elasticsearch](https://elasticsearch-py.readthedocs.io/en/master/index.html#compatibility)
in accordance to your elasticsearch server version.

After that you should install asynces package:

> pip install asynces


