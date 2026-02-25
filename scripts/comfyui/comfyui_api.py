#!/usr/bin/env python3
"""ComfyUI API helper for the Rex Marks the Spot production pipeline.

Provides utilities to interact with ComfyUI programmatically:
- Queue workflows
- Check system status
- Download generated outputs

Usage:
    from scripts.comfyui.comfyui_api import ComfyUIClient

    client = ComfyUIClient()
    print(client.get_system_stats())
"""

import json
import urllib.request
import urllib.parse
import uuid
from pathlib import Path

COMFYUI_URL = "http://localhost:8188"


class ComfyUIClient:
    def __init__(self, server_url=COMFYUI_URL):
        self.server_url = server_url.rstrip("/")

    def get_system_stats(self):
        """Get ComfyUI system stats (GPU, RAM, version info)."""
        url = f"{self.server_url}/system_stats"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())

    def get_object_info(self):
        """Get all available node types."""
        url = f"{self.server_url}/object_info"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())

    def list_models(self, model_type="checkpoints"):
        """List available models of a given type."""
        info = self.get_object_info()
        # Find loader nodes that expose model lists
        loaders = {
            "checkpoints": "CheckpointLoaderSimple",
            "diffusion_models": "UNETLoader",
            "vae": "VAELoader",
            "text_encoders": "DualCLIPLoader",
        }
        loader = loaders.get(model_type)
        if loader and loader in info:
            inputs = info[loader].get("input", {}).get("required", {})
            for key, val in inputs.items():
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], list):
                    return val[0]
        return []

    def queue_prompt(self, workflow: dict, client_id: str = None):
        """Queue a workflow for execution.

        Args:
            workflow: ComfyUI workflow dict (API format)
            client_id: Optional client ID for tracking

        Returns:
            dict with prompt_id
        """
        if client_id is None:
            client_id = str(uuid.uuid4())

        payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
        req = urllib.request.Request(
            f"{self.server_url}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())

    def get_queue(self):
        """Get current queue status."""
        url = f"{self.server_url}/queue"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())

    def get_history(self, prompt_id=None):
        """Get execution history."""
        url = f"{self.server_url}/history"
        if prompt_id:
            url += f"/{prompt_id}"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())

    def is_healthy(self):
        """Check if ComfyUI is running and responsive."""
        try:
            stats = self.get_system_stats()
            return stats.get("system", {}).get("comfyui_version") is not None
        except Exception:
            return False


if __name__ == "__main__":
    client = ComfyUIClient()

    if client.is_healthy():
        stats = client.get_system_stats()
        sys_info = stats["system"]
        print(f"ComfyUI v{sys_info['comfyui_version']}")
        print(f"PyTorch: {sys_info['pytorch_version']}")
        print(f"Python: {sys_info['python_version']}")
        print(f"RAM: {sys_info['ram_total'] / 1e9:.1f} GB total, {sys_info['ram_free'] / 1e9:.1f} GB free")

        devices = stats.get("devices", [])
        for dev in devices:
            print(f"Device: {dev['name']} ({dev['type']}) - VRAM: {dev['vram_total'] / 1e9:.1f} GB")

        # List available models
        for model_type in ["diffusion_models", "vae"]:
            models = client.list_models(model_type)
            if models:
                print(f"\n{model_type}:")
                for m in models:
                    print(f"  - {m}")
    else:
        print("ComfyUI is not running or not accessible at", COMFYUI_URL)
