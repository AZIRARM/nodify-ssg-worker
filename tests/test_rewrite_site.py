import worker


def test_replaces_code_with_relative_path(tmp_path):
    (tmp_path / 'a.html').write_text('see AB12 now', encoding='utf-8')
    mapping = {'AB12': 'sub/b.html'}

    worker.rewrite_site(str(tmp_path), mapping, {str(tmp_path / 'a.html')})

    assert (tmp_path / 'a.html').read_text(encoding='utf-8') == 'see sub/b.html now'


def test_relative_path_from_subfolder_uses_dotdot(tmp_path):
    sub = tmp_path / 'sub'
    sub.mkdir()
    (sub / 'x.html').write_text('link ROOT1', encoding='utf-8')
    mapping = {'ROOT1': 'index.html'}

    worker.rewrite_site(str(tmp_path), mapping, {str(sub / 'x.html')})

    assert (sub / 'x.html').read_text(encoding='utf-8') == 'link ../index.html'


def test_longer_codes_replaced_first(tmp_path):
    (tmp_path / 'f.html').write_text('ABC ABC123', encoding='utf-8')
    mapping = {'ABC': 'short.html', 'ABC123': 'long.html'}

    worker.rewrite_site(str(tmp_path), mapping, {str(tmp_path / 'f.html')})

    assert (tmp_path / 'f.html').read_text(encoding='utf-8') == 'short.html long.html'


def test_only_listed_files_are_rewritten(tmp_path):
    (tmp_path / 'a.html').write_text('AB12', encoding='utf-8')
    (tmp_path / 'b.html').write_text('AB12', encoding='utf-8')
    mapping = {'AB12': 'target.html'}

    worker.rewrite_site(str(tmp_path), mapping, {str(tmp_path / 'a.html')})

    assert (tmp_path / 'a.html').read_text(encoding='utf-8') == 'target.html'
    assert (tmp_path / 'b.html').read_text(encoding='utf-8') == 'AB12'


def test_api_file_url_is_replaced_by_local_path(tmp_path):
    """A Nodify API file URL must be replaced by the local relative path,
    NOT by a corrupted URL."""
    (tmp_path / 'page.html').write_text(
        '<img src="https://nodify-api.azirar.ovh/contents/code/IMG1/file?status=PUBLISHED">',
        encoding='utf-8',
    )
    mapping = {'IMG1': 'IMG1.bin'}

    worker.rewrite_site(str(tmp_path), mapping, {str(tmp_path / 'page.html')})

    html = (tmp_path / 'page.html').read_text(encoding='utf-8')
    assert html == '<img src="IMG1.bin">'
    assert 'nodify-api' not in html
    assert 'contents/code' not in html


def test_api_url_with_unknown_code_is_left_untouched(tmp_path):
    """If the code is not in mapping (e.g. ssg:false), the URL is preserved."""
    (tmp_path / 'page.html').write_text(
        '<img src="https://nodify-api.azirar.ovh/contents/code/UNKNOWN/file">',
        encoding='utf-8',
    )
    worker.rewrite_site(str(tmp_path), {}, {str(tmp_path / 'page.html')})

    html = (tmp_path / 'page.html').read_text(encoding='utf-8')
    assert 'https://nodify-api.azirar.ovh/contents/code/UNKNOWN/file' in html