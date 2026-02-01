#!/usr/bin/env python3
"""
Example Workflow: Full Pipeline Demonstration

This script demonstrates the complete pipeline from scene description
to validated render, showcasing all major components.

This script runs OUTSIDE of Blender and orchestrates the full workflow.

Usage:
    python scripts/example_workflow.py

Requirements:
    - Blender installed and in PATH (or BLENDER_PATH set)
    - Optional: ANTHROPIC_API_KEY for vision validation
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure scripts directory is in path
sys.path.insert(0, str(Path(__file__).parent))

from render.engine import RenderEngine, RenderConfig
from render.batch import BatchRenderer
from validate.vision import (
    check_api_available,
    validate_render,
    generate_scene_suggestions,
    RenderValidator
)


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step: int, total: int, message: str) -> None:
    """Print a step indicator."""
    print(f"\n[{step}/{total}] {message}")


def demo_basic_render():
    """Demonstrate basic render functionality."""
    print_header("DEMO 1: Basic Render")

    engine = RenderEngine()

    if not engine.is_available():
        print(f"Blender not available: {engine.version}")
        print("Skipping render demos...")
        return False

    print(f"Blender version: {engine.version}")

    # Use the POC script
    script_path = Path(__file__).parent / "poc_create_scene.py"
    output_path = Path(__file__).parent.parent / "renders" / "demo_basic.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print_step(1, 2, "Rendering scene...")
    result = engine.render(
        str(script_path),
        str(output_path),
        samples=32  # Low samples for quick demo
    )

    if result.success:
        print(f"  Render complete!")
        print(f"  Output: {output_path}")
        print(f"  Render time: {result.render_time:.1f}s")
        print_step(2, 2, "Success!")
        return True
    else:
        print(f"  Render failed: {result.error_message}")
        return False


def demo_validation():
    """Demonstrate vision validation functionality."""
    print_header("DEMO 2: Vision Validation")

    available, message = check_api_available()
    if not available:
        print(f"Claude API not available: {message}")
        print("Skipping validation demo...")
        return False

    print("Claude Vision API: Available")

    # Check for rendered image
    render_path = Path(__file__).parent.parent / "renders" / "demo_basic.png"
    if not render_path.exists():
        print(f"No render found at {render_path}")
        print("Run demo_basic_render() first")
        return False

    scene_description = """
    A simple 3D scene containing:
    - A green ground plane
    - An orange character placeholder (capsule/pill shape) at the center
    - 4 simple trees with brown trunks and green cone-shaped foliage
    - Three-point lighting setup
    - Blue gradient sky background
    """

    print_step(1, 2, "Validating render against description...")
    result = validate_render(str(render_path), scene_description)

    if result.success:
        print(f"\n  Matches description: {result.matches_description}")
        print(f"  Confidence: {result.confidence:.0%}")

        if result.elements_found:
            print(f"\n  Elements found:")
            for elem in result.elements_found[:5]:  # Limit output
                print(f"    + {elem}")

        if result.elements_missing:
            print(f"\n  Elements missing:")
            for elem in result.elements_missing[:5]:
                print(f"    - {elem}")

        if result.suggestions:
            print(f"\n  Suggestions:")
            for suggestion in result.suggestions[:3]:
                print(f"    * {suggestion}")

        print_step(2, 2, "Validation complete!")
        return True
    else:
        print(f"  Validation error: {result.error_message}")
        return False


def demo_scene_suggestions():
    """Demonstrate AI-generated scene setup suggestions."""
    print_header("DEMO 3: Scene Setup Suggestions")

    available, message = check_api_available()
    if not available:
        print(f"Claude API not available: {message}")
        print("Skipping suggestions demo...")
        return False

    scene_description = """
    Scene 7 from "Fairy Dinosaur Date Night":
    Interior of crashed car in Jurassic swamp.
    Nina wakes up confused, car interior strewn with toys and debris.
    Water drips, smoke from hood. Lush swamp visible outside.
    Time of day: Day
    Mood: Disoriented, wonderment
    """

    print_step(1, 2, "Generating scene setup recommendations...")
    suggestions = generate_scene_suggestions(
        scene_description,
        style_reference="Pixar/DreamWorks animated style"
    )

    if 'error' not in suggestions:
        print("\n  Camera Setup:")
        if 'camera' in suggestions:
            cam = suggestions['camera']
            print(f"    Position: {cam.get('position', 'N/A')}")
            print(f"    Target: {cam.get('target', 'N/A')}")
            print(f"    Focal length: {cam.get('focal_length', 'N/A')}mm")
            if 'notes' in cam:
                print(f"    Notes: {cam['notes'][:100]}...")

        print("\n  Lighting Setup:")
        if 'lighting' in suggestions:
            light = suggestions['lighting']
            print(f"    Type: {light.get('type', 'N/A')}")
            if 'notes' in light:
                print(f"    Notes: {light['notes'][:100]}...")

        print("\n  Objects Suggested:")
        if 'objects' in suggestions:
            for obj in suggestions['objects'][:5]:
                print(f"    - {obj.get('name', 'unnamed')}: {obj.get('type', 'unknown')}")

        print_step(2, 2, "Suggestions generated!")
        return True
    else:
        print(f"  Error: {suggestions['error']}")
        return False


def demo_iterative_workflow():
    """Demonstrate the iterative render-validate-improve workflow."""
    print_header("DEMO 4: Iterative Workflow")

    engine = RenderEngine()
    if not engine.is_available():
        print("Blender not available, skipping...")
        return False

    available, _ = check_api_available()
    if not available:
        print("Claude API not available, skipping...")
        return False

    scene_description = """
    A simple outdoor scene with:
    - Green grass ground
    - An orange character in the center
    - Four trees surrounding the character
    - Blue sky
    """

    validator = RenderValidator()
    script_path = Path(__file__).parent / "poc_create_scene.py"
    renders_dir = Path(__file__).parent.parent / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)

    max_iterations = 2  # Limited for demo
    print(f"Starting iterative workflow (max {max_iterations} iterations)...")

    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration} ---")

        # Render
        output_path = renders_dir / f"demo_iter_{iteration}.png"
        print_step(1, 3, "Rendering...")

        result = engine.render(
            str(script_path),
            str(output_path),
            samples=32
        )

        if not result.success:
            print(f"  Render failed: {result.error_message}")
            break

        print(f"  Completed in {result.render_time:.1f}s")

        # Validate
        print_step(2, 3, "Validating...")
        validation = validator.validate(str(output_path), scene_description)

        if not validation.success:
            print(f"  Validation error: {validation.error_message}")
            break

        print(f"  Matches: {validation.matches_description}")
        print(f"  Confidence: {validation.confidence:.0%}")

        # Check if we're done
        if validation.matches_description and not validation.needs_changes:
            print_step(3, 3, "Scene matches description!")
            break

        # Get improvement suggestions
        print_step(3, 3, "Getting improvements...")
        improvement = validator.get_improvement_prompt(validation)
        print(f"  {improvement[:200]}...")

    # Summary
    print("\n--- Workflow Summary ---")
    summary = validator.get_history_summary()
    for entry in summary:
        status = "PASS" if entry['matches'] else "NEEDS WORK"
        print(f"  Iteration {entry['iteration']}: {status} "
              f"({entry['suggestions_count']} suggestions)")

    return True


def demo_batch_setup():
    """Demonstrate batch rendering setup."""
    print_header("DEMO 5: Batch Rendering Setup")

    batch = BatchRenderer(output_dir="./renders/batch_demo")

    # Add jobs (these won't actually run without the scripts)
    scenes = [
        ("scene_01_home", "Living room with family"),
        ("scene_07_car", "Crashed car in swamp"),
        ("scene_26_swamp", "Kids in Jurassic swamp"),
    ]

    print("Setting up batch jobs:")
    for name, desc in scenes:
        # In real usage, these would be actual scripts
        job = batch.add_job(
            name=name,
            source=f"scripts/scenes/{name}.py",  # Placeholder
            samples=256,
            resolution=(1920, 1080)
        )
        print(f"  + {name}: {desc}")

    print(f"\nBatch configured with {len(batch.jobs)} jobs")
    print("  (Not executing - scripts don't exist yet)")

    return True


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("  BLENDER AUTOMATION PIPELINE - EXAMPLE WORKFLOW")
    print("=" * 60)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Working directory: {os.getcwd()}")

    # Check prerequisites
    print("\n--- Prerequisites ---")

    engine = RenderEngine()
    print(f"Blender: {'Available' if engine.is_available() else 'Not found'}")
    if engine.is_available():
        print(f"  Version: {engine.version}")

    api_ok, api_msg = check_api_available()
    print(f"Claude API: {api_msg}")

    # Run demos
    results = {}

    # Demo 1: Basic render
    results['basic_render'] = demo_basic_render()

    # Demo 2: Validation (needs render and API)
    results['validation'] = demo_validation()

    # Demo 3: Scene suggestions (needs API only)
    results['suggestions'] = demo_scene_suggestions()

    # Demo 4: Iterative workflow (needs both)
    results['iterative'] = demo_iterative_workflow()

    # Demo 5: Batch setup (no dependencies)
    results['batch_setup'] = demo_batch_setup()

    # Summary
    print_header("DEMO SUMMARY")
    for demo, success in results.items():
        status = "PASS" if success else "SKIP"
        print(f"  {demo}: {status}")

    passed = sum(1 for s in results.values() if s)
    total = len(results)
    print(f"\n  Total: {passed}/{total} demos completed")

    print("\n" + "=" * 60)
    print("  EXAMPLE WORKFLOW COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
