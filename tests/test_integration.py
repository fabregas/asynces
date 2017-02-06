from .utils import IntegrationTest, asynctest


class TestFunctional(IntegrationTest):
    @asynctest
    async def test_basic(self):
        async with self.elastic() as es:
            res = await es.index(index="test-idx", doc_type="test",
                                 body={"some": 333.3}, refresh=u'true')

            assert res['_type'] == 'test'
            assert res['forced_refresh'] is True
            assert res['result'] == 'created'
            assert res['created'] is True
            assert res['_version'] == 1
            assert res['_index'] == 'test-idx'
