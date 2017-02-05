
from elasticsearch.serializer import (
    JSONSerializer, Deserializer, DEFAULT_SERIALIZERS)
from elasticsearch.exceptions import (
    TransportError, ConnectionError,
    ConnectionTimeout, SerializationError)

from .pool import ConnectionPool
from .connection import AioConnection


class AioTransport:
    def __init__(self, hosts, max_retries=3, retry_on_status=(502, 503, 504,),
                 sniff_on_start=False, sniffer_timeout=None, sniff_timeout=0.1,
                 sniff_on_connection_fail=False, *, loop, **kwargs):
        self._hosts = hosts
        self._loop = loop
        self._serializer = JSONSerializer()
        self._max_retries = max_retries
        self._retry_on_status = retry_on_status

        # sniffing data
        self._sniffer_timeout = sniffer_timeout
        self._last_sniff = loop.time()
        self._sniff_timeout = sniff_timeout
        self._sniff_on_connection_fail = sniff_on_connection_fail

        serializers = DEFAULT_SERIALIZERS.copy()
        serializers[self._serializer.mimetype] = self._serializer
        self._deserializer = Deserializer(serializers, 'application/json')
        self._connection_pool = ConnectionPool([], loop=loop)
        self._kwargs = kwargs
        self.set_connections(hosts)

    def set_connections(self, hosts):
        connections = []
        for host in hosts:
            for connection in self._connection_pool.connections:
                if connection.host == host:
                    connections.append(connection)
                    break
            else:
                # previously unseen params, create new connection
                kwargs = self._kwargs.copy()
                kwargs.update(host)
                connection = AioConnection(**kwargs, loop=self._loop)
                connections.append(connection)

        self._connection_pool = ConnectionPool(connections, loop=self._loop)

    async def _get_sniff_data(self, initial=False):
        previous_sniff = self.last_sniff
        try:
            # reset last_sniff timestamp
            self.last_sniff = self._loop.time()
            for c in self._connection_pool.connections:
                try:
                    # use small timeout for the sniffing request,
                    # should be a fast api call
                    _, headers, node_info = await c.perform_request(
                        'GET', '/_nodes/_all/http',
                        timeout=self._sniff_timeout if not initial else None)
                    node_info = self.deserializer.loads(
                        node_info, headers.get('content-type'))
                    break
                except (ConnectionError, SerializationError):
                    pass
            else:
                raise TransportError("N/A", "Unable to sniff hosts.")
        except:
            # keep the previous value on error
            self.last_sniff = previous_sniff
            raise

        return list(node_info['nodes'].values())

    def _get_host_info(self, host_info):
        host = {}
        address = host_info.get('http', {}).get('publish_address')

        # malformed or no address given
        if not address or ':' not in address:
            return None

        host['host'], host['port'] = address.rsplit(':', 1)
        host['port'] = int(host['port'])

        # ignore master only nodes
        if host_info.get('roles', []) == ['master']:
            return None
        return host

    async def sniff_hosts(self, initial=False):
        node_info = await self._get_sniff_data(initial)
        hosts = list(filter(None, (self._get_host_info(n) for n in node_info)))
        # we weren't able to get any nodes, maybe using an incompatible
        # transport_schema or host_info_callback blocked all - raise error.
        if not hosts:
            raise TransportError(
                "N/A", "Unable to sniff hosts - no viable hosts found.")
        self._set_connections(hosts)

    async def get_connection(self):
        if self._sniffer_timeout:
            if self._loop.time() >= self._last_sniff + self._sniffer_timeout:
                await self.sniff_hosts()
        return await self._connection_pool.get_connection()

    async def _mark_dead(self, connection):
        # mark as dead even when sniffing to avoid
        # hitting this host during the sniff process
        await self._connection_pool.mark_dead(connection)
        if self.sniff_on_connection_fail:
            await self.sniff_hosts()

    def perform_request(self, method, url, params=None, body=None):
        return self.async_req(method, url, params, body)

    async def async_req(self, method, url, params, body):
        if body is not None:
            body = self._serializer.dumps(body)

        if params:
            timeout = params.pop('request_timeout', None)
            ignore = params.pop('ignore', ())
            if isinstance(ignore, int):
                ignore = (ignore, )
        else:
            ignore = ()
            timeout = None

        for attempt in range(self._max_retries + 1):
            conn = await self.get_connection()

            try:
                status, headers, data = await conn.perform_request(
                    method, url, params, body, ignore=ignore, timeout=timeout)
            except TransportError as e:
                if method == 'HEAD' and e.status_code == 404:
                    return False

                retry = False
                if isinstance(e, ConnectionTimeout):
                    retry = self._retry_on_timeout
                elif isinstance(e, ConnectionError):
                    retry = True
                elif e.status_code in self._retry_on_status:
                    retry = True

                if retry:
                    # only mark as dead if we are retrying
                    await self._mark_dead(conn)
                    # raise exception on last retry
                    if attempt == self.max_retries:
                        raise
                else:
                    raise
            else:
                if method == 'HEAD':
                    return 200 <= status < 300

                # connection didn't fail, confirm it's live status
                await self._connection_pool.mark_live(conn)
                if data:
                    data = self._deserializer.loads(
                        data, headers.get('content-type'))
                return data

    def close(self):
        self._connection_pool.close()

