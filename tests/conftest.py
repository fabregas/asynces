import docker as libdocker
import asyncio
import pytest
import uuid
import gc
import logging
from pytest_mock import mocker


log = logging.getLogger('es-tests')


def pytest_addoption(parser):
    parser.addoption('--docker-image', action='store',
                     default='elasticsearch:5.1.2',
                     help='Mysterion docker image to use')


@pytest.fixture(scope='session')
def docker(request):
    return libdocker.Client(version='auto')


def start_container(docker, container_id):
    docker.start(container=container_id)
    resp = docker.inspect_container(container=container_id)
    return resp["NetworkSettings"]["IPAddress"]


def container_logs(docker, container, srv_name):
    c_logs = docker.logs(
        container=container['Id'], stdout=True, stderr=True, follow=False)
    log.info("========== captured {} service log =========".format(srv_name))
    for msg in c_logs.decode().splitlines():
        log.info(msg)
    log.info("============================================")


@pytest.fixture(scope='session')
def session_id():
    return str(uuid.uuid4())


@pytest.yield_fixture(scope='class')
def loop(request):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(None)

    yield loop

    if not loop._closed:
        loop.call_soon(loop.stop)
        loop.run_forever()
        loop.close()
    gc.collect()
    asyncio.set_event_loop(None)


@pytest.yield_fixture(scope='session')
def es_server(request, docker, session_id):
    image = request.config.getoption('--docker-image')

    print("* pulling elasticsearch image ...")
    docker.pull(image)
    container = docker.create_container(
        image=image,
        name='asynces-es-tests-{}'.format(session_id),
    )
    ip = start_container(docker, container['Id'])
    print("* waiting es service ...")
    yield ip, 9200
    docker.kill(container=container['Id'])
    container_logs(docker, container, 'elasticsearch')
    docker.remove_container(container['Id'])


@pytest.fixture(scope='class')
def setup_test_class(request, loop, es_server):
    request.cls.loop = loop
    request.cls.es_host, request.cls.es_port = es_server
    request.cls.mocker = mocker
    loop.run_until_complete(request.cls.wait_es())
