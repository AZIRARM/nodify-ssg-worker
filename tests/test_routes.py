import worker


def test_health(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.get_json() == {'status': 'ok'}


def test_list_empty(client):
    r = client.get('/list')
    assert r.status_code == 200
    assert r.get_json() == []


def test_delete_missing(client):
    r = client.delete('/delete/nope')
    assert r.status_code == 404


def test_delete_rejects_path_traversal(client):
    r = client.delete('/delete/..')
    assert r.status_code == 400


def test_webhook_rejects_missing_code(client):
    r = client.post('/webhook', json={'client_payload': {}})
    assert r.status_code == 400


def test_webhook_rejects_bad_secret(client, monkeypatch):
    monkeypatch.setattr(worker, 'WORKER_SECRET', 'topsecret')
    r = client.post('/webhook', json={'client_payload': {'code': 'R'}})
    assert r.status_code == 401


def test_webhook_accepts_correct_secret(client, monkeypatch, fake_api):
    monkeypatch.setattr(worker, 'WORKER_SECRET', 'topsecret')
    fake_api.set('contents/node/code/ROOT', [])
    fake_api.set('nodes/parent/ROOT', [])

    r = client.post(
        '/webhook',
        json={'client_payload': {'code': 'ROOT', 'folder': 'mysite'}},
        headers={'Authorization': 'Bearer topsecret'},
    )
    assert r.status_code == 200
    assert r.get_json() == {'status': 'ok', 'site': 'mysite'}


def test_webhook_end_to_end_replaces_links(client, fake_api, tmp_path):
    fake_api.set('contents/node/code/ROOT', [
        {'code': 'PAGE-A', 'type': 'HTML', 'ssg': True,
         'payload': '<a href="PAGE-B">go</a>'},
        {'code': 'PAGE-B', 'type': 'HTML', 'ssg': True,
         'fileName': 'target.html', 'payload': 'target'},
    ])
    fake_api.set('nodes/parent/ROOT', [])

    r = client.post('/webhook',
                    json={'client_payload': {'code': 'ROOT', 'folder': 's'}})
    assert r.status_code == 200

    site = tmp_path / 's'
    assert (site / 'PAGE-A.html').read_text(encoding='utf-8') == \
        '<a href="target.html">go</a>'
    assert (site / 'target.html').read_text(encoding='utf-8') == 'target'


def test_webhook_with_real_landingpage_node(
        client, fake_api, tmp_path,
        real_landingpage_node, real_landingpage_contents):
    fake_api.set('contents/node/code/LANDINGPAGE-DEV-0643497554',
                 real_landingpage_contents)
    fake_api.set('nodes/parent/LANDINGPAGE-DEV-0643497554', [])

    r = client.post('/webhook', json={
        'client_payload': {
            'code': 'LANDINGPAGE-DEV-0643497554',
            'folder': 'mysite',
            'ssg': True,
        },
    })
    assert r.status_code == 200
    assert r.get_json() == {'status': 'ok', 'site': 'mysite'}

    site = tmp_path / 'mysite'

    assert (site / 'landingpage' / 'index.html').exists()
    assert (site / 'HTML-DEV-1092265001.html').exists()

    for skipped in [
        'HTML-DEV-9308029478.html',
        'HTML-DEV-6792117332.html',
        'HTML-DEV-0572598271.html',
        'STYLE-DEV-6197530005.html',
        'SCRIPT-DEV-9940367357.html',
    ]:
        assert not (site / skipped).exists()


def test_real_node_rewrite_changes_nothing(
        client, fake_api, tmp_path,
        real_landingpage_node, real_landingpage_contents):
    fake_api.set('contents/node/code/LANDINGPAGE-DEV-0643497554',
                 real_landingpage_contents)
    fake_api.set('nodes/parent/LANDINGPAGE-DEV-0643497554', [])

    r = client.post('/webhook', json={
        'client_payload': {'code': 'LANDINGPAGE-DEV-0643497554', 'folder': 'mysite'},
    })
    assert r.status_code == 200
    assert r.get_json() == {'status': 'ok', 'site': 'mysite'}

    site = tmp_path / 'mysite'

    assert (site / 'landingpage' / 'index.html').read_text(encoding='utf-8') == \
        '<!DOCTYPE html><html>Nodify</html>'
    assert (site / 'HTML-DEV-1092265001.html').read_text(encoding='utf-8') == \
        '<!DOCTYPE html>README'

    mapping_codes = ['HTML-DEV-1092265001', 'HTML-DEV-3480269024']
    for f in [site / 'landingpage' / 'index.html', site / 'HTML-DEV-1092265001.html']:
        text = f.read_text(encoding='utf-8')
        for code in mapping_codes:
            assert code not in text, f"{code} should not appear in {f.name}"


def test_real_ssg_test_node_end_to_end(client, fake_api, tmp_path):
    tiny_b64 = (
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
        'YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
    )
    contents = [
        {'code': 'HTML-DEV-1794911188250', 'type': 'HTML', 'ssg': True,
         'fileName': 'index.html',
         'payload': (
             '<header><h3>HELLO WORLD</h3></header>\n'
             '<img src="https://nodify-api.azirar.ovh/contents/code/'
             'PICTURE-DEV-1794913304849/file?status=PUBLISHED" alt="Mhamed"/>'
         )},
        {'code': 'PICTURE-DEV-1794913304849', 'type': 'PICTURE', 'ssg': True,
         'folder': 'pictures', 'fileName': 'mhamed.jpg',
         'file': {'data': f'data:image/jpeg;base64,{tiny_b64}'}},
    ]
    fake_api.set('contents/node/code/SSG_TEST-DEV-1794911122281', contents)
    fake_api.set('nodes/parent/SSG_TEST-DEV-1794911122281', [])

    r = client.post('/webhook', json={
        'client_payload': {'code': 'SSG_TEST-DEV-1794911122281', 'folder': 'ssg_test'},
    })
    assert r.status_code == 200

    site = tmp_path / 'ssg_test'

    html = (site / 'index.html').read_text(encoding='utf-8')
    assert '<h3>HELLO WORLD</h3>' in html

    assert (site / 'pictures' / 'mhamed.jpg').exists()
    assert (site / 'pictures' / 'mhamed.jpg').read_bytes()

    assert 'PICTURE-DEV-1794913304849' not in html
    assert 'nodify-api' not in html
    assert 'contents/code' not in html
    assert 'src="pictures/mhamed.jpg"' in html