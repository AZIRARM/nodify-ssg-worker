# Nodify SSG Worker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-2496ED.svg)](https://www.docker.com/)

A lightweight webhook receiver that listens to Nodify CMS events and generates static sites automatically.

## Overview

Nodify SSG Worker is a companion service for [Nodify Headless CMS](https://github.com/AZIRARM/nodify). It receives webhook notifications when you publish content and generates a complete static website from your nodes, sub-nodes, and contents.

## Architecture

Three separate services on three ports:

| Service | Internal Port | Description |
|---------|---------------|-------------|
| **Worker** | 5000 | Receives webhooks, generates static files. Exposes `/webhook`, `/list`, `/delete/{name}`, `/health`. |
| **Admin**  | 8080 | Management UI. **Never receives webhooks.** Proxies `/list` and `/delete` to the worker via `WORKER_URL`. |
| **Web**    | 80   | Serves the generated static sites (read-only). |

> ⚠️ **Routing rule:** the webhook endpoint (`/webhook`) must **always** be routed to the **Worker** (port 5000 internal). The **Admin** (port 8080 internal) is a management UI only — it never handles webhook payloads. Each service must be exposed on its **own** hostname.

## Quick Start

### Using Docker Compose

```bash
git clone https://github.com/AZIRARM/nodify-ssg-worker.git
cd nodify-ssg-worker
cp .env.example .env      # then edit .env
docker compose up -d
```

### Configuration (`.env`)

```env
# Host ports (mapped to internal container ports)
WORKER_PORT=5500          # -> worker:5000
ADMIN_PORT=5590           # -> admin:8080
WEB_PORT=5580             # -> web:80

# Nodify API
NODIFY_API_URL=https://nodify-api.your-domain.com
WORKER_SECRET=your-secret-key-here

# Host path where generated sites are stored (mounted into all 3 services)
SITES_VOLUME=./sites

# Public URL where generated sites are accessible
SITES_URL=http://localhost:5580

# Internal URL the admin uses to reach the worker
WORKER_URL=http://worker:5000     # (Docker)
# WORKER_URL=http://localhost:5000  # (local dev)

# Public URL of the webhook endpoint (shown in the admin UI)
WEBHOOK_URL=http://localhost:5500/webhook
```

### Using custom ports

```bash
WORKER_PORT=5001 ADMIN_PORT=8081 WEB_PORT=3001 docker compose up -d
```

---

## Configuring Nodify Headless CMS

The worker relies on three things from Nodify: **nodes**, **sub-nodes**, and **contents**. Each has to be configured in a specific way for the static site to be generated correctly.

### 1. The root node (webhook trigger)

The webhook is sent by **one node** — the root of the site. Configure it in Nodify as follows:

| Field | Required | Description |
|-------|----------|-------------|
| `code` | ✅ | The node code sent in the webhook payload (`client_payload.code`) |
| `ssg` | ✅ | Must be `true` (strict — `"true"`, `1`, absent → ignored) |
| `triggerUrl` | ✅ | `https://<worker-host>/webhook` (see *Webhook Configuration* below) |
| `triggerSecret` | ✅ | Must match `WORKER_SECRET` in `.env` |
| `folder` | ➖ | **Not used** for the root node. The site folder name comes from `client_payload.folder` in the webhook. |

> The root node itself is **not filtered** by `ssg` in the worker — it is always processed. Only its **contents** and **child nodes** are filtered.

### 2. Sub-nodes (children)

Sub-nodes are processed **recursively**, at any depth.

| Field | Required | Description |
|-------|----------|-------------|
| `code` | ✅ | Node code |
| `ssg` | ✅ | Must be `true` (strict). `false` / absent / `"true"` → **skipped entirely** (no folder, no contents). |
| `folder` | ➖ | Subfolder name inside the **parent node's** output folder. If absent, the node `code` is used. |

**Result:** `SITES_DIR/<site>/<parent-folder>/<sub-folder>/...`

### 3. Contents

Contents are the actual files (HTML pages, CSS, JS, images…).

| Field | Required | Description |
|-------|----------|-------------|
| `code` | ✅ | Unique content code. Used as a placeholder in other payloads (see *Link rewriting*). |
| `type` | ✅ | `HTML`, `STYLE`, `SCRIPT`, `PICTURE`, `FILE`, … |
| `ssg` | ✅ | Must be `true` (strict). `false` / absent → **not written**. |
| `fileName` | ➖ | Target filename (e.g. `index.html`, `mhamed.jpg`). Fallback: `{code}.html` for text, `{code}.bin` for binary. |
| `folder` | ➖ | Subfolder **inside the current node's output folder**. If absent, the file goes directly in the node folder. |
| `payload` | ✅ (text) | The text content. Used for **all non-binary types**. |
| `file.data` | ✅ (binary) | Base64 data URI (e.g. `data:image/jpeg;base64,...`). Used **only** for `PICTURE` and `FILE`. |

> ⚠️ **Binary vs text:** `PICTURE` and `FILE` are **binary** — they read `file.data`, ignore `payload`, and are **never rewritten** in pass 2. All other types are **text** — they read `payload`, are written as UTF-8, and participate in link rewriting.

### 4. Webhook configuration in Nodify

On the **root node**, set:

| Field | Value |
|-------|-------|
| Trigger URL | `https://<worker-host>/webhook` (→ **Worker**, NOT admin) |
| Trigger Secret | Your `WORKER_SECRET` value |

The webhook payload sent by Nodify looks like:

```json
{
  "event_type": "ssg-node",
  "client_payload": {
    "code": "YOUR_ROOT_NODE_CODE",
    "folder": "site-name",
    "ssg": true,
    "timestamp": "2025-01-01T00:00:00.000Z"
  }
}
```

- `client_payload.code` → root node code (required)
- `client_payload.folder` → site folder name (optional, defaults to `"default"`)

### 5. Link rewriting (how references work)

After generation, the worker **rewrites every text file** to replace:

1. **Full Nodify API file URLs**
   ```
   https://<api>/contents/code/<CODE>/file[?query]
   ```
   → replaced by the **local relative path** of the generated file (e.g. `pictures/mhamed.jpg`).

2. **Raw content codes** (outside API URLs)
   ```
   <CODE>
   ```
   → replaced by the **local relative path** of the generated file.

This means you can write in any payload:

```html
<img src="https://nodify-api.your-domain.com/contents/code/PICTURE-DEV-1794913304849/file?status=PUBLISHED"/>
```

or simply:

```html
<img src="PICTURE-DEV-1794913304849"/>
```

and both will be rewritten to:

```html
<img src="pictures/mhamed.jpg"/>
```

> Only codes present in the site's `mapping` are rewritten. Codes of `ssg: false` contents, or codes of contents not part of the current tree, are **left untouched**.

### 6. Full example

**Root node** `LANDINGPAGE-DEV-0643497554` (`ssg: true`):

```
Contents:
  ✅ HTML-DEV-3480269024  (ssg:true,  fileName:index.html, folder:null)       → index.html
  ✅ HTML-DEV-1092265001  (ssg:true,  fileName:null,       folder:null)       → HTML-DEV-1092265001.html
  ❌ HTML-DEV-9308029478  (ssg:false)                                         → skipped
  ❌ STYLE-DEV-6197530005 (ssg:false)                                         → skipped

Child nodes:
  ✅ BLOG-DEV-0000000001  (ssg:true, folder:blog)                             → blog/
```

**Generated tree** (`SITES_DIR/landingpage/`):

```
landingpage/
├── index.html
├── HTML-DEV-1092265001.html
└── blog/
    └── <contents of BLOG node>
```

**Root node** `SSG_TEST-DEV-1794911122281` (`ssg: true`):

```
Contents:
  ✅ HTML-DEV-1794911188250     (ssg:true,  fileName:index.html,  folder:null)       → index.html
  ✅ PICTURE-DEV-1794913304849  (ssg:true,  fileName:mhamed.jpg,  folder:pictures)   → pictures/mhamed.jpg
  ❌ HTML-DEV-1794911227551     (ssg:false)                                          → skipped
  ❌ HTML-DEV-1794913051716     (ssg:false)                                          → skipped
```

**Generated tree** (`SITES_DIR/ssg_test/`):

```
ssg_test/
├── index.html                          (contains <img src="pictures/mhamed.jpg">)
└── pictures/
    └── mhamed.jpg
```

---

## API Endpoints

All endpoints below are served by the **Worker**. The **Admin** serves `/`, `/api/sites`, and `/api/delete/{name}` and proxies to the worker.

| Method | Endpoint | Service | Description |
|--------|----------|---------|-------------|
| POST | `/webhook` | Worker | Receive webhook and generate a site |
| GET | `/list` | Worker | List all generated sites |
| DELETE | `/delete/{name}` | Worker | Delete a site |
| GET | `/health` | Worker | Health check |
| GET | `/` | Admin | Management UI |
| GET | `/api/sites` | Admin | Proxy to worker `/list` |
| DELETE | `/api/delete/{name}` | Admin | Proxy to worker `/delete/{name}` |

## Access URLs

| Service | URL |
|---------|-----|
| Admin Interface | `http://localhost:5590/` (local) · `https://nodify-ssg-admin.your-domain.com` (prod) |
| Generated Sites | `http://localhost:5580/{site-name}/` (local) · `https://nodify-ssg-sites.your-domain.com/{site-name}/` (prod) |
| Webhook Endpoint | `http://localhost:5500/webhook` (local) · `https://nodify-ssg-worker.your-domain.com/webhook` (prod) |

> **The webhook URL uses the Worker port (`WORKER_PORT`, default 5500) — never the Admin port.** The Admin UI displays this URL for convenience, but the actual endpoint is on the Worker.

---

## Routing / Reverse Proxy

Each service must be exposed on its **own** hostname. Example with three Nginx `server` blocks:

```nginx
# --- Worker: receives Nodify webhooks ---
server {
    listen 80;
    server_name nodify-ssg-worker.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5500;   # WORKER_PORT
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# --- Admin: management UI only ---
server {
    listen 80;
    server_name nodify-ssg-admin.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5590;   # ADMIN_PORT  (NOT the worker)
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# --- Web: serves generated static sites ---
server {
    listen 80;
    server_name nodify-ssg-sites.your-domain.com;

    root /path/to/sites;   # matches SITES_VOLUME
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

> ❌ **Anti-pattern:** a single `server` block with `location / { proxy_pass http://127.0.0.1:5000; }` routes *everything* to the worker, making the admin UI unreachable. Always separate the three services.

If you use **Nginx Proxy Manager** (recommended), create three Proxy Hosts pointing to `worker:5000`, `admin:8080`, and `web:80` respectively.

---

## Project Structure

```
nodify-ssg-worker/
├── docker-compose.yml
├── Dockerfile-Worker
├── Dockerfile-Admin
├── requirements.txt
├── requirements-dev.txt        # pytest, pytest-cov
├── worker.py                   # webhook receiver + site generator
├── admin.py                    # management UI
├── templates/                  # admin templates
│   └── index.html
├── static/                     # admin static assets
│   ├── style.css
│   └── app.js
├── tests/
│   ├── conftest.py
│   ├── test_collect_node.py
│   ├── test_rewrite_site.py
│   └── test_routes.py
├── .env
└── README.md
```

## Admin Interface Features

- 📁 List all generated sites
- 📊 View each site's size
- 🌐 Direct link to view each site
- 🗑 Delete sites
- 🔄 Auto-refresh every 30 seconds

## How It Works (two-pass generation)

1. You publish a node in Nodify (with `ssg: true` and a trigger URL).
2. Nodify sends a webhook to the **Worker** (`POST /webhook`).
3. **Pass 1 — collect:** the worker fetches contents and child nodes recursively:
   - `GET /contents/node/code/{code}?fillValues=true&withFiles=true`
   - `GET /nodes/parent/{code}`
   - Writes text files and binary files, and builds a `mapping[code] = relative_path`.
4. **Pass 2 — rewrite:** every text file is rewritten:
   - API URLs → local paths
   - Raw codes → local paths
5. The **Admin** UI lists the generated sites via `/api/sites` (proxied to the worker's `/list`).
6. The **Web** server serves the generated files.

## SSG Content Rules (summary)

- A node / sub-node / content is processed **only if `ssg is True`** (strict).
- A **node's** `folder` = subfolder under its **parent**. Fallback: node `code`.
- A **content's** `folder` = subfolder under the **current node**. Fallback: node root.
- `fileName` = target filename. Fallback: `{code}.html` (text) or `{code}.bin` (binary).
- `PICTURE` and `FILE` → read `file.data` (base64 data URI), written as binary.
- Other types → read `payload`, written as UTF-8.
- Binary files are **never rewritten**.
- Site folder name = `client_payload.folder` from the webhook (default `"default"`).
- The site is **wiped and regenerated** on each webhook.

## Environment Variables

| Variable | Default | Used by | Description |
|----------|---------|---------|-------------|
| `WORKER_PORT` | 5500 | compose | Host port for the worker |
| `ADMIN_PORT` | 5590 | compose | Host port for the admin UI |
| `WEB_PORT` | 5580 | compose | Host port for the web server |
| `NODIFY_API_URL` | - | worker | Nodify API base URL |
| `WORKER_SECRET` | - | worker | Webhook authentication secret |
| `SITES_DIR` | `/sites` | worker | Container path where sites are written |
| `SITES_VOLUME` | `./sites` | compose | Host path mounted into all 3 services |
| `SITES_URL` | - | admin | Public URL of generated sites |
| `WORKER_URL` | `http://worker:5000` | admin | Internal URL the admin uses to reach the worker |
| `WEBHOOK_URL` | `http://localhost:5500/webhook` | admin | Public URL of the webhook, displayed in the admin UI |

## Development

```bash
pip install -r requirements.txt
export NODIFY_API_URL="https://your-nodify-instance.com"
export WORKER_SECRET="your-secret-key"
export SITES_DIR="./sites"
python worker.py
```

In another terminal:

```bash
export WORKER_URL="http://localhost:5000"
export SITES_URL="http://localhost:5580"
export WEBHOOK_URL="http://localhost:5500/webhook"
python admin.py
```

Serve the generated sites locally:

```bash
python -m http.server 5580 --directory ./sites
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest -v
pytest --cov=worker --cov-report=term-missing
```

## Troubleshooting

### Worker doesn't receive webhooks
- Confirm the Nodify Trigger URL points to the **Worker** host (port `WORKER_PORT`, default 5500), path `/webhook`
- Check that `WORKER_SECRET` matches Nodify's `triggerSecret`
- Check logs: `docker compose logs worker`

### Admin UI unreachable / 404
- Make sure the reverse proxy routes the admin hostname to `ADMIN_PORT` (default 5590), **not** to the worker
- A single `location / { proxy_pass ...:5000; }` block sends admin traffic to the worker by mistake — split into three `server` blocks (see *Routing / Reverse Proxy*)

### The admin UI shows the wrong webhook URL
- The admin UI uses `WEBHOOK_URL` (env var). Make sure it points to the **Worker** (`http://localhost:5500/webhook`), **not** to the admin (`http://localhost:5590/webhook`).
- Set it in `.env`:
  ```env
  WEBHOOK_URL=http://localhost:5500/webhook
  ```
  and recreate the admin container:
  ```bash
  docker compose up -d --force-recreate admin
  ```

### Sites not appearing in admin
- Verify the admin can reach the worker: `docker exec admin curl http://worker:5000/list`
- Check that `SITES_VOLUME` is correctly mounted (worker writes to `/sites`, web serves the same volume)

### Files not generated
- Ensure content has `ssg: true` in Nodify
- Check worker logs for API errors

### Binary images referenced by API URL are not replaced
- Check that the referenced content has `ssg: true` (its code must be in `mapping`)
- Check that the URL matches `https?://<host>/contents/code/<code>/file[?query]`
- Check the generated HTML for `src="<local-path>"`

## License

MIT

## Links

- [Nodify CMS](https://github.com/AZIRARM/nodify)
- [Live Demo](https://nodify.azirar.ovh)
- [Report Issue](https://github.com/AZIRARM/nodify-ssg-worker/issues)
