"""
Nodify SSG Worker
=================

Receives a Nodify webhook, fetches the full content tree of a root node
(via the Nodify API), and generates a static site on disk.

How it works
------------
1. The webhook carries the root node `code` (`client_payload.code`)
   and the site name (`client_payload.folder`, optional — defaults to "default").
2. We walk the tree recursively:
   - A content / node is processed only if `ssg is True` (strict).
   - A NODE's folder = its `folder` field if set, otherwise its `code`.
   - A CONTENT's folder = its `folder` field if set; the file is written
     in a subfolder of the current node's output dir. If unset, the file
     is written directly in the node's output dir.
   - A child node lives inside its parent node's folder.
3. For every generated content (text or binary), we record:
       mapping[code] = path relative to the site root
   For TEXT contents only, we also add the absolute path to `text_files`.
4. After the full generation, we rewrite each file in `text_files`:
   - Nodify API file URLs (https://.../contents/code/{code}/file[?query])
     are replaced ENTIRELY by the local relative path of the generated file.
   - Raw `code` occurrences (outside API URLs) are replaced by the local
     relative path, as before.

Binary contents are read from `file.data` (base64 data URI). `payload` is
NOT used for binaries — this keeps the worker independent from the API
response shape, should it change later.
"""

from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import re
import shutil
import base64
import json
import urllib.request


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_prefix=1)


# ---------------------------------------------------------------------------
# Configuration (environment variables)
# ---------------------------------------------------------------------------
API_URL = os.environ.get('NODIFY_API_URL', '')
WORKER_SECRET = os.environ.get('WORKER_SECRET', '')


def get_sites_dir():
    """Return the sites directory, creating it on first use."""
    path = os.environ.get('SITES_DIR', '/sites')
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Regex: Nodify API file URLs
# ---------------------------------------------------------------------------
API_FILE_URL_RE = re.compile(
    r'https?://[^"\'\s]*/contents/code/([A-Za-z0-9\-]+)/file(?:\?[^"\'\s]*)?'
)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def fetch_json(url):
    """Fetch a URL and return the parsed JSON, or None if empty/invalid."""
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            raw = resp.read().decode('utf-8')
    except Exception as e:
        print(f"[fetch_json] error for {url}: {e}")
        return None

    if not raw or raw == 'null':
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[fetch_json] invalid JSON from {url}: {e}")
        return None


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def ensure_parent_dir(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_text(path, content):
    ensure_parent_dir(path)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def write_bytes(path, data):
    ensure_parent_dir(path)
    with open(path, 'wb') as f:
        f.write(data)


# ---------------------------------------------------------------------------
# Pass 1: generate files + collect
# ---------------------------------------------------------------------------
def collect_node(node_code, output_dir, site_root, mapping, text_files):
    """Process a node recursively.

    Side effects:
    - writes files on disk;
    - `mapping[code] = path relative to the site root` for ALL contents;
    - `text_files.add(absolute path)` ONLY for text contents.
    """
    # ---- 1a. Node contents ---------------------------------------------
    contents = fetch_json(
        f"{API_URL}/contents/node/code/{node_code}?fillValues=true&withFiles=true"
    )
    if contents is not None:
        if not isinstance(contents, list):
            contents = [contents]

        for item in contents:
            if not isinstance(item, dict):
                continue
            if item.get('ssg') is not True:          # strict filter
                continue

            content_type = item.get('type', '')
            code = item.get('code')
            file_name = item.get('fileName')
            payload = item.get('payload')
            content_folder = item.get('folder')      # NEW: content folder

            if not code:
                continue

            # NEW: if the content has a folder, write it in a subfolder
            # of the current node's output dir.
            content_output_dir = (
                os.path.join(output_dir, content_folder)
                if content_folder
                else output_dir
            )

            is_binary = content_type in ('FILE', 'PICTURE')

            # ---- Binaries: FILE / PICTURE (handled the same way) ----
            if is_binary:
                # Read `file.data` (base64 data URI), NOT `payload`.
                file_obj = item.get('file') or {}
                data_str = file_obj.get('data')
                if not data_str:
                    continue

                if ',' in data_str:
                    data_str = data_str.split(',', 1)[1]

                try:
                    file_bytes = base64.b64decode(data_str)
                except Exception as e:
                    print(f"[collect_node] base64 error for {code}: {e}")
                    continue

                filename = file_name or f"{code}.bin"
                abs_path = os.path.join(content_output_dir, filename)
                write_bytes(abs_path, file_bytes)

                mapping[code] = os.path.relpath(abs_path, site_root).replace(os.sep, '/')
                continue

            # ---- Texts: anything else ----
            if payload is None:
                continue

            filename = file_name or f"{code}.html"
            abs_path = os.path.join(content_output_dir, filename)

            if isinstance(payload, (dict, list)):
                text = json.dumps(payload, indent=2, ensure_ascii=False)
            else:
                text = str(payload)

            write_text(abs_path, text)

            mapping[code] = os.path.relpath(abs_path, site_root).replace(os.sep, '/')
            text_files.add(abs_path)

    # ---- 1b. Child nodes -----------------------------------------------
    children = fetch_json(f"{API_URL}/nodes/parent/{node_code}")
    if children is not None:
        if not isinstance(children, list):
            children = [children]

        for node in children:
            if not isinstance(node, dict):
                continue
            if node.get('ssg') is not True:          # strict filter
                continue

            child_code = node.get('code')
            if not child_code:
                continue

            # Node folder = `folder` if set, otherwise its `code`.
            child_dirname = node.get('folder') or child_code
            child_dir = os.path.join(output_dir, child_dirname)
            os.makedirs(child_dir, exist_ok=True)

            collect_node(child_code, child_dir, site_root, mapping, text_files)


# ---------------------------------------------------------------------------
# Pass 2: rewrite text files
# ---------------------------------------------------------------------------
def rewrite_site(site_root, mapping, text_files):
    """Rewrite every file in `text_files`.

    1. Nodify API file URLs are replaced ENTIRELY by a unique placeholder.
    2. Raw `code` occurrences (outside API URLs) are replaced by the local
       relative path (longer codes first, to avoid substring collisions).
    3. Placeholders are replaced by the local relative path.
    """
    for abs_path in sorted(text_files):
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, OSError) as e:
            print(f"[rewrite_site] skip {abs_path}: {e}")
            continue

        current_dir = os.path.dirname(abs_path)

        def local_path_for(code):
            site_rel = mapping[code]
            target_abs = os.path.join(site_root, site_rel)
            return os.path.relpath(target_abs, current_dir).replace(os.sep, '/')

        # --- 1. Replace Nodify API file URLs with a placeholder ---
        placeholders = {}   # placeholder -> code
        counter = [0]

        def _replace_api_url(match):
            code = match.group(1)
            if code not in mapping:
                return match.group(0)   # leave unknown codes untouched
            counter[0] += 1
            ph = f"\x00NODIFY_URL_{counter[0]}\x00"
            placeholders[ph] = code
            return ph

        content = API_FILE_URL_RE.sub(_replace_api_url, content)

        # --- 2. Replace remaining raw code occurrences ---
        replacements = []
        for code in mapping:
            if code not in content:
                continue
            replacements.append((code, local_path_for(code)))

        for code, rel_path in sorted(replacements, key=lambda x: -len(x[0])):
            content = content.replace(code, rel_path)

        # --- 3. Replace placeholders by the local path ---
        for ph, code in placeholders.items():
            content = content.replace(ph, local_path_for(code))

        try:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except OSError as e:
            print(f"[rewrite_site] cannot write {abs_path}: {e}")
            
# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,DELETE'
    return response


@app.route('/webhook', methods=['OPTIONS', 'POST'])
def webhook():
    if request.method == 'OPTIONS':
        return '', 200

    if WORKER_SECRET:
        auth = request.headers.get('Authorization', '')
        if auth != f"Bearer {WORKER_SECRET}":
            return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    client_payload = data.get('client_payload', {}) or {}
    node_code = client_payload.get('code')
    site_name = client_payload.get('folder') or 'default'

    if not node_code:
        return jsonify({'error': 'No node code'}), 400

    sites_dir = get_sites_dir()
    site_root = os.path.join(sites_dir, site_name)
    if os.path.exists(site_root):
        shutil.rmtree(site_root)
    os.makedirs(site_root, exist_ok=True)

    mapping = {}
    text_files = set()
    collect_node(node_code, site_root, site_root, mapping, text_files)

    rewrite_site(site_root, mapping, text_files)

    return jsonify({'status': 'ok', 'site': site_name}), 200


@app.route('/list', methods=['GET'])
def list_sites():
    sites_dir = get_sites_dir()
    sites = []
    if os.path.isdir(sites_dir):
        for name in os.listdir(sites_dir):
            path = os.path.join(sites_dir, name)
            if os.path.isdir(path):
                size = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, _, files in os.walk(path)
                    for f in files
                )
                sites.append({'name': name, 'size': round(size / 1024, 2)})
    return jsonify(sites)


@app.route('/delete/<name>', methods=['DELETE'])
def delete_site(name):
    if not name or name in ('.', '..') or '/' in name or '\\' in name:
        return jsonify({'error': 'invalid name'}), 400

    path = os.path.join(get_sites_dir(), name)
    if os.path.isdir(path):
        shutil.rmtree(path)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'not found'}), 404


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)