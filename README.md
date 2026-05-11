# Nodify SSG Worker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-2496ED.svg)](https://www.docker.com/)

A lightweight webhook receiver that listens to Nodify CMS events and generates static sites automatically.

## Overview

Nodify SSG Worker is a companion service for [Nodify Headless CMS](https://github.com/AZIRARM/nodify). It receives webhook notifications when you publish content and generates a complete static website from your nodes and content.

## Architecture

Three separate services on three ports:

| Service | Port (Internal) | Description |
|---------|-----------------|-------------|
| Worker | 5000 | Receives webhooks, generates static files |
| Admin | 8080 | Web interface to manage sites |
| Web | 80 | Serves generated sites |

## Quick Start

### Using Docker Compose

```bash
git clone https://github.com/AZIRARM/nodify-ssg-worker.git
cd nodify-ssg-worker
docker compose up -d
```

### Configuration

Create a `.env` file:

```env
# Port for the worker service (receives webhooks)
WORKER_PORT=5500

# Port for the admin web interface (manage sites)
ADMIN_PORT=5590

# Port for the web server (serves generated static sites)
WEB_PORT=5580

# URL of your Nodify API instance
NODIFY_API_URL=https://nodify-api.azirar.ovh

# Secret key for authenticating incoming webhook requests (must match triggerSecret in Nodify)
WORKER_SECRET=your-secret-key-here

# Host path where generated static sites are stored
SITES_VOLUME=/dockers/nodify-ssg-worker/sites

# Public URL where generated sites are accessible
SITES_URL=https://nodify-sites.azirar.ovh
```

### Using custom ports

```bash
WORKER_PORT=5001 ADMIN_PORT=8081 WEB_PORT=3001 docker compose up -d
```

## Webhook Configuration in Nodify

In your Nodify node settings:

| Field | Value |
|-------|-------|
| Trigger URL | `https://your-domain:5500/webhook` |
| Trigger Secret | Your `WORKER_SECRET` value |
| Folder | Site name (e.g., `my-blog`) |

### Webhook Payload Format

```json
{
  "event_type": "ssg-node",
  "client_payload": {
    "code": "YOUR_NODE_CODE",
    "folder": "site-name",
    "ssg": true,
    "timestamp": "2025-01-01T00:00:00.000Z"
  }
}
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook` | Receive webhook and generate site |
| GET | `/list` | List all generated sites |
| DELETE | `/delete/{name}` | Delete a site |
| GET | `/health` | Health check |

## Access URLs

| Service | URL |
|---------|-----|
| Admin Interface | `https://nodify-ssg-admin.your-domain.com` |
| Generated Sites | `https://nodify-ssg-sites.your-domain.com/{site-name}/` |
| Webhook Endpoint | `https://nodify-ssg-worker.your-domain.com/webhook` |

## Project Structure

```
nodify-ssg-worker/
├── docker-compose.yml
├── Dockerfile-Worker
├── Dockerfile-Admin
├── requirements.txt
├── worker.py
├── admin.py
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── app.js
├── .env
└── README.md
```

## Admin Interface Features

- 📁 List all generated sites
- 📊 View site size
- 🌐 Direct link to view each site
- 🗑 Delete sites
- 🔄 Auto-refresh every 30 seconds

## How It Works

1. You publish a node in Nodify (with SSG enabled)
2. Nodify sends a webhook to the worker
3. Worker fetches all content from Nodify API (`/contents/node/code/{code}?fillValues=true&withFiles=true`)
4. Worker recursively processes nodes and their children
5. Files are saved to the sites directory with custom folder and filename support
6. Admin interface shows generated sites via `/list` API
7. Web server serves static files on the web port

## SSG Content Rules

- A node or content is only generated if `ssg: true`
- Files are saved with custom `fileName` if provided, otherwise `{code}.{type}`
- Images and files (PICTURE, FILE types) are decoded from base64 and saved as binary
- Sub-nodes create subfolders recursively
- The root folder is determined by the `folder` field in the webhook payload

## Requirements

- Docker & Docker Compose
- Nodify CMS instance (v1.0+)
- Nginx Proxy Manager (or similar) for SSL termination (recommended)

## Development

```bash
# Run without Docker
pip install -r requirements.txt
export NODIFY_API_URL="https://your-nodify-instance.com"
export WORKER_SECRET="your-secret-key"
python worker.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKER_PORT` | 5500 | External port for worker service |
| `ADMIN_PORT` | 5590 | External port for admin interface |
| `WEB_PORT` | 5580 | External port for web server |
| `NODIFY_API_URL` | - | URL of your Nodify API instance |
| `WORKER_SECRET` | - | Secret for webhook authentication |
| `SITES_VOLUME` | ./sites | Host path for generated sites |
| `SITES_URL` | - | Public URL for generated sites |

## Troubleshooting

### Worker doesn't receive webhooks
- Check that NPM forwards HTTPS to HTTP correctly
- Verify `WORKER_SECRET` matches Nodify's triggerSecret
- Check logs: `docker compose logs worker`

### Sites not appearing in admin
- Verify admin can reach worker: `docker exec admin curl http://worker:5000/list`
- Check that `SITES_VOLUME` is correctly mounted

### Files not generated
- Ensure content has `ssg: true` in Nodify
- Check worker logs for API errors

## License

MIT

## Links

- [Nodify CMS](https://github.com/AZIRARM/nodify)
- [Live Demo](https://nodify.azirar.ovh)
- [Report Issue](https://github.com/AZIRARM/nodify-ssg-worker/issues)
