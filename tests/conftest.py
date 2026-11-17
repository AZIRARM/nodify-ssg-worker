import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def fake_api(monkeypatch):
    import worker
    routes = {}

    def _fake_fetch_json(url):
        for suffix, payload in routes.items():
            if suffix in url:
                return payload
        return None

    class FakeAPI:
        def set(self, url_suffix, payload):
            routes[url_suffix] = payload

    fake = FakeAPI()
    monkeypatch.setattr(worker, 'fetch_json', _fake_fetch_json)
    return fake


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('SITES_DIR', str(tmp_path))
    import worker
    worker.app.config['TESTING'] = True
    return worker.app.test_client()


@pytest.fixture
def real_landingpage_node():
    """The real LANDINGPAGE-DEV-0643497554 node (ssg: true, folder: 'landingpage')."""
    return {
        'code': 'LANDINGPAGE-DEV-0643497554',
        'name': 'LandingPage',
        'folder': 'landingpage',
        'ssg': True,
    }


@pytest.fixture
def real_landingpage_contents():
    """The real contents of LANDINGPAGE-DEV-0643497554, trimmed to essentials.

    Kept minimal but faithful: codes, ssg flags, fileNames, payloads.
    """
    return [
        # ssg: false → must be skipped
        {'code': 'HTML-DEV-9308029478', 'type': 'HTML', 'ssg': False,
         'description': 'Feature', 'payload': '<section>features</section>'},

        # ssg: false → must be skipped
        {'code': 'HTML-DEV-6792117332', 'type': 'HTML', 'ssg': False,
         'description': 'Header', 'payload': '<header>hero</header>'},

        # ssg: true, fileName: null → HTML-DEV-1092265001.html
        {'code': 'HTML-DEV-1092265001', 'type': 'HTML', 'ssg': True,
         'description': 'README (PRE REQUIES)', 'payload': '<!DOCTYPE html>README'},

        # ssg: false → must be skipped
        {'code': 'HTML-DEV-0572598271', 'type': 'HTML', 'ssg': False,
         'description': 'Footer', 'payload': '<footer>footer</footer>'},

        # ssg: false → must be skipped
        {'code': 'STYLE-DEV-6197530005', 'type': 'STYLE', 'ssg': False,
         'description': 'Styles', 'payload': 'body { font-family: Arial; }'},

        # ssg: false → must be skipped
        {'code': 'SCRIPT-DEV-9940367357', 'type': 'SCRIPT', 'ssg': False,
         'description': 'Build Sections', 'payload': 'function writeSections(){}'},

        # ssg: true, fileName: 'index.html', folder: 'landingpage' (IGNORED)
        {'code': 'HTML-DEV-3480269024', 'type': 'HTML', 'ssg': True,
         'folder': 'landingpage', 'fileName': 'index.html',
         'description': 'Page principale',
         'payload': '<!DOCTYPE html><html>Nodify</html>'},
    ]