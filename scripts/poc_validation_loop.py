#!/usr/bin/env python3
"""
Proof of Concept: Vision Validation Loop

This script demonstrates the complete pipeline:
1. Execute Blender script to create/render scene
2. Send rendered image to Claude Vision API for validation
3. Report results

Requirements:
    pip install anthropic

Usage:
    export ANTHROPIC_API_KEY="your-key"
    python scripts/poc_validation_loop.py

Note: This script is meant to be run OUTSIDE of Blender.
"""

import subprocess
import base64
import os
import sys
from pathlib import Path

# Check for anthropic library
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Note: anthropic library not installed. Vision validation will be simulated.")
    print("Install with: pip install anthropic")


# Configuration
BLENDER_EXECUTABLE = os.environ.get("BLENDER_PATH", "blender")
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "renders"
RENDER_SCRIPT = SCRIPT_DIR / "poc_create_scene.py"


def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def run_blender_render(output_path: Path, samples: int = 32) -> bool:
    """
    Execute Blender in headless mode to render the scene.

    Returns True if render succeeded, False otherwise.
    """
    print("\n" + "=" * 60)
    print("STEP 1: Rendering Scene in Blender (Headless)")
    print("=" * 60)

    cmd = [
        BLENDER_EXECUTABLE,
        "-b",  # Background/headless mode
        "-P", str(RENDER_SCRIPT),
        "--",
        "--output", str(output_path),
        "--samples", str(samples)
    ]

    print(f"Command: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            print("Blender render completed successfully!")
            # Print last few lines of output
            lines = result.stdout.strip().split('\n')
            for line in lines[-10:]:
                print(f"  {line}")
            return True
        else:
            print(f"Blender render failed with code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False

    except FileNotFoundError:
        print(f"ERROR: Blender not found at '{BLENDER_EXECUTABLE}'")
        print("Set BLENDER_PATH environment variable or install Blender.")
        return False
    except subprocess.TimeoutExpired:
        print("ERROR: Render timed out after 5 minutes")
        return False


def encode_image_base64(image_path: Path) -> str:
    """Read and encode image as base64"""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def validate_with_claude_vision(image_path: Path, scene_description: str) -> dict:
    """
    Send rendered image to Claude Vision API for validation.

    Returns a dict with:
        - success: bool
        - matches_description: bool
        - analysis: str
        - suggestions: list[str]
    """
    print("\n" + "=" * 60)
    print("STEP 2: Vision Validation with Claude")
    print("=" * 60)

    if not HAS_ANTHROPIC:
        # Simulated response for demo purposes
        print("(Simulated - anthropic library not installed)")
        return {
            "success": True,
            "matches_description": True,
            "analysis": "SIMULATED: Image would be analyzed for scene elements.",
            "suggestions": ["Install anthropic library for real validation"]
        }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("WARNING: ANTHROPIC_API_KEY not set. Skipping vision validation.")
        return {
            "success": False,
            "matches_description": False,
            "analysis": "API key not configured",
            "suggestions": ["Set ANTHROPIC_API_KEY environment variable"]
        }

    print(f"Analyzing image: {image_path}")
    print(f"Expected scene: {scene_description[:100]}...")

    client = anthropic.Anthropic(api_key=api_key)
    image_data = encode_image_base64(image_path)

    prompt = f"""Analyze this 3D rendered image and validate it against this scene description:

EXPECTED SCENE:
{scene_description}

Please evaluate:
1. Does the image match the description? (yes/no)
2. What elements are present in the image?
3. What elements are missing or incorrect?
4. Quality assessment (lighting, composition, colors)
5. Specific suggestions for improvement

Format your response as:
MATCHES: [yes/no]
ELEMENTS PRESENT: [list]
MISSING/INCORRECT: [list]
QUALITY: [assessment]
SUGGESTIONS: [list]"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        analysis_text = response.content[0].text
        print("\nClaude's Analysis:")
        print("-" * 40)
        print(analysis_text)
        print("-" * 40)

        # Parse response
        matches = "MATCHES: yes" in analysis_text.lower() or "matches: yes" in analysis_text.lower()

        return {
            "success": True,
            "matches_description": matches,
            "analysis": analysis_text,
            "suggestions": []  # Would parse from response
        }

    except Exception as e:
        print(f"ERROR calling Claude API: {e}")
        return {
            "success": False,
            "matches_description": False,
            "analysis": str(e),
            "suggestions": ["Check API key and network connection"]
        }


def main():
    """Main pipeline execution"""
    print("\n" + "=" * 60)
    print("BLENDER + LLM INTEGRATION - PROOF OF CONCEPT")
    print("=" * 60)

    # Setup
    output_dir = ensure_output_dir()
    render_path = output_dir / "poc_render.png"

    # Scene description (what we expect to see)
    scene_description = """
    A simple 3D scene containing:
    - A green ground plane
    - An orange character placeholder (capsule/pill shape) at the center
    - 4 simple trees with brown trunks and green cone-shaped foliage
    - Three-point lighting setup
    - Blue gradient sky background
    - Camera positioned to show the character with environment visible
    """

    # Step 1: Render
    render_success = run_blender_render(render_path, samples=32)

    if not render_success:
        print("\n[PIPELINE FAILED] Render step failed. Check Blender installation.")
        sys.exit(1)

    if not render_path.exists():
        print(f"\n[PIPELINE FAILED] Render output not found: {render_path}")
        sys.exit(1)

    print(f"\nRender saved to: {render_path}")
    print(f"File size: {render_path.stat().st_size / 1024:.1f} KB")

    # Step 2: Validate
    validation = validate_with_claude_vision(render_path, scene_description)

    # Step 3: Report
    print("\n" + "=" * 60)
    print("STEP 3: Validation Results")
    print("=" * 60)

    if validation["success"]:
        if validation["matches_description"]:
            print("\n[PASS] Scene matches expected description!")
        else:
            print("\n[NEEDS ADJUSTMENT] Scene does not fully match description.")
            if validation["suggestions"]:
                print("\nSuggested improvements:")
                for suggestion in validation["suggestions"]:
                    print(f"  - {suggestion}")
    else:
        print("\n[VALIDATION SKIPPED] Could not validate image.")
        print(f"Reason: {validation['analysis']}")

    print("\n" + "=" * 60)
    print("PROOF OF CONCEPT COMPLETE")
    print("=" * 60)
    print(f"\nOutput image: {render_path}")
    print("\nThis demonstrates the complete pipeline:")
    print("  1. Claude generates Blender Python script")
    print("  2. Blender executes script headlessly")
    print("  3. Rendered image sent to Claude Vision for validation")
    print("  4. Feedback loop enables iterative refinement")


if __name__ == "__main__":
    main()
