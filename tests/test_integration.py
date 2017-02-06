import pytest
import elasticsearch as es
from .utils import IntegrationTest, asynctest


class TestFunctional(IntegrationTest):
    @asynctest
    async def test_basic(self):
        async with self.elastic() as es:
            res = await es.index(index="test-idx", doc_type="test",
                                 body={"some": 333.3}, refresh=True)

            assert res['_type'] == 'test'
            assert res['forced_refresh'] is True
            assert res['result'] == 'created'
            assert res['created'] is True
            assert res['_version'] == 1
            assert res['_index'] == 'test-idx'

    @asynctest
    async def test_cluster(self):
        async with self.elastic() as es:
            res1 = await es.cluster.health()
            res2 = await es.cluster.health(
                local=True, wait_for_status='yellow')
            assert res1 == res2

            ret = await es.cluster.stats()
            assert ret['cluster_name'] == 'elasticsearch'
            assert ret['status'] == 'yellow'

            await es.cluster.stats(human=True)

    @asynctest
    @pytest.mark.skipif(
        es.VERSION >= (5, 0), reason="for elasticsearch 2.X only")
    async def test_es2(self):
        pass

    @asynctest
    @pytest.mark.skipif(
        es.VERSION < (5, 0), reason="for elasticsearch 5.X only")
    async def test_es5(self):
        pass
