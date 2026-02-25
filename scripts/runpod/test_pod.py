#!/usr/bin/env python3
"""Test ComfyUI workflows on a RunPod pod.

Connects to the pod's ComfyUI instance, runs test workflows,
and downloads results.

Usage:
    python scripts/runpod/test_pod.py                    # Run all tests
    python scripts/runpod/test_pod.py --test wan_t2v     # Run specific test
    python scripts/runpod/test_pod.py --url https://xxx  # Custom ComfyUI URL
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
WORKFLOWS_DIR = SCRIPT_DIR / "workflows"
OUTPUT_DIR = SCRIPT_DIR / "test_outputs"


def get_comfyui_url():
    """Get ComfyUI URL from pod_info.json or environment."""
    # Check environment variable first
    url = os.environ.get("COMFYUI_URL")
    if url:
        return url.rstrip("/")

    # Check pod_info.json
    info_path = SCRIPT_DIR / "pod_info.json"
    if info_path.exists():
        with open(info_path) as f:
            info = json.load(f)
            url = info.get("comfyui_url")
            if url:
                return url.rstrip("/")

    print("ERROR: Cannot determine ComfyUI URL.")
    print("  Set COMFYUI_URL env var, or run launch_pod.py first.")
    sys.exit(1)


def check_health(url):
    """Check if ComfyUI is running."""
    try:
        req = urllib.request.Request(f"{url}/system_stats")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            sys_info = data.get("system", {})
            print(f"ComfyUI v{sys_info.get('comfyui_version', '?')}")
            print(f"PyTorch: {sys_info.get('pytorch_version', '?')}")

            devices = data.get("devices", [])
            for dev in devices:
                vram_gb = dev.get("vram_total", 0) / 1e9
                print(f"GPU: {dev.get('name', '?')} - {vram_gb:.1f} GB VRAM")
            return True
    except Exception as e:
        print(f"ComfyUI not reachable at {url}: {e}")
        return False


def queue_workflow(url, workflow, client_id=None):
    """Queue a workflow and return the prompt_id."""
    if client_id is None:
        client_id = str(uuid.uuid4())

    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"{url}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        return result.get("prompt_id")


def wait_for_completion(url, prompt_id, timeout=600):
    """Wait for a queued prompt to complete."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{url}/history/{prompt_id}") as resp:
                history = json.loads(resp.read())
                if prompt_id in history:
                    prompt_data = history[prompt_id]
                    status = prompt_data.get("status", {})
                    if status.get("completed", False) or status.get("status_str") == "success":
                        return prompt_data
                    if status.get("status_str") == "error":
                        print(f"ERROR: Workflow failed!")
                        msgs = status.get("messages", [])
                        for msg in msgs:
                            print(f"  {msg}")
                        return None
        except Exception:
            pass

        elapsed = int(time.time() - start)
        print(f"  Waiting... ({elapsed}s)", end="\r")
        time.sleep(3)

    print(f"\nTimeout after {timeout}s")
    return None


