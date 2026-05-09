# Nodify SSG Worker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-2496ED.svg)](https://www.docker.com/)

A lightweight webhook receiver that listens to Nodify CMS events and generates static sites automatically.

## Overview

Nodify SSG Worker is a companion service for [Nodify Headless CMS](https://github.com/AZIRARM/nodify). It receives webhook notifications when you publish content and generates a complete static website from your nodes and content.

## Architecture

Three separate services on three ports:

| Service | Port | Description |
|---------|------|-------------|
| Worker | 5000 | Receives webhooks, generates static files |
| Admin | 8080 | Web interface to manage sites |
| Web | 3000 | Serves generated sites |

## Quick Start

### Using Docker Compose

```bash
git clone https://github.com/AZIRARM/nodify-ssg-worker.git
cd nodify-ssg-worker
docker-compose up -d
```

### Configuration

Create a `.env` file:

```env
# Ports
WORKER_PORT=5000
ADMIN_PORT=8080
WEB_PORT=3000

# Nodify API URL
NODIFY_API_URL=https://your-nodify-instance.com
```

### Using custom ports

```bash
WORKER_PORT=5001 ADMIN_PORT=8081 WEB_PORT=3001 docker-compose up -d
```

## Webhook Configuration in Nodify

In your Nodify node settings:

| Field | Value |
|-------|-------|
| Trigger URL | `http://your-server:5000/webhook` |
| Trigger Secret | (optional) |
| Folder | Site name (e.g., `my-blog`) |

### Webhook Payload Format

```json
{
  "event_type": "ssg-node",
  "client_payload": {
    "code": "YOUR_NODE_CODE",
    "folder": "site-name"
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
| Admin Interface | `http://localhost:8080` |
| Generated Sites | `http://localhost:3000/{site-name}/` |
| Webhook Endpoint | `http://localhost:5000/webhook` |

## Project Structure

```
nodify-ssg-worker/
├── docker-compose.yml
├── Dockerfile.worker
├── Dockerfile.admin
├── requirements.txt
├── worker.py
├── admin.py
├── templates/
│   └── index.html
├── .env
└── README.md
```

## Admin Interface Features

- 📁 List all generated sites
- 📊 View site size
- 🌐 Direct link to view each site
- 🗑 Delete sites
- 🔄 Auto-refresh

## How It Works

1. You publish a node in Nodify (with SSG enabled)
2. Nodify sends a webhook to the worker
3. Worker fetches all content from Nodify API
4. Worker recursively processes nodes and their children
5. Files are saved to the sites directory
6. Admin interface shows generated sites
7. Nginx serves static files on the web port

## Requirements

- Docker & Docker Compose
- Nodify CMS instance (v1.0+)

## Development

```bash
# Run without Docker
pip install -r requirements.txt
export NODIFY_API_URL="https://your-nodify-instance.com"
python worker.py
```

## License

MIT

## Links

- [Nodify CMS](https://github.com/AZIRARM/nodify)
- [Live Demo](https://nodify.azirar.ovh)
- [Report Issue](https://github.com/AZIRARM/nodify-ssg-worker/issues)
