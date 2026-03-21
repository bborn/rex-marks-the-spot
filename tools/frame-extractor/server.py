#!/usr/bin/env python3
"""
Frame Extractor Server

A minimal HTTP server that extracts the last frame from a video URL
using ffmpeg and uploads it to R2 via rclone.

Usage:
    python3 server.py [--port 8788] [--host 0.0.0.0]

Endpoints:
    POST /extract-last-frame
    Body: { "video_url": "https://...", "output_path": "storyboards/v3/scene-01/panel-end.png" }
    Returns: { "frame_url": "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/..." }

    GET /health
    Returns: { "status": "ok" }
"""

import json
import os
import subprocess
import tempfile
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

R2_PUBLIC_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev"
R2_BUCKET = "r2:rex-assets"

# Simple shared secret for auth (set via env var)
AUTH_TOKEN = os.environ.get("FRAME_EXTRACTOR_TOKEN", "")


class FrameExtractorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok"})
        else:
            self._respond(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/extract-last-frame":
            self._respond(404, {"error": "not found"})
            return

        # Check auth
        if AUTH_TOKEN:
            auth = self.headers.get("Authorization", "")
            if auth != f"Bearer {AUTH_TOKEN}":
                self._respond(401, {"error": "unauthorized"})
                return

        # Parse body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "invalid JSON"})
            return

        video_url = data.get("video_url")
        output_path = data.get("output_path")

        if not video_url or not output_path:
            self._respond(400, {"error": "video_url and output_path required"})
            return

        try:
            frame_url = extract_and_upload(video_url, output_path)
            self._respond(200, {"frame_url": frame_url})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[frame-extractor] {args[0]} {args[1]} {args[2]}")


def extract_and_upload(video_url: str, output_path: str) -> str:
    """Download video, extract last frame with ffmpeg, upload to R2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "video.mp4")
        frame_path = os.path.join(tmpdir, "last_frame.png")

        # Download video
        print(f"[frame-extractor] Downloading video: {video_url}")
        urllib.request.urlretrieve(video_url, video_path)

        # Extract last frame using ffmpeg
        print(f"[frame-extractor] Extracting last frame...")
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-sseof", "-0.1",
                "-i", video_path,
                "-frames:v", "1",
                "-update", "1",
                frame_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        if not os.path.exists(frame_path):
            raise RuntimeError("ffmpeg produced no output frame")

        # Upload to R2 via rclone
        r2_dest = f"{R2_BUCKET}/{output_path}"
        print(f"[frame-extractor] Uploading to {r2_dest}")
        result = subprocess.run(
            ["rclone", "copyto", frame_path, r2_dest],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(f"rclone upload failed: {result.stderr}")

        frame_url = f"{R2_PUBLIC_URL}/{output_path}"
        print(f"[frame-extractor] Done: {frame_url}")
        return frame_url


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Frame Extractor Server")
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    print(f"[frame-extractor] Starting on {args.host}:{args.port}")
    server = HTTPServer((args.host, args.port), FrameExtractorHandler)
    server.serve_forever()
