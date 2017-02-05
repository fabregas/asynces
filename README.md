# asynces
Asyncio driver for Elasticsearch


Example:
```python
import asyncio
from asynces import AsyncElasticsearch

async def test():
    ret = await s.search(index='my-index')
    return ret

loop = asyncio.get_event_loop()
es = AsyncElasticsearch('http://127.0.0.1:9200/', loop=loop)
loop.run_until_complete(test(es))
es.close()
loop.close()
```
