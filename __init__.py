from elasticsearch import Elasticsearch
from .transport import AioTransport


class AsyncElasticsearch(Elasticsearch):
    def __init__(self, hosts, *, loop):
        super(AsyncElasticsearch, self).__init__(
            hosts, transport_class=AioTransport, loop=loop)

    def close(self):
        self.transport.close()
