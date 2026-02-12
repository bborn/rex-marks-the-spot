#!/usr/bin/env python3
"""Tests for TaskYou Board API server.

Run: python3 -m pytest test_server.py -v
  or: python3 test_server.py  (uses unittest)
"""

import json
import os
import subprocess
import sys
import threading
import time
import unittest
from http.server import HTTPServer
from unittest.mock import patch, MagicMock
from urllib.request import urlopen, Request
from urllib.error import HTTPError

# Import the server module
sys.path.insert(0, os.path.dirname(__file__))
import server


SAMPLE_BOARD = {
    "columns": [
        {"status": "backlog", "label": "Backlog", "count": 2, "tasks": [
            {"id": 1, "title": "Task 1", "project": "test", "type": "code", "pinned": False, "age_hint": "1h"},
        ]},
        {"status": "processing", "label": "In Progress", "count": 1, "tasks": [
            {"id": 2, "title": "Task 2", "project": "test", "type": "code", "pinned": True, "age_hint": "5m"},
        ]},
    ]
}

SAMPLE_TASK = {
    "id": 42,
    "title": "Test task",
    "status": "processing",
    "project": "test",
    "type": "code",
    "body": "Task description here",
    "branch": "task/42-test",
    "created_at": "2026-01-01T00:00:00Z",
}

SAMPLE_LIST = [
    {"id": 1, "title": "Task 1", "status": "backlog", "project": "test", "type": "code"},
    {"id": 2, "title": "Task 2", "status": "processing", "project": "test", "type": "code"},
]


def _mock_run_ty(*args, timeout=15):
    """Mock ty CLI calls with canned responses."""
    cmd_args = list(args)
    if "board" in cmd_args:
        return True, json.dumps(SAMPLE_BOARD)
    if "show" in cmd_args:
        return True, json.dumps(SAMPLE_TASK)
    if "list" in cmd_args:
        return True, json.dumps(SAMPLE_LIST)
    return False, "unknown command"


class TestAPI(unittest.TestCase):
    """Integration tests using a real HTTP server with mocked ty calls."""

    @classmethod
    def setUpClass(cls):
        # Clear cache
        server._cache.clear()
        # Patch run_ty
        cls.patcher = patch("server.run_ty", side_effect=_mock_run_ty)
        cls.patcher.start()

        # Start server on a free port
        cls.httpd = HTTPServer(("127.0.0.1", 0), server.TaskYouAPIHandler)
        cls.port = cls.httpd.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.patcher.stop()

    def setUp(self):
        server._cache.clear()

    def _get(self, path):
        req = Request(f"{self.base}{path}")
        with urlopen(req) as resp:
            return resp.status, json.loads(resp.read())

    def _get_raw(self, path):
        req = Request(f"{self.base}{path}")
        with urlopen(req) as resp:
            return resp.status, resp.read().decode(), resp.headers

    # --- Board endpoint ---

    def test_board_returns_columns(self):
        status, data = self._get("/api/taskyou/board")
        self.assertEqual(status, 200)
        self.assertIn("columns", data)
        self.assertEqual(len(data["columns"]), 2)

    def test_board_column_structure(self):
        _, data = self._get("/api/taskyou/board")
        col = data["columns"][0]
        self.assertIn("status", col)
        self.assertIn("label", col)
        self.assertIn("count", col)
        self.assertIn("tasks", col)

    def test_board_task_structure(self):
        _, data = self._get("/api/taskyou/board")
        task = data["columns"][0]["tasks"][0]
        self.assertEqual(task["id"], 1)
        self.assertIn("title", task)

    # --- Task endpoint ---

    def test_task_detail(self):
        status, data = self._get("/api/taskyou/task/42")
        self.assertEqual(status, 200)
        self.assertEqual(data["id"], 42)
        self.assertEqual(data["title"], "Test task")
        self.assertIn("body", data)

    def test_task_invalid_id(self):
        try:
            self._get("/api/taskyou/task/abc")
            self.fail("Expected HTTP error")
        except HTTPError as e:
            self.assertEqual(e.code, 400)

    # --- List endpoint ---

    def test_list_returns_array(self):
        status, data = self._get("/api/taskyou/list")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    # --- Health endpoint ---

    def test_health_ok(self):
        status, data = self._get("/api/taskyou/health")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])

    # --- Root serves HTML ---

    def test_root_serves_html(self):
        status, body, headers = self._get_raw("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        self.assertIn("<!DOCTYPE html>", body)

    # --- 404 ---

    def test_404_returns_endpoints(self):
        try:
            self._get("/nonexistent")
            self.fail("Expected HTTP error")
        except HTTPError as e:
            self.assertEqual(e.code, 404)
            data = json.loads(e.read())
            self.assertIn("endpoints", data)

    # --- Caching ---

    def test_cache_hit(self):
        # First call populates cache
        self._get("/api/taskyou/board")
        # Verify cache is populated
        self.assertTrue(any(k.startswith("board:") for k in server._cache))

    # --- CORS ---

    def test_cors_header_when_set(self):
        old = server.TaskYouAPIHandler.cors_origin
        server.TaskYouAPIHandler.cors_origin = "*"
        try:
            _, _, headers = self._get_raw("/api/taskyou/health")
            self.assertEqual(headers.get("Access-Control-Allow-Origin"), "*")
        finally:
            server.TaskYouAPIHandler.cors_origin = old


class TestRunTy(unittest.TestCase):
    """Unit tests for the run_ty helper."""

    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='{"ok": true}', stderr="")
        ok, output = server.run_ty("list", "--json")
        self.assertTrue(ok)
        self.assertIn("ok", output)

    @patch("subprocess.run")
    def test_nonzero_exit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error msg")
        ok, output = server.run_ty("bad")
        self.assertFalse(ok)
        self.assertIn("error msg", output)

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_missing_binary(self, _):
        ok, output = server.run_ty("list")
        self.assertFalse(ok)
        self.assertIn("not found", output)

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ty", timeout=15))
    def test_timeout(self, _):
        ok, output = server.run_ty("list")
        self.assertFalse(ok)
        self.assertIn("timed out", output)


if __name__ == "__main__":
    unittest.main()
