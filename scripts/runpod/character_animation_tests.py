#!/usr/bin/env python3
"""Character animation tests using approved turnaround sheets.

Runs video generation tests on ComfyUI via SSH tunnel to RunPod pod.
Tests: Wan 2.1 T2V, Capybara T2V with character ref, Capybara TI2I,
       Capybara TV2V (storyboard animation).

Usage:
    # Set up SSH tunnel first:
    # ssh -f -N -L 18188:localhost:8188 -i ~/.ssh/id_ed25519 root@<ip> -p <port>
    python scripts/runpod/character_animation_tests.py
    python scripts/runpod/character_animation_tests.py --test mia_t2v
    python scripts/runpod/character_animation_tests.py --test all
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
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "test_outputs"
COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://localhost:18188")

# Test results tracker
test_results = []


def log(msg):
    """Log with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def check_health():
    """Verify ComfyUI is reachable."""
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=10) as resp:
            data = json.loads(resp.read())
            ver = data["system"]["comfyui_version"]
            gpu = data["devices"][0]["name"] if data.get("devices") else "unknown"
            vram = data["devices"][0]["vram_total"] / 1e9 if data.get("devices") else 0
            log(f"ComfyUI v{ver} | GPU: {gpu} | VRAM: {vram:.0f} GB")
            return True
    except Exception as e:
        log(f"ERROR: ComfyUI not reachable at {COMFYUI_URL}: {e}")
        return False


def queue_prompt(workflow):
    """Queue a workflow and return prompt_id."""
    client_id = str(uuid.uuid4())
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        return result.get("prompt_id")


def wait_completion(prompt_id, timeout=900):
    """Wait for prompt completion, return result or None."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as resp:
                history = json.loads(resp.read())
                if prompt_id in history:
                    data = history[prompt_id]
                    status = data.get("status", {})
                    if status.get("completed") or status.get("status_str") == "success":
                        return data
                    if status.get("status_str") == "error":
                        msgs = status.get("messages", [])
                        log(f"  ERROR: Workflow failed: {msgs}")
                        return None
        except Exception:
            pass
        elapsed = int(time.time() - start)
        print(f"  Waiting... ({elapsed}s / {timeout}s)", end="\r", flush=True)
        time.sleep(5)
    print()
    log(f"  TIMEOUT after {timeout}s")
    return None


def download_outputs(result, test_name):
    """Download output files from completed workflow."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    outputs = result.get("outputs", {})
    downloaded = []

    for node_id, node_output in outputs.items():
        # Videos
        for vid in node_output.get("gifs", []):
            filename = vid.get("filename")
            subfolder = vid.get("subfolder", "")
            vid_type = vid.get("type", "output")
            if filename:
                vid_url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type={vid_type}"
                local_path = OUTPUT_DIR / f"{test_name}_{filename}"
                try:
                    urllib.request.urlretrieve(vid_url, str(local_path))
                    size_mb = local_path.stat().st_size / 1e6
                    log(f"  Downloaded: {local_path.name} ({size_mb:.1f} MB)")
                    downloaded.append(str(local_path))
                except Exception as e:
                    log(f"  Download failed for {filename}: {e}")

        # Images
        for img in node_output.get("images", []):
            filename = img.get("filename")
            subfolder = img.get("subfolder", "")
            img_type = img.get("type", "output")
            if filename:
                img_url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                local_path = OUTPUT_DIR / f"{test_name}_{filename}"
                try:
                    urllib.request.urlretrieve(img_url, str(local_path))
                    size_mb = local_path.stat().st_size / 1e6
                    log(f"  Downloaded: {local_path.name} ({size_mb:.1f} MB)")
                    downloaded.append(str(local_path))
                except Exception as e:
                    log(f"  Download failed for {filename}: {e}")

    return downloaded