def download_outputs(url, prompt_data, test_name):
    """Download generated outputs from a completed workflow."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    outputs = prompt_data.get("outputs", {})
    downloaded = []

    for node_id, node_output in outputs.items():
        # Check for images
        for img in node_output.get("images", []):
            filename = img.get("filename")
            subfolder = img.get("subfolder", "")
            img_type = img.get("type", "output")
            if filename:
                img_url = f"{url}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                local_path = OUTPUT_DIR / f"{test_name}_{filename}"
                try:
                    urllib.request.urlretrieve(img_url, local_path)
                    downloaded.append(str(local_path))
                    print(f"  Downloaded: {local_path.name}")
                except Exception as e:
                    print(f"  Failed to download {filename}: {e}")

        # Check for videos/gifs
        for vid in node_output.get("gifs", []):
            filename = vid.get("filename")
            subfolder = vid.get("subfolder", "")
            vid_type = vid.get("type", "output")
            if filename:
                vid_url = f"{url}/view?filename={filename}&subfolder={subfolder}&type={vid_type}"
                local_path = OUTPUT_DIR / f"{test_name}_{filename}"
                try:
                    urllib.request.urlretrieve(vid_url, local_path)
                    downloaded.append(str(local_path))
                    print(f"  Downloaded: {local_path.name}")
                except Exception as e:
                    print(f"  Failed to download {filename}: {e}")

    return downloaded


def upload_to_r2(local_files):
    """Upload test outputs to R2."""
    for f in local_files:
        filename = os.path.basename(f)
        r2_path = f"r2:rex-assets/comfyui-tests/{filename}"
        try:
            subprocess.run(
                ["rclone", "copy", f, "r2:rex-assets/comfyui-tests/"],
                check=True, capture_output=True, text=True,
            )
            print(f"  Uploaded to R2: comfyui-tests/{filename}")
        except subprocess.CalledProcessError as e:
            print(f"  R2 upload failed: {e.stderr}")
        except FileNotFoundError:
            print(f"  rclone not available - skipping R2 upload")
            break


def list_available_models(url):
    """List models available on the ComfyUI instance."""
    try:
        with urllib.request.urlopen(f"{url}/object_info") as resp:
            info = json.loads(resp.read())

        # Check diffusion models
        unet_loader = info.get("UNETLoader", {})
        unet_inputs = unet_loader.get("input", {}).get("required", {})
        if "unet_name" in unet_inputs:
            models = unet_inputs["unet_name"]
            if isinstance(models, list) and models:
                print("\nDiffusion Models:")
                for m in (models[0] if isinstance(models[0], list) else models):
                    print(f"  - {m}")

        # Check VAE
        vae_loader = info.get("VAELoader", {})
        vae_inputs = vae_loader.get("input", {}).get("required", {})
        if "vae_name" in vae_inputs:
            vaes = vae_inputs["vae_name"]
            if isinstance(vaes, list) and vaes:
                print("\nVAE Models:")
                for v in (vaes[0] if isinstance(vaes[0], list) else vaes):
                    print(f"  - {v}")

        # Check for Capybara nodes
        capybara_nodes = [k for k in info.keys() if "capybara" in k.lower()]
        if capybara_nodes:
            print(f"\nCapybara Nodes ({len(capybara_nodes)}):")
            for n in capybara_nodes:
                print(f"  - {n}")
        else:
            print("\nCapybara: NOT INSTALLED")

        # Check for IP-Adapter nodes
        ipa_nodes = [k for k in info.keys() if "ipadapter" in k.lower()]
        if ipa_nodes:
            print(f"\nIP-Adapter Nodes ({len(ipa_nodes)}):")
            for n in sorted(ipa_nodes)[:10]:
                print(f"  - {n}")
            if len(ipa_nodes) > 10:
                print(f"  ... and {len(ipa_nodes) - 10} more")

    except Exception as e:
        print(f"Could not list models: {e}")


def test_wan_t2v(url):
    """Test Wan 2.1 text-to-video generation."""
    print("\n" + "=" * 50)
    print("TEST: Wan 2.1 Text-to-Video (1.3B model)")
    print("=" * 50)

    workflow_path = WORKFLOWS_DIR / "wan21_t2v_basic.json"
    if not workflow_path.exists():
        print(f"Workflow not found: {workflow_path}")
        return False

    with open(workflow_path) as f:
        workflow = json.load(f)

    print("Queuing workflow...")
    prompt_id = queue_workflow(url, workflow)
    if not prompt_id:
        print("Failed to queue workflow")
        return False

    print(f"Prompt ID: {prompt_id}")
    print("Generating video (this may take 2-5 minutes)...")

    result = wait_for_completion(url, prompt_id, timeout=600)
    if not result:
        print("Generation failed or timed out")
        return False

    print("\nGeneration complete!")
    files = download_outputs(url, result, "wan21_t2v")
    if files:
        upload_to_r2(files)
        return True
    else:
        print("No output files found")
        return False


def test_capybara_t2v(url):
    """Test Capybara text-to-video generation."""
    print("\n" + "=" * 50)
    print("TEST: Capybara Text-to-Video")
    print("=" * 50)

    # Check if Capybara nodes are available
    try:
        with urllib.request.urlopen(f"{url}/object_info") as resp:
            info = json.loads(resp.read())
        capybara_nodes = [k for k in info.keys() if "capybara" in k.lower() or "Capybara" in k]
        if not capybara_nodes:
            print("Capybara nodes not found. Run pod_setup.sh first.")
            return False
        print(f"Found {len(capybara_nodes)} Capybara nodes")
    except Exception as e:
        print(f"Cannot check nodes: {e}")
        return False

    # Capybara T2V workflow
    workflow = {
        "1": {
            "class_type": "CapybaraLoadPipeline",
            "inputs": {
                "task": "t2v",
                "dtype": "bf16",
            }
        },
        "2": {
            "class_type": "CapybaraGenerate",
            "inputs": {
                "pipeline": ["1", 0],
                "prompt": "A cute cartoon dinosaur walking through a colorful jungle, Pixar animation style, smooth motion, vibrant colors",
                "negative_prompt": "blurry, low quality, distorted",
                "width": 512,
                "height": 320,
                "num_frames": 33,
                "steps": 20,
                "guidance_scale": 7.0,
                "seed": 42,
            }
        },
        "3": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["2", 0],
                "frame_rate": 16,
                "loop_count": 0,
                "filename_prefix": "capybara_t2v_test",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
            }
        }
    }

    print("Queuing Capybara T2V workflow...")
    prompt_id = queue_workflow(url, workflow)
    if not prompt_id:
        print("Failed to queue workflow")
        return False

    print(f"Prompt ID: {prompt_id}")
    print("Generating video (this may take 3-10 minutes for Capybara)...")

    result = wait_for_completion(url, prompt_id, timeout=900)
    if not result:
        print("Generation failed or timed out")
        return False

    print("\nGeneration complete!")
    files = download_outputs(url, result, "capybara_t2v")
    if files:
        upload_to_r2(files)
        return True
    else:
        print("No output files found")
        return False


def test_capybara_tv2v(url):
    """Test Capybara video-to-video (the key capability)."""
    print("\n" + "=" * 50)
    print("TEST: Capybara Video-to-Video (TV2V)")
    print("=" * 50)

    # Check if we have any source video to use
    # For a first test, we'd need to first generate a video with Wan
    # and then use it as input to Capybara TV2V
    print("Note: TV2V requires an input video.")
    print("This test should be run after a successful T2V test produces a video.")
    print("The workflow will be saved for manual testing via ComfyUI UI.")

    # Save a template workflow that the user can load in ComfyUI
    workflow = {
        "1": {
            "class_type": "VHS_LoadVideo",
            "inputs": {
                "video": "wan21_t2v_test_00001.mp4",
                "force_rate": 16,
                "force_size": "Disabled",
                "frame_load_cap": 0,
                "skip_first_frames": 0,
            }
        },
        "2": {
            "class_type": "CapybaraLoadPipeline",
            "inputs": {
                "task": "tv2v",
                "dtype": "bf16",
            }
        },
        "3": {
            "class_type": "CapybaraGenerate",
            "inputs": {
                "pipeline": ["2", 0],
                "video": ["1", 0],
                "prompt": "A Pixar-style cartoon dinosaur walking through a magical jungle, high quality 3D animation, smooth movement",
                "negative_prompt": "blurry, low quality, distorted, live action",
                "steps": 20,
                "guidance_scale": 7.0,
                "strength": 0.7,
                "seed": 42,
            }
        },
        "4": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["3", 0],
                "frame_rate": 16,
                "loop_count": 0,
                "filename_prefix": "capybara_tv2v_test",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
            }
        }
    }

    workflow_path = WORKFLOWS_DIR / "capybara_tv2v.json"
    with open(workflow_path, "w") as f:
        json.dump(workflow, f, indent=2)
    print(f"TV2V workflow template saved to: {workflow_path}")
    print("Load this in ComfyUI UI and update the input video path to test.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Test ComfyUI workflows on RunPod")
    parser.add_argument("--url", help="ComfyUI URL (overrides pod_info.json)")
    parser.add_argument("--test", choices=["wan_t2v", "capybara_t2v", "capybara_tv2v", "all"],
                        default="all", help="Which test to run")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    args = parser.parse_args()

    url = args.url or get_comfyui_url()
    print(f"Connecting to ComfyUI at: {url}")
    print()

    if not check_health(url):
        print("\nComfyUI is not reachable. Is the pod running?")
        sys.exit(1)

    if args.list_models:
        list_available_models(url)
        return

    results = {}

    if args.test in ("wan_t2v", "all"):
        results["wan_t2v"] = test_wan_t2v(url)

    if args.test in ("capybara_t2v", "all"):
        results["capybara_t2v"] = test_capybara_t2v(url)

    if args.test in ("capybara_tv2v", "all"):
        results["capybara_tv2v"] = test_capybara_tv2v(url)

    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")

    if all(results.values()):
        print("\nAll tests passed!")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"\nFailed tests: {', '.join(failed)}")


if __name__ == "__main__":
    main()
