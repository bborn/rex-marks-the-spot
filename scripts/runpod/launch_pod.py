#!/usr/bin/env python3
"""Launch a RunPod GPU pod with ComfyUI for video generation.

Prerequisites:
    pip install runpod
    export RUNPOD_API_KEY="your_api_key_here"

Usage:
    python scripts/runpod/launch_pod.py              # Launch new pod
    python scripts/runpod/launch_pod.py --gpu a100   # Use A100 instead of 4090
    python scripts/runpod/launch_pod.py --stop        # Stop running pod
    python scripts/runpod/launch_pod.py --start       # Restart stopped pod
    python scripts/runpod/launch_pod.py --status       # Check pod status
    python scripts/runpod/launch_pod.py --terminate    # Terminate pod (destroys data)
"""

import argparse
import json
import os
import sys
import time

try:
    import runpod
except ImportError:
    print("ERROR: runpod package not installed. Run: pip install runpod")
    sys.exit(1)

# GPU configurations (Community Cloud pricing, approximate)
GPU_CONFIGS = {
    "4090": {
        "gpu_type_id": "NVIDIA GeForce RTX 4090",
        "gpu_count": 1,
        "cost_approx": "$0.44/hr",
        "vram": "24 GB",
    },
    "a100-80": {
        "gpu_type_id": "NVIDIA A100 80GB PCIe",
        "gpu_count": 1,
        "cost_approx": "$0.64/hr",
        "vram": "80 GB",
    },
    "a100-sxm": {
        "gpu_type_id": "NVIDIA A100-SXM4-80GB",
        "gpu_count": 1,
        "cost_approx": "$0.74/hr",
        "vram": "80 GB",
    },
    "l40s": {
        "gpu_type_id": "NVIDIA L40S",
        "gpu_count": 1,
        "cost_approx": "$0.44/hr",
        "vram": "48 GB",
    },
    "3090": {
        "gpu_type_id": "NVIDIA GeForce RTX 3090",
        "gpu_count": 1,
        "cost_approx": "$0.22/hr",
        "vram": "24 GB",
    },
}

# RunPod ComfyUI template - official pre-built image
COMFYUI_TEMPLATE_ID = "rvfwevhz1h"  # RunPod's official ComfyUI template

# Pod name for easy identification
POD_NAME = "rex-comfyui-video"

# Volume size for model storage (persists across pod restarts)
VOLUME_SIZE_GB = 100

# Container disk (ephemeral, for OS/runtime)
CONTAINER_DISK_GB = 20


def get_api_key():
    key = os.environ.get("RUNPOD_API_KEY")
    if not key:
        key_file = os.path.expanduser("~/.runpod_api_key")
        if os.path.exists(key_file):
            with open(key_file) as f:
                key = f.read().strip()
    if not key:
        print("ERROR: RUNPOD_API_KEY not set.")
        print("  export RUNPOD_API_KEY='your_key_here'")
        print("  OR save it to ~/.runpod_api_key")
        sys.exit(1)
    return key


def find_pod():
    """Find our existing pod by name."""
    pods = runpod.get_pods()
    for pod in pods:
        if pod.get("name") == POD_NAME:
            return pod
    return None


def get_gpu_availability():
    """Check GPU availability on Community Cloud."""
    try:
        gpus = runpod.get_gpus()
        available = {}
        for gpu in gpus:
            gpu_id = gpu.get("id", "")
            for key, config in GPU_CONFIGS.items():
                if config["gpu_type_id"] == gpu_id:
                    available[key] = {
                        "available": gpu.get("communityCloud", {}).get("stockStatus", "unavailable"),
                        "price": gpu.get("communityPrice", "N/A"),
                        "secure_price": gpu.get("securePrice", "N/A"),
                    }
        return available
    except Exception as e:
        print(f"Warning: Could not check GPU availability: {e}")
        return {}


