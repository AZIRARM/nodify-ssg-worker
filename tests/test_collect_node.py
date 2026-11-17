import os
import base64
import pytest
import worker


def _read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Basic collect_node behavior
# ---------------------------------------------------------------------------

def test_skips_content_when_ssg_is_not_true(fake_api, tmp_path):
    fake_api.set('contents/node/code/ROOT', [
        {'code': 'A', 'type': 'HTML', 'ssg': False, 'payload': '<p>A</p>'},
        {'code': 'B', 'type': 'HTML', 'ssg': 'true', 'payload': '<p>B</p>'},  # string, not True
        {'code': 'C', 'type': 'HTML', 'payload': '<p>C</p>'},                 # missing ssg
    ])
    fake_api.set('nodes/parent/ROOT', [])

    mapping, text_files = {}, set()
    worker.collect_node('ROOT', str(tmp_path), str(tmp_path), mapping, text_files)

    assert mapping == {}
    assert text_files == set()


def test_writes_text_content_and_records_mapping(fake_api, tmp_path):
    fake_api.set('contents/node/code/ROOT', [
        {'code': 'AB12', 'type': 'HTML', 'ssg': True, 'payload': '<p>hi</p>'},
    ])
    fake_api.set('nodes/parent/ROOT', [])

    mapping, text_files = {}, set()
    worker.collect_node('ROOT', str(tmp_path), str(tmp_path), mapping, text_files)

    expected_file = tmp_path / 'AB12.html'
    assert expected_file.read_text(encoding='utf-8') == '<p>hi</p>'
    assert mapping == {'AB12': 'AB12.html'}
    assert text_files == {str(expected_file)}


def test_uses_fileName_when_provided(fake_api, tmp_path):
    fake_api.set('contents/node/code/ROOT', [
        {'code': 'AB12', 'type': 'HTML', 'ssg': True, 'fileName': 'about.html', 'payload': 'x'},
    ])
    fake_api.set('nodes/parent/ROOT', [])

    mapping, _ = {}, set()
    worker.collect_node('ROOT', str(tmp_path), str(tmp_path), mapping, _)

    assert (tmp_path / 'about.html').exists()
    assert mapping == {'AB12': 'about.html'}


def test_binary_file_is_written_but_not_marked_as_text(fake_api, tmp_path):
    raw = b'\x89PNG\r\n\x1a\nfake'
    b64 = base64.b64encode(raw).decode()

    fake_api.set('contents/node/code/ROOT', [
        {'code': 'IMG1', 'type': 'PICTURE', 'ssg': True,
         'file': {'data': f'data:image/png;base64,{b64}'}},
    ])
    fake_api.set('nodes/parent/ROOT', [])

    mapping, text_files = {}, set()
    worker.collect_node('ROOT', str(tmp_path), str(tmp_path), mapping, text_files)

    assert (tmp_path / 'IMG1.bin').read_bytes() == raw
    assert mapping == {'IMG1': 'IMG1.bin'}
    assert text_files == set()   # binary never added


# ---------------------------------------------------------------------------
# Content folder (NEW RULE): a content with `folder` goes into a subfolder
# ---------------------------------------------------------------------------

def test_content_with_folder_creates_subfolder(fake_api, tmp_path):
    """A content with folder='pictures' and fileName='mhamed.jpg' must be
    written to pictures/mhamed.jpg (subfolder of the node's output dir)."""
    tiny_b64 = (
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
        'YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
    )
    fake_api.set('contents/node/code/ROOT', [
        {'code': 'IMG1', 'type': 'PICTURE', 'ssg': True,
         'folder': 'pictures', 'fileName': 'mhamed.jpg',
         'file': {'data': f'data:image/jpeg;base64,{tiny_b64}'}},
    ])
    fake_api.set('nodes/parent/ROOT', [])

    mapping, text_files = {}, set()
    worker.collect_node('ROOT', str(tmp_path), str(tmp_path), mapping, text_files)

    assert (tmp_path / 'pictures' / 'mhamed.jpg').exists()
    assert mapping == {'IMG1': 'pictures/mhamed.jpg'}
    assert text_files == set()   # binary


