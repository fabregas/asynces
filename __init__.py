from elasticsearch import Elasticsearch
from .transport import AioTransport


class AsyncElasticsearch(Elasticsearch):
    def __init__(self, hosts, *, loop, **kwargs):
        super(AsyncElasticsearch, self).__init__(
            hosts, transport_class=AioTransport, loop=loop, **kwargs)

    def close(self):
        self.transport.close()