def launch_pod(gpu_type="4090"):
    """Launch a new ComfyUI pod."""
    config = GPU_CONFIGS.get(gpu_type)
    if not config:
        print(f"Unknown GPU type: {gpu_type}")
        print(f"Available: {', '.join(GPU_CONFIGS.keys())}")
        sys.exit(1)

    existing = find_pod()
    if existing:
        status = existing.get("desiredStatus", "unknown")
        pod_id = existing["id"]
        print(f"Pod '{POD_NAME}' already exists (id={pod_id}, status={status})")
        if status == "EXITED":
            print("Pod is stopped. Use --start to resume it.")
        else:
            print_pod_info(existing)
        return existing

    print(f"Launching pod with {config['gpu_type_id']} ({config['vram']} VRAM)")
    print(f"  Estimated cost: {config['cost_approx']} (Community Cloud)")
    print(f"  Volume: {VOLUME_SIZE_GB} GB persistent storage")
    print()

    # Check availability first
    avail = get_gpu_availability()
    if gpu_type in avail:
        stock = avail[gpu_type].get("available", "unknown")
        if stock == "unavailable" or stock == "Low":
            print(f"Warning: {config['gpu_type_id']} stock is '{stock}'")
            print("You may want to try a different GPU type.")

    try:
        pod = runpod.create_pod(
            name=POD_NAME,
            image_name="runpod/comfyui:3.0.4",  # Official ComfyUI image
            gpu_type_id=config["gpu_type_id"],
            gpu_count=config["gpu_count"],
            volume_in_gb=VOLUME_SIZE_GB,
            container_disk_in_gb=CONTAINER_DISK_GB,
            cloud_type="COMMUNITY",
            ports="8188/http,22/tcp",
            volume_mount_path="/workspace",
            # Environment variables for the pod
            env={
                "JUPYTER_PASSWORD": "comfyui",
            },
        )
    except Exception as e:
        error_msg = str(e)
        if "no available" in error_msg.lower() or "stock" in error_msg.lower():
            print(f"GPU type {config['gpu_type_id']} is not available right now.")
            print("Try a different GPU type:")
            for key, cfg in GPU_CONFIGS.items():
                print(f"  --gpu {key}: {cfg['gpu_type_id']} ({cfg['vram']}, ~{cfg['cost_approx']})")
            sys.exit(1)
        raise

    pod_id = pod.get("id")
    print(f"Pod created! ID: {pod_id}")
    print("Waiting for pod to start...")

    # Wait for pod to be ready
    for i in range(60):
        time.sleep(5)
        pods = runpod.get_pods()
        for p in pods:
            if p.get("id") == pod_id:
                status = p.get("desiredStatus", "unknown")
                runtime = p.get("runtime", {})
                if runtime and runtime.get("uptimeInSeconds"):
                    print(f"\nPod is running! (uptime: {runtime['uptimeInSeconds']}s)")
                    print_pod_info(p)
                    return p
                print(f"  Status: {status}...", end="\r")
        if i % 6 == 0 and i > 0:
            print(f"  Still waiting ({i * 5}s)...")

    print("\nTimeout waiting for pod. Check RunPod dashboard.")
    return pod


def print_pod_info(pod):
    """Print connection info for a pod."""
    pod_id = pod["id"]
    runtime = pod.get("runtime", {}) or {}
    ports = runtime.get("ports", []) or []

    print(f"\n{'='*60}")
    print(f"  Pod: {pod.get('name')} (id: {pod_id})")
    print(f"  GPU: {pod.get('machine', {}).get('gpuDisplayName', 'N/A')}")
    print(f"  Status: {pod.get('desiredStatus', 'unknown')}")
    print(f"{'='*60}")

    # Find the HTTP port for ComfyUI
    comfy_url = None
    ssh_cmd = None
    for port in ports:
        if port.get("privatePort") == 8188:
            comfy_url = f"https://{pod_id}-8188.proxy.runpod.net"
        if port.get("privatePort") == 22:
            ip = port.get("ip")
            pub_port = port.get("publicPort")
            if ip and pub_port:
                ssh_cmd = f"ssh root@{ip} -p {pub_port} -i ~/.ssh/id_ed25519"

    if comfy_url:
        print(f"\n  ComfyUI: {comfy_url}")
    else:
        print(f"\n  ComfyUI: https://{pod_id}-8188.proxy.runpod.net (proxy URL)")

    if ssh_cmd:
        print(f"  SSH:     {ssh_cmd}")
    else:
        print(f"  SSH:     ssh into pod via RunPod dashboard or:")
        print(f"           runpodctl ssh {pod_id}")

    print(f"\n  RunPod:  https://www.runpod.io/console/pods/{pod_id}")
    print(f"{'='*60}")

    # Save pod info to a file for other scripts
    info = {
        "pod_id": pod_id,
        "name": pod.get("name"),
        "gpu": pod.get("machine", {}).get("gpuDisplayName"),
        "comfyui_url": comfy_url or f"https://{pod_id}-8188.proxy.runpod.net",
        "status": pod.get("desiredStatus"),
    }
    info_path = os.path.join(os.path.dirname(__file__), "pod_info.json")
    with open(info_path, "w") as f:
        json.dump(info, f, indent=2)
    print(f"\n  Pod info saved to: {info_path}")


