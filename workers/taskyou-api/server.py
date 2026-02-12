#!/usr/bin/env python3
"""TaskYou Board API - lightweight HTTP wrapper around `ty` CLI commands.

Zero dependencies beyond Python 3.7+ stdlib. Exposes TaskYou board data as
JSON for embedding in HTML dashboards, status pages, etc.

Usage:
    python3 server.py                    # localhost:8099
    python3 server.py --port 9000        # custom port
    python3 server.py --host 0.0.0.0     # listen on all interfaces
    python3 server.py --cors '*'         # allow all origins
"""

import argparse
import json
import os
import subprocess
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_TTL = 30  # seconds
TY_BIN = os.environ.get("TY_BIN", "ty")
BOARD_LIMIT = int(os.environ.get("BOARD_LIMIT", "20"))
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "")

# In-memory cache: {key: (timestamp, data)}
_cache: dict[str, tuple[float, object]] = {}


def cached(key: str, ttl: int = CACHE_TTL):
    """Simple TTL cache decorator for parameterized calls."""
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < ttl:
        return entry[1]
    return None


def cache_set(key: str, data: object):
    _cache[key] = (time.time(), data)


# ---------------------------------------------------------------------------
# ty command wrappers
# ---------------------------------------------------------------------------

def run_ty(*args: str, timeout: int = 15) -> tuple[bool, str]:
    """Run a ty command and return (success, stdout)."""
    cmd = [TY_BIN] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return False, result.stderr.strip() or f"ty exited with code {result.returncode}"
        return True, result.stdout
    except FileNotFoundError:
        return False, f"ty binary not found at '{TY_BIN}'"
    except subprocess.TimeoutExpired:
        return False, "ty command timed out"


def get_board(limit: int = BOARD_LIMIT) -> tuple[bool, object]:
    """Get the Kanban board as parsed JSON."""
    cache_key = f"board:{limit}"
    hit = cached(cache_key)
    if hit is not None:
        return True, hit

    ok, output = run_ty("board", "--json", "--limit", str(limit))
    if not ok:
        return False, {"error": output}

    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        return False, {"error": f"Failed to parse ty output: {e}"}

    cache_set(cache_key, data)
    return True, data


def get_task(task_id: int) -> tuple[bool, object]:
    """Get a single task's details as parsed JSON."""
    cache_key = f"task:{task_id}"
    hit = cached(cache_key)
    if hit is not None:
        return True, hit

    ok, output = run_ty("show", str(task_id), "--json")
    if not ok:
        return False, {"error": output}

    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        return False, {"error": f"Failed to parse ty output: {e}"}

    cache_set(cache_key, data)
    return True, data


def get_list(status: str | None = None, limit: int = 50) -> tuple[bool, object]:
    """Get a filtered task list as parsed JSON."""
    cache_key = f"list:{status}:{limit}"
    hit = cached(cache_key)
    if hit is not None:
        return True, hit

    args = ["list", "--json", "--limit", str(limit)]
    if status:
        args += ["--status", status]

    ok, output = run_ty(*args)
    if not ok:
        return False, {"error": output}

    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        return False, {"error": f"Failed to parse ty output: {e}"}

    cache_set(cache_key, data)
    return True, data


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent


class TaskYouAPIHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for the TaskYou API."""

    cors_origin = CORS_ORIGIN

    def send_json(self, data: object, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if self.cors_origin:
            self.send_header("Access-Control-Allow-Origin", self.cors_origin)
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, filepath: Path):
        if not filepath.is_file():
            self.send_json({"error": "Not found"}, 404)
            return
        body = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        if self.cors_origin:
            self.send_header("Access-Control-Allow-Origin", self.cors_origin)
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)

        # --- API routes ---

        if path == "/api/taskyou/board":
            limit = int(qs.get("limit", [str(BOARD_LIMIT)])[0])
            ok, data = get_board(limit)
            self.send_json(data, 200 if ok else 500)
            return

        if path.startswith("/api/taskyou/task/"):
            try:
                task_id = int(path.split("/")[-1])
            except ValueError:
                self.send_json({"error": "Invalid task ID"}, 400)
                return
            ok, data = get_task(task_id)
            status_code = 200 if ok else (404 if "not found" in str(data).lower() else 500)
            self.send_json(data, status_code)
            return

        if path == "/api/taskyou/list":
            status = qs.get("status", [None])[0]
            limit = int(qs.get("limit", ["50"])[0])
            ok, data = get_list(status, limit)
            self.send_json(data, 200 if ok else 500)
            return

        if path == "/api/taskyou/health":
            ok, _ = run_ty("list", "--limit", "1", "--json")
            self.send_json({"ok": ok}, 200 if ok else 503)
            return

        # --- Static files ---

        if path in ("", "/"):
            self.send_html(STATIC_DIR / "example.html")
            return

        # Fallback
        self.send_json({"error": "Not found", "endpoints": [
            "/api/taskyou/board",
            "/api/taskyou/task/<id>",
            "/api/taskyou/list",
            "/api/taskyou/health",
            "/",
        ]}, 404)

    def log_message(self, format, *args):
        """Quieter logging - one line per request."""
        sys.stderr.write(f"[taskyou-api] {self.address_string()} {format % args}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global CORS_ORIGIN, BOARD_LIMIT

    parser = argparse.ArgumentParser(description="TaskYou Board API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8099, help="Listen port (default: 8099)")
    parser.add_argument("--cors", default=CORS_ORIGIN, help="CORS Allow-Origin header value")
    parser.add_argument("--limit", type=int, default=BOARD_LIMIT, help="Default board task limit per column")
    args = parser.parse_args()

    # Apply CLI args to module-level config
    CORS_ORIGIN = args.cors
    BOARD_LIMIT = args.limit
    TaskYouAPIHandler.cors_origin = args.cors

    server = HTTPServer((args.host, args.port), TaskYouAPIHandler)
    print(f"TaskYou API listening on http://{args.host}:{args.port}")
    print(f"  Board:  http://{args.host}:{args.port}/api/taskyou/board")
    print(f"  Task:   http://{args.host}:{args.port}/api/taskyou/task/<id>")
    print(f"  List:   http://{args.host}:{args.port}/api/taskyou/list")
    print(f"  Health: http://{args.host}:{args.port}/api/taskyou/health")
    print(f"  Widget: http://{args.host}:{args.port}/")
    print(f"  CORS:   {args.cors or 'disabled'}")
    print(f"  Cache:  {CACHE_TTL}s TTL")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