def upload_to_r2(files):
    """Upload files to R2 at comfyui-tests/character-tests/."""
    for f in files:
        try:
            subprocess.run(
                ["rclone", "copy", f, "r2:rex-assets/comfyui-tests/character-tests/"],
                check=True, capture_output=True, text=True,
            )
            fname = os.path.basename(f)
            url = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/character-tests/{fname}"
            log(f"  Uploaded to R2: {url}")
        except subprocess.CalledProcessError as e:
            log(f"  R2 upload error: {e.stderr}")
        except FileNotFoundError:
            log("  rclone not available")
            break


def run_test(name, workflow, timeout=900):
    """Run a single test: queue, wait, download, upload."""
    log(f"")
    log(f"{'='*60}")
    log(f"TEST: {name}")
    log(f"{'='*60}")

    start = time.time()
    try:
        prompt_id = queue_prompt(workflow)
    except Exception as e:
        log(f"  FAILED to queue: {e}")
        test_results.append({"name": name, "status": "QUEUE_FAIL", "error": str(e)})
        return []

    log(f"  Queued: {prompt_id}")
    log(f"  Generating (timeout={timeout}s)...")

    result = wait_completion(prompt_id, timeout=timeout)
    elapsed = time.time() - start

    if not result:
        log(f"  FAILED after {elapsed:.0f}s")
        test_results.append({"name": name, "status": "FAIL", "time_s": elapsed})
        return []

    print()
    log(f"  Completed in {elapsed:.0f}s")

    files = download_outputs(result, name)
    if files:
        upload_to_r2(files)
        test_results.append({
            "name": name, "status": "PASS", "time_s": elapsed,
            "files": [os.path.basename(f) for f in files]
        })
    else:
        log(f"  No output files found")
        test_results.append({"name": name, "status": "NO_OUTPUT", "time_s": elapsed})

    return files


# ============================================================
# TEST 1: Mia T2V with Wan 2.1 (character-descriptive prompt)
# ============================================================
def test_mia_wan_t2v():
    """Wan 2.1 T2V: Mia walking through jungle, Pixar style."""
    workflow = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "wan2.1_t2v_1.3B_bf16.safetensors",
                "weight_dtype": "default"
            }
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "type": "wan"
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "A young girl with a wavy ponytail wearing a purple shirt and pink skirt walks through a magical jungle with giant glowing mushrooms and luminescent ferns. Pixar 3D animation style, smooth character animation, vibrant saturated colors, soft volumetric lighting, cute cartoon character.",
                "clip": ["2", 0]
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "blurry, low quality, distorted, ugly, watermark, text, static, realistic, photorealistic",
                "clip": ["2", 0]
            }
        },
        "5": {
            "class_type": "EmptyHunyuanLatentVideo",
            "inputs": {
                "width": 480,
                "height": 320,
                "length": 33,
                "batch_size": 1
            }
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "seed": 123,
                "steps": 20,
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            }
        },
        "7": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "wan_2.1_vae.safetensors"}
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["6", 0],
                "vae": ["7", 0]
            }
        },
        "9": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["8", 0],
                "frame_rate": 16,
                "loop_count": 0,
                "filename_prefix": "mia_wan_t2v",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": False
            }
        }
    }
    return run_test("mia_wan_t2v", workflow, timeout=300)


# ============================================================
# TEST 2: Mia Capybara T2V with character reference image
# ============================================================
def test_mia_capybara_t2v():
    """Capybara T2V: Mia with character reference, jungle walk."""
    workflow = {
        "1": {
            "class_type": "CapybaraLoadPipeline",
            "inputs": {
                "model_path": "/workspace/capybara_model",
                "transformer_version": "capybara_v01",
                "dtype": "bfloat16",
                "enable_offloading": True,
                "flow_shift": 5.0,
                "quantize": "none"
            }
        },
        "2": {
            "class_type": "CapybaraGenerate",
            "inputs": {
                "pipe": ["1", 0],
                "prompt": "A young girl with a wavy ponytail wearing a purple shirt and pink skirt walks through a magical jungle with giant glowing mushrooms. Pixar 3D animation style, smooth character animation, vibrant colors, soft lighting, cute cartoon character design.",
                "negative_prompt": "blurry, low quality, distorted, ugly, watermark, realistic, photorealistic",
                "task_type": "t2v",
                "resolution": "480p",
                "aspect_ratio": "16:9",
                "num_frames": 33,
                "num_inference_steps": 30,
                "guidance_scale": 6.0,
                "seed": 123
            }
        },
        "3": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["2", 0],
                "frame_rate": 16,
                "loop_count": 0,
                "filename_prefix": "mia_capybara_t2v",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": False
            }
        }
    }
    return run_test("mia_capybara_t2v", workflow, timeout=600)


