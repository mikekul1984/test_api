import pytest
import requests
from urllib.parse import urljoin
from extra.configs import TESTUSER


def pytest_addoption(parser):
    parser.addoption("--host",
        action="store",
        default="localhost",
        help="host of the server under test (e.g. localhost or searchbox-1.dev.search.km)."
    )
    parser.addoption("--port",
        action="store",
        default=80,
        help="port of the server under test."
    )
    parser.addoption("--api_version",
        action="store",
        default="0.1",
        help="port of the server under test."
    )

@pytest.fixture(scope='session')
def host_url(request):
    '''Construct base url of goropka webserver ({scheme}://{host}:{port}) under test and check connection.
    '''
    base_url = "{host}/apis/{}:{port}".format(
        host=request.config.getoption("host"),
        version=request.config.getoption("api_version"),
        port=request.config.getoption("port")
    )
    r = requests.head(base_url)
    r.raise_for_status()
    return base_url

@pytest.fixture(scope='session')
def med_api(host_url):
    return BaseClient(host_url, root='/')

class BaseClient(object):
    '''Convenience interface for any REST API
    '''
    def __init__(self, base_url, root='/'):
        self._base = urljoin(base_url, root)
        self._session = requests.Session()

    def __getattr__(self, request_method):
        '''Proxy for `self.request(request_method, ...)`.
        '''
        return lambda *args, **kwargs: self.request(request_method, *args, **kwargs)

    def request(self, method, url_path=None, **kwargs):
        '''Send request using http verb `method` to a `url_path` (absolute or relative).
        All `kwargs` are passed to a requests.request method.
        Return requests.Response object.
        '''
        return self._session.request(method, self._prepare_url(url_path), allow_redirects=False, **kwargs)

    def _prepare_url(self, url_path):
        '''Prepare a valid URL from `url_path` using `self._base` as a base URL.
        '''
        return urljoin(self._base, url_path) if url_path else self._base

    def update_root(self, new_root):
        '''Update the base URL (aka root) which is used for all requests.
        '''
        self._base = self._prepare_url(new_root)