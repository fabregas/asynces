import asyncio
import pytest
from .utils import IntegrationTest, asynctest
from elasticsearch.exceptions import (
    ConnectionError, ConnectionTimeout, TransportError)

mocked_nodes = '''{
"_nodes":{"total":1,"successful":1,"failed":0},
"cluster_name":"elasticsearch",
"nodes":{
    "VzLd3fFhTHqNwmmY2PS4hQ":{
        "name":"VzLd3fF",
        "transport_address":"127.0.0.1:9300",
        "host":"127.0.0.1",
        "ip":"127.0.0.1",
        "version":"5.1.2",
        "build_hash":"c8c4c16",
        "roles":["master","data","ingest"],
        "http":{
           "bound_address":["[::]:9200"],
           "publish_address":"172.17.0.2:9200",
           "max_content_length_in_bytes":104857600
        }
    },
    "masterOnly":{
        "name":"shouldBeIgnored",
        "transport_address":"127.0.0.1:9300",
        "host":"127.0.0.1",
        "ip":"127.0.0.1",
        "version":"5.1.2",
        "build_hash":"c8c4c16",
        "roles":["master"],
        "http":{
           "bound_address":["[::]:9200"],
           "publish_address":"172.17.0.55:9200",
           "max_content_length_in_bytes":104857600
        }
    },
    "invalidAddr":{
        "name":"shouldBeIgnoredToo",
        "transport_address":"127.0.0.1:9300",
        "host":"127.0.0.1",
        "ip":"127.0.0.1",
        "version":"5.1.2",
        "build_hash":"c8c4c16",
        "roles":["master"],
        "http":{
           "bound_address":["[::]:9200"],
           "publish_address":"172.17.0.56",
           "max_content_length_in_bytes":104857600
        }
    },
    "gdfwDdsTHqNwmmY2PS4ha":{
        "name":"DSsdcsr",
        "transport_address":"127.0.0.1:9300",
        "host":"127.0.0.1",
        "ip":"127.0.0.1",
        "version":"5.1.2",
        "build_hash":"c8c4c16",
        "roles":["master","data","ingest"],
        "http":{
           "bound_address":["[::]:9200"],
           "publish_address":"172.17.0.3:9200",
           "max_content_length_in_bytes":104857600
        }
    }
} }'''

call_cnt = 0


class MockedConn:
    async def req(self, method, url, params=None, body=None,
                  timeout=None, ignore=()):
        global call_cnt
        if url == '/_nodes/_all/http':
            return 200, {}, mocked_nodes
        elif url == '/_cluster/stats':
            return 200, {}, '{"cluster_name": "elasticsearch"}'
        elif url == '/_cluster/health':
            call_cnt += 1
            if call_cnt == 3:
                call_cnt = 0
                return 200, {}, '{"mocked": "ok"}'
            raise ConnectionError('N/A', "mocked exc", Exception("mocked"))
        elif url == '/_cat/indices':
            call_cnt += 1
            if call_cnt == 3:
                call_cnt = 0
                return 200, {}, '{"mocked": "ok"}'
            raise ConnectionTimeout('N/A', "mocked exc", Exception("mocked"))
        elif url == '/_cat/nodes':
            call_cnt += 1
            if call_cnt == 4:
                call_cnt = 0
                return 200, {}, '{"mocked": "ok"}'
            raise TransportError(503, "mocked exc", Exception("mocked"))
        elif url == '/test' and method == 'HEAD':
            raise TransportError(404, "mocked exc", Exception("mocked"))

        print(self, method, url, params, body)
        print(self.addr())
        return 500, {}, ''


class TestMocks(IntegrationTest):
    @asynctest
    async def test_sniff_mock(self, mocker):
        mocker.resetall()
        mocker.patch('asynces.connection.AioConnection.perform_request',
                     new=MockedConn.req)

        async with self.elastic(
                sniff_on_start=True, retry_on_timeout=True,
                sniff_on_connection_fail=True, sniffer_timeout=0.1) as es:
            ret = await es.cluster.stats()
            assert ret['cluster_name'] == 'elasticsearch'

            cl = sorted(es.transport._connection_pool.connections,
                        key=lambda x: x.host)
            assert len(cl) == 2
            assert cl[0].addr() == {"host": "172.17.0.2", "port": 9200}
            assert cl[1].addr() == {"host": "172.17.0.3", "port": 9200}

            # simulate hosts down and up for retry
            res = await es.cluster.health()
            assert res == {"mocked": "ok"}

            res = await es.cat.indices()
            assert res == {"mocked": "ok"}

            res = await es.cat.nodes()
            assert res == {"mocked": "ok"}

            res = await es.cat.nodes(ignore=503)
            assert res == {"mocked": "ok"}

            res = await es.indices.exists("test")
            assert res is False

            # waiting for sniff timeout
            await asyncio.sleep(0.3, loop=self.loop)

            res = await es.indices.exists("test")
            assert res is False

        # no retry on timeout error case
        async with self.elastic(retry_on_timeout=False) as es:
            with pytest.raises(ConnectionTimeout):
                res = await es.cat.indices()

    @asynctest
    async def test_sniff_err(self, mocker):
        async def err(*args, **kvargs):
            raise ConnectionError('N/A', "mocked exc", Exception("mocked"))
        mocker.resetall()
        mocker.patch(
            'asynces.connection.AioConnection.perform_request', new=err)

        async with self.elastic(sniff_on_start=True) as es:
            with pytest.raises(TransportError) as err:
                await es.indices.exists("test")
            assert err.value.error == "Unable to sniff hosts."

        # check sniff with empty nodes returned
        async def emptynodes(*args, **kvargs):
            return 200, {}, '{"nodes": {}}'
        mocker.patch(
            'asynces.connection.AioConnection.perform_request', new=emptynodes)
        async with self.elastic(sniff_on_start=True) as es:
            with pytest.raises(TransportError) as err:
                await es.indices.exists("test")
            assert err.value.error == ("Unable to sniff hosts "
                                       "- no viable hosts found.")

    @asynctest
    async def test_conn_timeouted(self, mocker):
        async def mockerr(*args, **kvargs):
            raise asyncio.TimeoutError("mocked")
        mocker.patch(
            'aiohttp.client_reqrep.ClientResponse.text', new=mockerr)

        async with self.elastic() as es:
            with pytest.raises(ConnectionTimeout):
                await es.indices.exists("test")

    @asynctest
    async def test_conn_bad_status(self, mocker):
        async def mockresp(*args, **kwargs):
            class Resp:
                status = 444
                async def text(self):
                    return ""
                async def release(self):
                    pass
            return Resp()
        mocker.patch(
            'aiohttp.client.ClientSession._request', new=mockresp)
        async with self.elastic() as es:
            with pytest.raises(TransportError) as err:
                await es.cat.nodes()
            assert err.value.status_code == 444
