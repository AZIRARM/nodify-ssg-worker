from flask import Flask, request, jsonify
import os, subprocess, base64, json, shutil

app = Flask(__name__)

API_URL = os.environ.get('NODIFY_API_URL', '')
WORKER_SECRET = os.environ.get('WORKER_SECRET', '')
SITES_DIR = os.environ.get('SITES_DIR', '/sites')
os.makedirs(SITES_DIR, exist_ok=True)

def fetch_url(url):
    result = subprocess.run(['curl', '-s', url], capture_output=True, text=True)
    return result.stdout

def save_content(payload, path):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        if isinstance(payload, (dict, list)):
            json.dump(payload, f, indent=2, ensure_ascii=False)
        else:
            f.write(str(payload))

def save_file(data, path):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)

def process_node(node_code, output_dir):
    url = f"{API_URL}/contents/node/code/{node_code}?fillValues=true&withFiles=true"
    response = fetch_url(url)

    if response and response != 'null':
        try:
            items = json.loads(response)
            if not isinstance(items, list):
                items = [items]
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get('ssg') is False or item.get('ssg') == 'false':
                    continue
                content_type = item.get('type', '')
                code = item.get('code', '')
                file_name = item.get('fileName')
                payload = item.get('payload')
                if content_type in ['FILE', 'PICTURE']:
                    file_obj = item.get('file')
                    if file_obj and 'data' in file_obj:
                        data_str = file_obj['data']
                        if ',' in data_str:
                            base64_data = data_str.split(',', 1)[1]
                        else:
                            base64_data = data_str
                        file_bytes = base64.b64decode(base64_data)
                        filename = file_name if file_name else f"{code}.bin"
                        save_file(file_bytes, os.path.join(output_dir, filename))
                elif payload:
                    filename = file_name if file_name else f"{code}.html"
                    save_content(payload, os.path.join(output_dir, filename))
        except:
            pass

    url = f"{API_URL}/nodes/parent/{node_code}"
    response = fetch_url(url)
    if response and response != 'null' and response != '[]':
        try:
            nodes = json.loads(response)
            if not isinstance(nodes, list):
                nodes = [nodes]
            for node in nodes:
                child_code = node.get('code')
                child_folder = node.get('folder')
                node_name = node.get('name', child_code)
                node_ssg = node.get('ssg', True)
                if child_code and (node_ssg is not False and node_ssg != 'false'):
                    target_dir = os.path.join(output_dir, child_folder if child_folder else node_name)
                    os.makedirs(target_dir, exist_ok=True)
                    process_node(child_code, target_dir)
        except:
            pass

@app.route('/webhook', methods=['POST'])
def webhook():
    # Vérification du secret
    if WORKER_SECRET:
        auth_header = request.headers.get('Authorization', '')
        expected = f"Bearer {WORKER_SECRET}"
        if auth_header != expected:
            return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    node_code = data.get('client_payload', {}).get('code')
    site_name = data.get('client_payload', {}).get('folder', 'default')

    if not node_code:
        return jsonify({'error': 'No node code'}), 400

    site_dir = os.path.join(SITES_DIR, site_name)
    if os.path.exists(site_dir):
        shutil.rmtree(site_dir)
    os.makedirs(site_dir, exist_ok=True)

    process_node(node_code, site_dir)

    return jsonify({'status': 'ok', 'site': site_name}), 200

@app.route('/list', methods=['GET'])
def list_sites():
    sites = []
    if os.path.exists(SITES_DIR):
        for name in os.listdir(SITES_DIR):
            path = os.path.join(SITES_DIR, name)
            if os.path.isdir(path):
                size = sum(os.path.getsize(os.path.join(dirpath, f))
                          for dirpath, _, files in os.walk(path) for f in files)
                sites.append({'name': name, 'size': round(size / 1024, 2)})
    return jsonify(sites)

@app.route('/delete/<name>', methods=['DELETE'])
def delete_site(name):
    path = os.path.join(SITES_DIR, name)
    if os.path.exists(path):
        shutil.rmtree(path)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'not found'}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)