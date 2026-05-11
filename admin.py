from flask import Flask, render_template, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix
import requests
import os

app = Flask(__name__, template_folder='templates')
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_prefix=1)

WORKER_URL = os.environ.get('WORKER_URL', 'http://worker:5000')
SITES_URL = os.environ.get('SITES_URL', 'https://nodify-ssg-sites.azirar.ovh')

@app.route('/')
def index():
    return render_template('index.html', sites_url=SITES_URL)

@app.route('/api/sites')
def api_sites():
    resp = requests.get(f"{WORKER_URL}/list")
    return jsonify(resp.json())

@app.route('/api/delete/<name>', methods=['DELETE'])
def api_delete(name):
    resp = requests.delete(f"{WORKER_URL}/delete/{name}")
    return jsonify(resp.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