def test_content_without_folder_goes_to_node_root(fake_api, tmp_path):
    """A content without folder goes directly in the node's output dir."""
    fake_api.set('contents/node/code/ROOT', [
        {'code': 'HTML1', 'type': 'HTML', 'ssg': True,
         'payload': 'hello'},
    ])
    fake_api.set('nodes/parent/ROOT', [])

    mapping, text_files = {}, set()
    worker.collect_node('ROOT', str(tmp_path), str(tmp_path), mapping, text_files)

    assert (tmp_path / 'HTML1.html').exists()
    assert mapping == {'HTML1': 'HTML1.html'}


def test_text_content_with_folder_creates_subfolder(fake_api, tmp_path):
    """Same rule applies to text contents: folder creates a subfolder."""
    fake_api.set('contents/node/code/ROOT', [
        {'code': 'HTML1', 'type': 'HTML', 'ssg': True,
         'folder': 'blog', 'fileName': 'post.html', 'payload': 'post'},
    ])
    fake_api.set('nodes/parent/ROOT', [])

    mapping, text_files = {}, set()
    worker.collect_node('ROOT', str(tmp_path), str(tmp_path), mapping, text_files)

    assert (tmp_path / 'blog' / 'post.html').read_text(encoding='utf-8') == 'post'
    assert mapping == {'HTML1': 'blog/post.html'}
    assert text_files == {str(tmp_path / 'blog' / 'post.html')}


# ---------------------------------------------------------------------------
# Child nodes
# ---------------------------------------------------------------------------

def test_child_node_goes_into_its_own_folder(fake_api, tmp_path):
    fake_api.set('contents/node/code/ROOT', [])
    fake_api.set('contents/node/code/CHILD', [
        {'code': 'C1', 'type': 'HTML', 'ssg': True, 'payload': 'child'},
    ])
    fake_api.set('nodes/parent/ROOT', [
        {'code': 'CHILD', 'ssg': True, 'folder': 'blog'},
    ])
    fake_api.set('nodes/parent/CHILD', [])

    mapping, text_files = {}, set()
    worker.collect_node('ROOT', str(tmp_path), str(tmp_path), mapping, text_files)

    assert (tmp_path / 'blog' / 'C1.html').read_text(encoding='utf-8') == 'child'
    assert mapping == {'C1': 'blog/C1.html'}


def test_child_node_folder_falls_back_to_code(fake_api, tmp_path):
    fake_api.set('contents/node/code/ROOT', [])
    fake_api.set('contents/node/code/CHILD', [])
    fake_api.set('nodes/parent/ROOT', [
        {'code': 'CHILD', 'ssg': True},   # no folder
    ])
    fake_api.set('nodes/parent/CHILD', [])

    worker.collect_node('ROOT', str(tmp_path), str(tmp_path), {}, set())

    assert (tmp_path / 'CHILD').is_dir()


def test_child_node_with_ssg_false_is_skipped(fake_api, tmp_path):
    fake_api.set('contents/node/code/ROOT', [])
    fake_api.set('nodes/parent/ROOT', [
        {'code': 'CHILD', 'ssg': False},
    ])
    # No route for contents/node/code/CHILD → if it were called, fetch_json returns None
    worker.collect_node('ROOT', str(tmp_path), str(tmp_path), {}, set())

    assert not (tmp_path / 'CHILD').exists()


# ---------------------------------------------------------------------------
# Real-world LANDINGPAGE node
# ---------------------------------------------------------------------------
def test_real_node_skips_ssg_false_contents(
        fake_api, tmp_path, real_landingpage_node, real_landingpage_contents):
    """Only ssg: true contents are written; ssg: false ones are ignored."""
    fake_api.set('contents/node/code/LANDINGPAGE-DEV-0643497554',
                 real_landingpage_contents)
    fake_api.set('nodes/parent/LANDINGPAGE-DEV-0643497554', [])

    mapping, text_files = {}, set()
    worker.collect_node(
        'LANDINGPAGE-DEV-0643497554', str(tmp_path), str(tmp_path),
        mapping, text_files,
    )

    # Only the two ssg:true contents must exist
    assert (tmp_path / 'HTML-DEV-1092265001.html').exists()
    assert (tmp_path / 'landingpage' / 'index.html').exists()   # ← folder used

    # All ssg:false contents must be absent
    for skipped in [
        'HTML-DEV-9308029478.html',
        'HTML-DEV-6792117332.html',
        'HTML-DEV-0572598271.html',
        'STYLE-DEV-6197530005.html',
        'SCRIPT-DEV-9940367357.html',
    ]:
        assert not (tmp_path / skipped).exists(), f"{skipped} must not exist"

