#!/usr/bin/env python3
"""
Blender Automation Pipeline

Main orchestration script that ties together scene creation,
rendering, and validation in an end-to-end workflow.

This script runs OUTSIDE of Blender and manages the full pipeline.

Usage:
    # Basic usage
    python scripts/pipeline.py --scene "A forest with trees and a character"

    # With validation
    python scripts/pipeline.py --scene "scene description" --validate

    # Full iterative loop
    python scripts/pipeline.py --scene "scene description" --iterate --max-iterations 3

    # From config file
    python scripts/pipeline.py --config scene_config.json
"""

import os
import sys
import json
import argparse
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from render.engine import RenderEngine, RenderResult, generate_render_script
from render.batch import BatchRenderer, BatchJob
from validate.vision import (
    RenderValidator,
    ValidationResult,
    generate_scene_suggestions,
    check_api_available
)


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution."""
    scene_description: str
    output_dir: str = "./renders"
    output_name: str = "render"
    resolution: tuple = (1920, 1080)
    samples: int = 128
    validate: bool = False
    iterate: bool = False
    max_iterations: int = 3
    style_reference: Optional[str] = None
    verbose: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> 'PipelineConfig':
        return cls(
            scene_description=data.get('scene_description', ''),
            output_dir=data.get('output_dir', './renders'),
            output_name=data.get('output_name', 'render'),
            resolution=tuple(data.get('resolution', [1920, 1080])),
            samples=data.get('samples', 128),
            validate=data.get('validate', False),
            iterate=data.get('iterate', False),
            max_iterations=data.get('max_iterations', 3),
            style_reference=data.get('style_reference'),
            verbose=data.get('verbose', True)
        )

    @classmethod
    def from_json(cls, path: str) -> 'PipelineConfig':
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    success: bool
    output_path: Optional[str] = None
    iterations: int = 0
    render_time: float = 0.0
    validation_result: Optional[ValidationResult] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'success': self.success,
            'output_path': self.output_path,
            'iterations': self.iterations,
            'render_time': self.render_time,
            'validation': self.validation_result.to_dict() if self.validation_result else None,
            'error_message': self.error_message,
        }


class Pipeline:
    """
    Main pipeline orchestrator.

    Manages the complete workflow from scene description to validated render.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig(scene_description="")
        self.engine = RenderEngine()
        self.validator = RenderValidator()
        self.history: List[Dict[str, Any]] = []

        # Ensure output directory exists
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    def log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.config.verbose:
            print(message)

    def run(self) -> PipelineResult:
        """
        Execute the full pipeline.

        Returns:
            PipelineResult with outcome
        """
        self.log("\n" + "=" * 60)
        self.log("BLENDER AUTOMATION PIPELINE")
        self.log("=" * 60)

        # Check prerequisites
        if not self.engine.is_available():
            return PipelineResult(
                success=False,
                error_message=f"Blender not available: {self.engine.version}"
            )

        if not self.config.scene_description:
            return PipelineResult(
                success=False,
                error_message="No scene description provided"
            )

        # Generate scene setup if we have API access
        scene_setup = None
        api_available, _ = check_api_available()

        if api_available:
            self.log("\n[1/4] Generating scene setup recommendations...")
            scene_setup = generate_scene_suggestions(
                self.config.scene_description,
                style_reference=self.config.style_reference
            )
            if 'error' not in scene_setup:
                self.log("  Scene setup generated successfully")
            else:
                self.log(f"  Warning: {scene_setup.get('error')}")
                scene_setup = None

        # Create the render script
        self.log("\n[2/4] Creating render script...")
        script_path = self._create_render_script(scene_setup)
        self.log(f"  Script created: {script_path}")

        # Execute the pipeline
        if self.config.iterate and api_available:
            return self._run_iterative(script_path)
        else:
            return self._run_single(script_path)

    def _create_render_script(self, scene_setup: Optional[Dict] = None) -> str:
        """Create a render script based on scene description."""
        # Build scene description dict
        scene_dict = {
            'resolution': self.config.resolution,
            'samples': self.config.samples,
        }

        # Add defaults for scene elements
        scene_dict['ground'] = {'size': 20}
        scene_dict['lighting'] = {'type': 'three_point'}
        scene_dict['sky'] = {'gradient': True}
        scene_dict['camera'] = {
            'location': (7, -7, 5),
            'target': (0, 0, 1)
        }

        # Parse scene description for objects
        desc_lower = self.config.scene_description.lower()
        objects = []

        if 'character' in desc_lower or 'person' in desc_lower:
            objects.append({
                'type': 'character',
                'name': 'Character',
                'location': (0, 0, 0)
            })

        if 'tree' in desc_lower or 'forest' in desc_lower:
            for i, pos in enumerate([(-3, 3, 0), (4, 2, 0), (-2, -4, 0), (3, -3, 0)]):
                objects.append({
                    'type': 'tree',
                    'name': f'Tree_{i}',
                    'location': pos
                })

        scene_dict['objects'] = objects

        # Use scene setup suggestions if available
        if scene_setup and 'camera' in scene_setup:
            cam = scene_setup['camera']
            if 'position' in cam:
                scene_dict['camera']['location'] = tuple(cam['position'])
            if 'target' in cam:
                scene_dict['camera']['target'] = tuple(cam['target'])

        if scene_setup and 'lighting' in scene_setup:
            light = scene_setup['lighting']
            if 'type' in light:
                scene_dict['lighting']['type'] = light['type']
            if 'time_of_day' in light:
                scene_dict['lighting']['time'] = light['time_of_day']

        # Generate the script
        script_path = os.path.join(self.config.output_dir, 'scene_script.py')
        generate_render_script(scene_dict, script_path)

        return script_path

    def _run_single(self, script_path: str) -> PipelineResult:
        """Run a single render without iteration."""
        self.log("\n[3/4] Rendering scene...")

        output_path = os.path.join(
            self.config.output_dir,
            f"{self.config.output_name}.png"
        )

        result = self.engine.render(
            script_path,
            output_path,
            samples=self.config.samples,
            resolution=self.config.resolution
        )

        if not result.success:
            return PipelineResult(
                success=False,
                error_message=result.error_message
            )

        self.log(f"  Render complete: {output_path}")
        self.log(f"  Render time: {result.render_time:.1f}s")

        # Validate if requested
        validation_result = None
        if self.config.validate:
            self.log("\n[4/4] Validating render...")
            validation_result = self.validator.validate(
                output_path,
                self.config.scene_description
            )

            if validation_result.success:
                self.log(f"  Matches description: {validation_result.matches_description}")
                self.log(f"  Confidence: {validation_result.confidence:.0%}")

                if validation_result.elements_missing:
                    self.log("  Missing elements:")
                    for elem in validation_result.elements_missing:
                        self.log(f"    - {elem}")

                if validation_result.suggestions:
                    self.log("  Suggestions:")
                    for suggestion in validation_result.suggestions:
                        self.log(f"    - {suggestion}")
            else:
                self.log(f"  Validation error: {validation_result.error_message}")
        else:
            self.log("\n[4/4] Skipping validation (not requested)")

        return PipelineResult(
            success=True,
            output_path=output_path,
            iterations=1,
            render_time=result.render_time,
            validation_result=validation_result
        )

    def _run_iterative(self, script_path: str) -> PipelineResult:
        """Run iterative render-validate-improve loop."""
        self.log("\n[3/4] Starting iterative render loop...")

        total_render_time = 0
        current_script = script_path
        final_output = None
        final_validation = None

        for iteration in range(1, self.config.max_iterations + 1):
            self.log(f"\n--- Iteration {iteration}/{self.config.max_iterations} ---")

            # Render
            output_path = os.path.join(
                self.config.output_dir,
                f"{self.config.output_name}_iter{iteration}.png"
            )

            result = self.engine.render(
                current_script,
                output_path,
                samples=self.config.samples,
                resolution=self.config.resolution
            )

            if not result.success:
                self.log(f"  Render failed: {result.error_message}")
                break

            total_render_time += result.render_time
            final_output = output_path
            self.log(f"  Rendered: {output_path} ({result.render_time:.1f}s)")

            # Validate
            validation = self.validator.validate(
                output_path,
                self.config.scene_description
            )
            final_validation = validation

            if not validation.success:
                self.log(f"  Validation error: {validation.error_message}")
                break

            self.log(f"  Matches: {validation.matches_description} "
                    f"(confidence: {validation.confidence:.0%})")

            # Record in history
            self.history.append({
                'iteration': iteration,
                'output': output_path,
                'render_time': result.render_time,
                'matches': validation.matches_description,
                'confidence': validation.confidence,
                'suggestions': validation.suggestions
            })

            # Check if we're done
            if validation.matches_description and not validation.needs_changes:
                self.log("  Scene matches description - done!")
                break

            # Generate improvement suggestions
            if iteration < self.config.max_iterations:
                self.log("  Generating improvements...")
                improvement = self.validator.get_improvement_prompt(validation)
                self.log(f"  {improvement}")

                # In a full implementation, we would modify the script here
                # For now, we just note that improvements are needed
                self.log("  (Script modification not yet implemented)")

        self.log(f"\n[4/4] Iterative loop complete")
        self.log(f"  Total iterations: {len(self.history)}")
        self.log(f"  Total render time: {total_render_time:.1f}s")

        return PipelineResult(
            success=True,
            output_path=final_output,
            iterations=len(self.history),
            render_time=total_render_time,
            validation_result=final_validation,
            history=self.history
        )


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Blender Automation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --scene "A forest scene with trees"
  %(prog)s --scene "A character in a room" --validate
  %(prog)s --scene "Night scene" --iterate --max-iterations 5
  %(prog)s --config my_scene.json
        """
    )

    parser.add_argument(
        '--scene', '-s',
        type=str,
        help='Scene description'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to JSON config file'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='./renders',
        help='Output directory (default: ./renders)'
    )
    parser.add_argument(
        '--output-name', '-n',
        type=str,
        default='render',
        help='Output filename base (default: render)'
    )
    parser.add_argument(
        '--resolution', '-r',
        type=str,
        default='1920x1080',
        help='Resolution WxH (default: 1920x1080)'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=128,
        help='Render samples (default: 128)'
    )
    parser.add_argument(
        '--validate', '-v',
        action='store_true',
        help='Validate render against description'
    )
    parser.add_argument(
        '--iterate', '-i',
        action='store_true',
        help='Run iterative improvement loop'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=3,
        help='Maximum iterations for improvement loop (default: 3)'
    )
    parser.add_argument(
        '--style',
        type=str,
        help='Style reference (e.g., "Pixar style")'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output messages'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check Blender availability and exit'
    )

    args = parser.parse_args()

    # Check mode
    if args.check:
        engine = RenderEngine()
        if engine.is_available():
            print(f"Blender available: {engine.version}")
            api_ok, api_msg = check_api_available()
            print(f"Claude API: {api_msg}")
            sys.exit(0)
        else:
            print(f"Blender not available: {engine.version}")
            sys.exit(1)

    # Load config
    if args.config:
        config = PipelineConfig.from_json(args.config)
    else:
        if not args.scene:
            parser.error("Either --scene or --config is required")

        # Parse resolution
        try:
            w, h = args.resolution.lower().split('x')
            resolution = (int(w), int(h))
        except:
            resolution = (1920, 1080)

        config = PipelineConfig(
            scene_description=args.scene,
            output_dir=args.output_dir,
            output_name=args.output_name,
            resolution=resolution,
            samples=args.samples,
            validate=args.validate,
            iterate=args.iterate,
            max_iterations=args.max_iterations,
            style_reference=args.style,
            verbose=not args.quiet
        )

    # Run pipeline
    pipeline = Pipeline(config)
    result = pipeline.run()

    # Output results
    if not args.quiet:
        print("\n" + "=" * 60)
        print("PIPELINE RESULT")
        print("=" * 60)
        print(json.dumps(result.to_dict(), indent=2))

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