# ============================================================
# TEST 3: Mia Capybara TI2I (image-to-image animation)
# ============================================================
def test_mia_capybara_ti2i():
    """Capybara TI2I: Animate Mia turnaround - waving/walking."""
    workflow = {
        "10": {
            "class_type": "LoadImage",
            "inputs": {
                "image": "mia_turnaround_APPROVED_ALT.png"
            }
        },
        "1": {
            "class_type": "CapybaraLoadPipeline",
            "inputs": {
                "model_path": "/workspace/capybara_model",
                "transformer_version": "capybara_v01",
                "dtype": "bfloat16",
                "enable_offloading": True,
                "flow_shift": 5.0,
                "quantize": "none"
            }
        },
        "2": {
            "class_type": "CapybaraGenerate",
            "inputs": {
                "pipe": ["1", 0],
                "prompt": "A young cartoon girl with a wavy ponytail starts waving hello and then walks forward with a bounce in her step. Pixar 3D animation style, smooth animation, cute character, colorful background.",
                "negative_prompt": "blurry, low quality, distorted, ugly, realistic",
                "task_type": "ti2i",
                "resolution": "480p",
                "aspect_ratio": "16:9",
                "num_frames": 33,
                "num_inference_steps": 30,
                "guidance_scale": 6.0,
                "seed": 456,
                "reference": ["10", 0]
            }
        },
        "3": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["2", 0],
                "frame_rate": 16,
                "loop_count": 0,
                "filename_prefix": "mia_capybara_ti2i",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": False
            }
        }
    }
    return run_test("mia_capybara_ti2i", workflow, timeout=600)


# ============================================================
# TEST 4: Gabe & Nina date night - Capybara T2V
# ============================================================
def test_gabe_nina_t2v():
    """Capybara T2V: Gabe and Nina walking arm in arm."""
    workflow = {
        "1": {
            "class_type": "CapybaraLoadPipeline",
            "inputs": {
                "model_path": "/workspace/capybara_model",
                "transformer_version": "capybara_v01",
                "dtype": "bfloat16",
                "enable_offloading": True,
                "flow_shift": 5.0,
                "quantize": "none"
            }
        },
        "2": {
            "class_type": "CapybaraGenerate",
            "inputs": {
                "pipe": ["1", 0],
                "prompt": "A stocky man with glasses wearing a black tuxedo and a beautiful woman in a black cocktail dress walk arm in arm down an elegant hallway. Warm golden lighting, Pixar 3D animation style, smooth character animation, romantic atmosphere, cute cartoon characters.",
                "negative_prompt": "blurry, low quality, distorted, ugly, realistic, photorealistic",
                "task_type": "t2v",
                "resolution": "480p",
                "aspect_ratio": "16:9",
                "num_frames": 33,
                "num_inference_steps": 30,
                "guidance_scale": 6.0,
                "seed": 789
            }
        },
        "3": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["2", 0],
                "frame_rate": 16,
                "loop_count": 0,
                "filename_prefix": "gabe_nina_capybara_t2v",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": False
            }
        }
    }
    return run_test("gabe_nina_capybara_t2v", workflow, timeout=600)


