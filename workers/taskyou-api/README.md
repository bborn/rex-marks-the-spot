# TaskYou Board API

Lightweight HTTP API that wraps the `ty` CLI to expose TaskYou board data as JSON. Zero external dependencies -- uses Python 3.7+ stdlib only.

## Quick Start

```bash
python3 server.py
# => http://127.0.0.1:8099
```

Open `http://localhost:8099` in a browser to see the live board widget.

## Options

```
--host HOST    Bind address (default: 127.0.0.1)
--port PORT    Listen port (default: 8099)
--cors ORIGIN  Access-Control-Allow-Origin value (e.g. '*')
--limit N      Default max tasks per board column (default: 20)
```

Environment variables: `TY_BIN`, `BOARD_LIMIT`, `CORS_ORIGIN`.

## API Endpoints

### GET /api/taskyou/board

Full Kanban board with columns and tasks.

| Param   | Default | Description                     |
|---------|---------|---------------------------------|
| `limit` | 20      | Max tasks shown per column      |

### GET /api/taskyou/task/:id

Details for a single task (title, status, description, branch, etc).

### GET /api/taskyou/list

Flat task list with optional filters.

| Param    | Default | Description                          |
|----------|---------|--------------------------------------|
| `status` | all     | Filter: backlog, queued, processing, blocked, done |
| `limit`  | 50      | Max tasks returned                   |

### GET /api/taskyou/health

Returns `{"ok": true}` if `ty` is reachable.

## Caching

Responses are cached in-memory for 30 seconds to avoid hammering the `ty` CLI on rapid refreshes.

## CORS

Disabled by default. To allow cross-origin requests:

```bash
python3 server.py --cors '*'              # allow all origins
python3 server.py --cors 'https://mysite' # specific origin
```

## Run as a Service

```bash
sudo cp systemd/taskyou-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now taskyou-api
```

Check status: `sudo systemctl status taskyou-api`

## Embedding the Widget

The included `example.html` renders a live Kanban board that auto-refreshes every 30 seconds. To embed it elsewhere, set the API base URL:

```html
<script>
  window.TASKYOU_API_BASE = 'http://your-server:8099';
</script>
```

## Security Notes

- Read-only: no write operations exposed
- Bind to `127.0.0.1` by default (localhost only)
- Use `--host 0.0.0.0` only on trusted networks or behind a reverse proxy
- No authentication -- intended for internal/team use
- Consider a reverse proxy (nginx/caddy) for TLS and auth if exposing publicly