def test_real_node_mapping_contains_only_ssg_true(
        fake_api, tmp_path, real_landingpage_node, real_landingpage_contents):
    fake_api.set('contents/node/code/LANDINGPAGE-DEV-0643497554',
                 real_landingpage_contents)
    fake_api.set('nodes/parent/LANDINGPAGE-DEV-0643497554', [])

    mapping, text_files = {}, set()
    worker.collect_node(
        'LANDINGPAGE-DEV-0643497554', str(tmp_path), str(tmp_path),
        mapping, text_files,
    )

    assert mapping == {
        'HTML-DEV-1092265001': 'HTML-DEV-1092265001.html',
        'HTML-DEV-3480269024': 'landingpage/index.html',   # ← folder used
    }
    assert text_files == {
        str(tmp_path / 'HTML-DEV-1092265001.html'),
        str(tmp_path / 'landingpage' / 'index.html'),
    }
    
def test_real_node_content_folder_is_used(
        fake_api, tmp_path, real_landingpage_node, real_landingpage_contents):
    """The content HTML-DEV-3480269024 has folder='landingpage' and
    fileName='index.html'. With the NEW RULE, it must be written to
    landingpage/index.html (subfolder), NOT at the node root."""
    fake_api.set('contents/node/code/LANDINGPAGE-DEV-0643497554',
                 real_landingpage_contents)
    fake_api.set('nodes/parent/LANDINGPAGE-DEV-0643497554', [])

    mapping, text_files = {}, set()
    worker.collect_node(
        'LANDINGPAGE-DEV-0643497554', str(tmp_path), str(tmp_path),
        mapping, text_files,
    )

    # index.html is in landingpage/, NOT at the root of tmp_path
    assert (tmp_path / 'landingpage' / 'index.html').exists()
    assert not (tmp_path / 'index.html').exists()
    assert mapping['HTML-DEV-3480269024'] == 'landingpage/index.html'


def test_real_node_payload_is_written_verbatim(
        fake_api, tmp_path, real_landingpage_node, real_landingpage_contents):
    """The payload written must be exactly the payload field (JSON-unescaped)."""
    fake_api.set('contents/node/code/LANDINGPAGE-DEV-0643497554',
                 real_landingpage_contents)
    fake_api.set('nodes/parent/LANDINGPAGE-DEV-0643497554', [])

    worker.collect_node(
        'LANDINGPAGE-DEV-0643497554', str(tmp_path), str(tmp_path), {}, set(),
    )

    index = (tmp_path / 'landingpage' / 'index.html').read_text(encoding='utf-8')
    assert index == '<!DOCTYPE html><html>Nodify</html>'

    readme = (tmp_path / 'HTML-DEV-1092265001.html').read_text(encoding='utf-8')
    assert readme == '<!DOCTYPE html>README'


def test_real_node_with_child_node_in_its_folder(
        fake_api, tmp_path, real_landingpage_node, real_landingpage_contents):
    """A child node of LANDINGPAGE with ssg:true goes into a subfolder
    named after its own folder (or code)."""
    fake_api.set('contents/node/code/LANDINGPAGE-DEV-0643497554',
                 real_landingpage_contents)
    fake_api.set('contents/node/code/BLOG-DEV-0000000001', [
        {'code': 'HTML-DEV-BLOG00001', 'type': 'HTML', 'ssg': True,
         'payload': '<article>post</article>'},
    ])
    fake_api.set('nodes/parent/LANDINGPAGE-DEV-0643497554', [
        {'code': 'BLOG-DEV-0000000001', 'name': 'Blog',
         'folder': 'blog', 'ssg': True},
    ])
    fake_api.set('nodes/parent/BLOG-DEV-0000000001', [])

    mapping, text_files = {}, set()
    worker.collect_node(
        'LANDINGPAGE-DEV-0643497554', str(tmp_path), str(tmp_path),
        mapping, text_files,
    )

    assert (tmp_path / 'landingpage' / 'index.html').exists()
    assert (tmp_path / 'blog' / 'HTML-DEV-BLOG00001.html').exists()
    assert mapping['HTML-DEV-BLOG00001'] == 'blog/HTML-DEV-BLOG00001.html'