# ============================================================
# TEST 5: Gabe & Nina Wan T2V (smaller model, faster)
# ============================================================
def test_gabe_nina_wan_t2v():
    """Wan 2.1 T2V: Gabe and Nina date night walk."""
    workflow = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "wan2.1_t2v_1.3B_bf16.safetensors",
                "weight_dtype": "default"
            }
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "type": "wan"
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "A stocky cartoon man with glasses wearing a black tuxedo and a beautiful cartoon woman in a black cocktail dress walk arm in arm down a grand elegant hallway. Warm golden lighting, chandeliers, Pixar 3D animation style, smooth character movement, romantic atmosphere.",
                "clip": ["2", 0]
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "blurry, low quality, distorted, ugly, watermark, text, static, realistic",
                "clip": ["2", 0]
            }
        },
        "5": {
            "class_type": "EmptyHunyuanLatentVideo",
            "inputs": {
                "width": 480,
                "height": 320,
                "length": 33,
                "batch_size": 1
            }
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "seed": 789,
                "steps": 20,
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            }
        },
        "7": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "wan_2.1_vae.safetensors"}
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["6", 0],
                "vae": ["7", 0]
            }
        },
        "9": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["8", 0],
                "frame_rate": 16,
                "loop_count": 0,
                "filename_prefix": "gabe_nina_wan_t2v",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": False
            }
        }
    }
    return run_test("gabe_nina_wan_t2v", workflow, timeout=300)


# ============================================================
# TEST 6: Storyboard panel to video - Capybara TV2V
# ============================================================
def test_storyboard_tv2v():
    """Capybara TV2V: Animate storyboard panel (scene-01-panel-01)."""
    # First we need to create a short video from the storyboard image
    # Since TV2V needs video input, we use ti2i instead (image to video)
    workflow = {
        "10": {
            "class_type": "LoadImage",
            "inputs": {
                "image": "scene-01-panel-01.png"
            }
        },
        "1": {
            "class_type": "CapybaraLoadPipeline",
            "inputs": {
                "model_path": "/workspace/capybara_model",
                "transformer_version": "capybara_v01",
                "dtype": "bfloat16",
                "enable_offloading": True,
                "flow_shift": 5.0,
                "quantize": "none"
            }
        },
        "2": {
            "class_type": "CapybaraGenerate",
            "inputs": {
                "pipe": ["1", 0],
                "prompt": "Animate this living room scene. Camera slowly pans across the cozy family living room with warm evening lighting. Pixar 3D animation style, subtle ambient motion, soft shadows, cozy atmosphere.",
                "negative_prompt": "blurry, low quality, distorted, ugly, realistic, photorealistic",
                "task_type": "ti2i",
                "resolution": "480p",
                "aspect_ratio": "16:9",
                "num_frames": 33,
                "num_inference_steps": 30,
                "guidance_scale": 6.0,
                "seed": 321,
                "reference": ["10", 0]
            }
        },
        "3": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["2", 0],
                "frame_rate": 16,
                "loop_count": 0,
                "filename_prefix": "storyboard_capybara_ti2i",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": False
            }
        }
    }
    return run_test("storyboard_capybara_ti2i", workflow, timeout=600)


# ============================================================
# TEST 7: Mia TV2V - Animate turnaround front view
# ============================================================
def test_mia_capybara_tv2v():
    """Capybara TV2V: Animate Mia turnaround front view video."""
    workflow = {
        "1": {
            "class_type": "CapybaraLoadPipeline",
            "inputs": {
                "model_path": "/workspace/capybara_model",
                "transformer_version": "capybara_v01",
                "dtype": "bfloat16",
                "enable_offloading": True,
                "flow_shift": 5.0,
                "quantize": "none"
            }
        },
        "2": {
            "class_type": "CapybaraGenerate",
            "inputs": {
                "pipe": ["1", 0],
                "prompt": "Make the young cartoon girl wave hello and then start walking forward with a bounce in her step. Add a colorful magical forest background. Pixar 3D animation style, smooth character animation, vibrant colors.",
                "negative_prompt": "blurry, low quality, distorted, ugly, realistic, static, still image",
                "task_type": "tv2v",
                "resolution": "480p",
                "aspect_ratio": "16:9",
                "num_frames": 33,
                "num_inference_steps": 30,
                "guidance_scale": 6.0,
                "seed": 555,
                "reference_video_path": "/workspace/ComfyUI/output/mia_front_static.mp4"
            }
        },
        "3": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["2", 0],
                "frame_rate": 16,
                "loop_count": 0,
                "filename_prefix": "mia_capybara_tv2v",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": False
            }
        }
    }
    return run_test("mia_capybara_tv2v", workflow, timeout=600)


