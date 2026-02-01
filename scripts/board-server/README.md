# TaskYou Board API Server

Real-time API server for the TaskYou board widget. Provides live task board data that can be polled every 2-3 seconds for real-time updates.

## Quick Start

```bash
# Run the setup script (installs Node.js, dependencies, and systemd service)
chmod +x setup.sh
./setup.sh
```

## Manual Setup

```bash
# Install Node.js (if not already installed)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.nvm/nvm.sh
nvm install --lts

# Install dependencies
npm install

# Run the server
node server.js
```

## API Endpoints

### GET /api/board
Returns the current board state (equivalent to `ty board --json`).

**Response:**
```json
{
  "columns": [
    {
      "status": "backlog",
      "label": "Backlog",
      "count": 5,
      "tasks": [
        {
          "id": 1,
          "title": "Task title",
          "project": "personal",
          "type": "code",
          "pinned": false,
          "age_hint": "created 2h 30m"
        }
      ]
    }
  ],
  "updated_at": "2026-02-01T12:00:00.000Z",
  "server_version": "1.0.0"
}
```

### GET /api/task/:id
Returns detailed information for a specific task.

### GET /api/task/:id/output
Returns the recent output for a specific task (equivalent to `ty output :id`).

**Query Parameters:**
- `lines` (optional): Number of lines to return (default: 20, max: 100)

**Response:**
```json
{
  "task_id": 21,
  "lines": 20,
  "output": "Agent output here...",
  "updated_at": "2026-02-01T12:00:00.000Z"
}
```

### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-01T12:00:00.000Z",
  "ty_available": true,
  "uptime": 3600
}
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3080` | Port to listen on |
| `TY_PATH` | `/home/rex/.local/bin/ty` | Path to the `ty` binary |

## Reverse Proxy Configuration

### Caddy

Add to your Caddyfile:

```
api.rexmarksthespot.com {
    reverse_proxy localhost:3080
}
```

### Nginx

```nginx
server {
    server_name api.rexmarksthespot.com;

    location / {
        proxy_pass http://localhost:3080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Service Management

```bash
# Check status
sudo systemctl status taskyou-board-server

# View logs
sudo journalctl -u taskyou-board-server -f

# Restart
sudo systemctl restart taskyou-board-server

# Stop
sudo systemctl stop taskyou-board-server
```

## Development

```bash
# Run with auto-reload (Node.js 18+)
npm run dev

# Or manually
node --watch server.js
```