def stop_pod():
    """Stop (but don't terminate) the pod to save money."""
    pod = find_pod()
    if not pod:
        print(f"No pod named '{POD_NAME}' found.")
        return
    pod_id = pod["id"]
    print(f"Stopping pod {pod_id}...")
    runpod.stop_pod(pod_id)
    print("Pod stopped. Volume data is preserved.")
    print("  Billing: You're only charged for volume storage (~$0.10/GB/month)")
    print(f"  Restart: python {__file__} --start")


def start_pod():
    """Restart a stopped pod."""
    pod = find_pod()
    if not pod:
        print(f"No pod named '{POD_NAME}' found.")
        return
    pod_id = pod["id"]
    status = pod.get("desiredStatus")
    if status == "RUNNING":
        print("Pod is already running!")
        print_pod_info(pod)
        return

    print(f"Starting pod {pod_id}...")
    runpod.resume_pod(pod_id, gpu_count=1)
    print("Pod starting... wait 30-60s for ComfyUI to be ready.")

    # Wait and get updated info
    for i in range(24):
        time.sleep(5)
        pods = runpod.get_pods()
        for p in pods:
            if p.get("id") == pod_id:
                runtime = p.get("runtime", {})
                if runtime and runtime.get("uptimeInSeconds"):
                    print_pod_info(p)
                    return
    print("Pod is starting. Check RunPod dashboard for status.")


def terminate_pod():
    """Terminate the pod completely (destroys all data including volume)."""
    pod = find_pod()
    if not pod:
        print(f"No pod named '{POD_NAME}' found.")
        return
    pod_id = pod["id"]
    print(f"WARNING: This will TERMINATE pod {pod_id} and DELETE all data!")
    print("This action cannot be undone.")
    confirm = input("Type 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        return
    runpod.terminate_pod(pod_id)
    print("Pod terminated.")


def show_status():
    """Show current pod status."""
    pod = find_pod()
    if not pod:
        print(f"No pod named '{POD_NAME}' found.")
        print("\nTo create one: python scripts/runpod/launch_pod.py")
        return
    print_pod_info(pod)

    # Show cost estimate
    runtime = pod.get("runtime", {}) or {}
    uptime = runtime.get("uptimeInSeconds", 0)
    if uptime > 0:
        hours = uptime / 3600
        gpu = pod.get("machine", {}).get("gpuDisplayName", "")
        cost_per_hr = 0.44 if "4090" in gpu else 0.64
        print(f"\n  Uptime: {hours:.1f} hours")
        print(f"  Est. cost so far: ${hours * cost_per_hr:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Manage RunPod ComfyUI pod")
    parser.add_argument("--gpu", default="4090", choices=GPU_CONFIGS.keys(),
                        help="GPU type (default: 4090)")
    parser.add_argument("--stop", action="store_true", help="Stop the pod")
    parser.add_argument("--start", action="store_true", help="Start a stopped pod")
    parser.add_argument("--terminate", action="store_true", help="Terminate pod (destroys data)")
    parser.add_argument("--status", action="store_true", help="Show pod status")
    parser.add_argument("--availability", action="store_true", help="Check GPU availability")
    args = parser.parse_args()

    api_key = get_api_key()
    runpod.api_key = api_key

    if args.stop:
        stop_pod()
    elif args.start:
        start_pod()
    elif args.terminate:
        terminate_pod()
    elif args.status:
        show_status()
    elif args.availability:
        avail = get_gpu_availability()
        print("GPU Availability (Community Cloud):")
        for gpu_key, info in avail.items():
            config = GPU_CONFIGS[gpu_key]
            print(f"  {gpu_key}: {config['gpu_type_id']} ({config['vram']})")
            print(f"    Stock: {info.get('available', 'unknown')}")
            print(f"    Price: ${info.get('price', 'N/A')}/hr")
    else:
        launch_pod(args.gpu)


if __name__ == "__main__":
    main()