# ============================================================
# TEST 8: Storyboard TV2V - Animate storyboard panel
# ============================================================
def test_storyboard_capybara_tv2v():
    """Capybara TV2V: Animate storyboard panel into video."""
    workflow = {
        "1": {
            "class_type": "CapybaraLoadPipeline",
            "inputs": {
                "model_path": "/workspace/capybara_model",
                "transformer_version": "capybara_v01",
                "dtype": "bfloat16",
                "enable_offloading": True,
                "flow_shift": 5.0,
                "quantize": "none"
            }
        },
        "2": {
            "class_type": "CapybaraGenerate",
            "inputs": {
                "pipe": ["1", 0],
                "prompt": "Animate this living room scene into a Pixar-style 3D animation. Camera slowly pans right revealing more of the cozy family home. Warm evening lighting, soft shadows, subtle ambient motion like curtains swaying and light flickering.",
                "negative_prompt": "blurry, low quality, distorted, ugly, realistic, photorealistic",
                "task_type": "tv2v",
                "resolution": "480p",
                "aspect_ratio": "16:9",
                "num_frames": 33,
                "num_inference_steps": 30,
                "guidance_scale": 6.0,
                "seed": 999,
                "reference_video_path": "/workspace/ComfyUI/output/storyboard_static.mp4"
            }
        },
        "3": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["2", 0],
                "frame_rate": 16,
                "loop_count": 0,
                "filename_prefix": "storyboard_capybara_tv2v",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": False
            }
        }
    }
    return run_test("storyboard_capybara_tv2v", workflow, timeout=600)


# ============================================================
# All available tests
# ============================================================
ALL_TESTS = {
    "mia_wan_t2v": test_mia_wan_t2v,
    "mia_capybara_t2v": test_mia_capybara_t2v,
    "mia_capybara_ti2i": test_mia_capybara_ti2i,
    "mia_capybara_tv2v": test_mia_capybara_tv2v,
    "gabe_nina_t2v": test_gabe_nina_t2v,
    "gabe_nina_wan_t2v": test_gabe_nina_wan_t2v,
    "storyboard_ti2i": test_storyboard_tv2v,
    "storyboard_tv2v": test_storyboard_capybara_tv2v,
}


def main():
    global COMFYUI_URL

    parser = argparse.ArgumentParser(description="Character animation tests")
    parser.add_argument("--test", default="all",
                        choices=list(ALL_TESTS.keys()) + ["all"],
                        help="Which test to run (default: all)")
    parser.add_argument("--url", help=f"ComfyUI URL (default: {COMFYUI_URL})")
    args = parser.parse_args()

    if args.url:
        COMFYUI_URL = args.url

    log(f"ComfyUI URL: {COMFYUI_URL}")

    if not check_health():
        log("ComfyUI not reachable. Set up SSH tunnel first.")
        sys.exit(1)

    if args.test == "all":
        tests_to_run = list(ALL_TESTS.items())
    else:
        tests_to_run = [(args.test, ALL_TESTS[args.test])]

    all_files = []
    for name, test_fn in tests_to_run:
        files = test_fn()
        all_files.extend(files)

    # Print summary
    log("")
    log("=" * 60)
    log("TEST SUMMARY")
    log("=" * 60)
    for r in test_results:
        status = r["status"]
        name = r["name"]
        time_s = r.get("time_s", 0)
        files = r.get("files", [])
        symbol = "PASS" if status == "PASS" else "FAIL"
        log(f"  [{symbol}] {name} ({time_s:.0f}s) {', '.join(files)}")

    passed = sum(1 for r in test_results if r["status"] == "PASS")
    total = len(test_results)
    log(f"\n  {passed}/{total} tests passed")
    log(f"  Output dir: {OUTPUT_DIR}")

    if all_files:
        log(f"\n  R2 URLs:")
        for f in all_files:
            fname = os.path.basename(f)
            log(f"    https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/character-tests/{fname}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