def test_real_node_child_without_folder_falls_back_to_code(
        fake_api, tmp_path, real_landingpage_node, real_landingpage_contents):
    fake_api.set('contents/node/code/LANDINGPAGE-DEV-0643497554',
                 real_landingpage_contents)
    fake_api.set('contents/node/code/CHILD-DEV-9999999999', [])
    fake_api.set('nodes/parent/LANDINGPAGE-DEV-0643497554', [
        {'code': 'CHILD-DEV-9999999999', 'name': 'Child', 'ssg': True},
    ])
    fake_api.set('nodes/parent/CHILD-DEV-9999999999', [])

    worker.collect_node(
        'LANDINGPAGE-DEV-0643497554', str(tmp_path), str(tmp_path), {}, set(),
    )

    assert (tmp_path / 'CHILD-DEV-9999999999').is_dir()


def test_real_node_ssg_false_codes_absent_from_mapping(
        fake_api, tmp_path, real_landingpage_node, real_landingpage_contents):
    """Codes of ssg:false contents must NOT be in mapping, so even if another
    payload referenced them, they would never be rewritten."""
    fake_api.set('contents/node/code/LANDINGPAGE-DEV-0643497554',
                 real_landingpage_contents)
    fake_api.set('nodes/parent/LANDINGPAGE-DEV-0643497554', [])

    mapping, text_files = {}, set()
    worker.collect_node('LANDINGPAGE-DEV-0643497554', str(tmp_path), str(tmp_path),
                        mapping, text_files)

    for skipped_code in [
        'HTML-DEV-9308029478',   # Feature
        'HTML-DEV-6792117332',   # Header
        'HTML-DEV-0572598271',   # Footer
        'STYLE-DEV-6197530005',  # Styles
        'SCRIPT-DEV-9940367357', # Build Sections
    ]:
        assert skipped_code not in mapping, \
            f"ssg:false code {skipped_code} must not be in mapping"


# ---------------------------------------------------------------------------
# Real-world SSG_TEST node (binary + text + content folder)
# ---------------------------------------------------------------------------

def test_real_ssg_test_node_picture_is_written_as_binary(fake_api, tmp_path):
    """PICTURE with ssg:true, folder:'pictures', fileName:'mhamed.jpg' →
    written as binary in pictures/, NOT in text_files, mapping points to
    'pictures/mhamed.jpg' (content folder is now USED)."""
    tiny_b64 = (
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
        'YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
    )
    contents = [
        {'code': 'HTML-DEV-1794911227551', 'type': 'HTML', 'ssg': False,
         'payload': '<style>h3{color:red;}</style>'},
        {'code': 'HTML-DEV-1794913051716', 'type': 'HTML', 'ssg': False,
         'payload': '<h3>HELLO WORLD</h3>'},
        {'code': 'HTML-DEV-1794911188250', 'type': 'HTML', 'ssg': True,
         'fileName': 'index.html',
         'payload': '<header><h3>HELLO WORLD</h3></header>'},
        {'code': 'PICTURE-DEV-1794913304849', 'type': 'PICTURE', 'ssg': True,
         'folder': 'pictures', 'fileName': 'mhamed.jpg',
         'file': {'data': f'data:image/jpeg;base64,{tiny_b64}'},
         'payload': f'data:image/jpeg;base64,{tiny_b64}'},
    ]
    fake_api.set('contents/node/code/SSG_TEST-DEV-1794911122281', contents)
    fake_api.set('nodes/parent/SSG_TEST-DEV-1794911122281', [])

    mapping, text_files = {}, set()
    worker.collect_node('SSG_TEST-DEV-1794911122281', str(tmp_path), str(tmp_path),
                        mapping, text_files)

    # index.html written as text at the node root (no folder on this content)
    assert (tmp_path / 'index.html').exists()
    assert mapping['HTML-DEV-1794911188250'] == 'index.html'

    # mhamed.jpg written as binary in pictures/ (content folder USED)
    jpg = tmp_path / 'pictures' / 'mhamed.jpg'
    assert jpg.exists()
    assert jpg.read_bytes()   # non-empty binary
    assert mapping['PICTURE-DEV-1794913304849'] == 'pictures/mhamed.jpg'

    # text_files contains only index.html (binary never rewritten)
    assert text_files == {str(tmp_path / 'index.html')}

    # ssg:false contents absent
    assert 'HTML-DEV-1794911227551' not in mapping
    assert 'HTML-DEV-1794913051716' not in mapping