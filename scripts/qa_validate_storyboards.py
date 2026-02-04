#!/usr/bin/env python3
"""
QA Validation Script for Storyboard Panels

Analyzes all storyboard panels across Acts 1, 2, and 3 for quality issues:
- Corrupted/unreadable images
- TV static / noise patterns
- Low contrast or washed-out images
- Very dark images
- Unusual file sizes (too small = likely corrupted)
- Aspect ratio anomalies

Usage:
    python scripts/qa_validate_storyboards.py [--output-dir reports]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    from PIL import Image
    import numpy as np
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Install with: pip install pillow numpy")
    sys.exit(1)


class StoryboardQAValidator:
    """Validates storyboard panels for quality issues."""

    # Quality thresholds
    MIN_FILE_SIZE_KB = 10  # Minimum file size in KB
    MIN_RESOLUTION = 200  # Minimum width/height
    EXPECTED_ASPECT_RATIO = (16, 9)  # Expected aspect ratio
    ASPECT_RATIO_TOLERANCE = 0.3  # How much deviation is allowed

    NOISE_THRESHOLD = 0.85  # High-frequency content threshold for TV static
    MIN_CONTRAST = 0.05  # Minimum standard deviation for contrast
    MAX_DARKNESS = 0.1  # Maximum average brightness before flagging as too dark
    MIN_BRIGHTNESS = 0.05  # Too dark threshold
    MAX_BRIGHTNESS = 0.95  # Too bright/washed out threshold

    def __init__(self, storyboards_dir: Path):
        self.storyboards_dir = storyboards_dir
        self.results = {
            "summary": {},
            "panels": {},
            "issues": {
                "corrupted": [],
                "tv_static": [],
                "low_contrast": [],
                "too_dark": [],
                "too_bright": [],
                "small_file": [],
                "low_resolution": [],
                "aspect_ratio": [],
            },
            "by_act": {},
            "by_scene": {},
        }

    def find_all_panels(self) -> list[Path]:
        """Find all storyboard panel images."""
        panels = []
        for act_dir in ["act1", "act2", "act3"]:
            panels_dir = self.storyboards_dir / act_dir / "panels"
            if panels_dir.exists():
                panels.extend(sorted(panels_dir.glob("*.png")))
        return panels

    def analyze_image(self, image_path: Path) -> dict:
        """Analyze a single image for quality issues."""
        result = {
            "path": str(image_path),
            "filename": image_path.name,
            "issues": [],
            "scores": {},
            "metadata": {},
        }

        # Check file size
        file_size_kb = image_path.stat().st_size / 1024
        result["metadata"]["file_size_kb"] = round(file_size_kb, 1)

        if file_size_kb < self.MIN_FILE_SIZE_KB:
            result["issues"].append("small_file")

        # Try to open the image
        try:
            img = Image.open(image_path)
            img.load()  # Force load to detect corruption
        except Exception as e:
            result["issues"].append("corrupted")
            result["error"] = str(e)
            return result

        # Get image dimensions
        width, height = img.size
        result["metadata"]["width"] = width
        result["metadata"]["height"] = height
        result["metadata"]["mode"] = img.mode

        # Check resolution
        if width < self.MIN_RESOLUTION or height < self.MIN_RESOLUTION:
            result["issues"].append("low_resolution")

        # Check aspect ratio
        actual_ratio = width / height
        expected_ratio = self.EXPECTED_ASPECT_RATIO[0] / self.EXPECTED_ASPECT_RATIO[1]
        ratio_diff = abs(actual_ratio - expected_ratio) / expected_ratio
        result["metadata"]["aspect_ratio"] = round(actual_ratio, 2)

        if ratio_diff > self.ASPECT_RATIO_TOLERANCE:
            result["issues"].append("aspect_ratio")

        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Convert to numpy array for analysis
        img_array = np.array(img, dtype=np.float32) / 255.0

        # Calculate brightness
        brightness = np.mean(img_array)
        result["scores"]["brightness"] = round(brightness, 3)

        if brightness < self.MIN_BRIGHTNESS:
            result["issues"].append("too_dark")
        elif brightness > self.MAX_BRIGHTNESS:
            result["issues"].append("too_bright")

        # Calculate contrast (standard deviation)
        contrast = np.std(img_array)
        result["scores"]["contrast"] = round(contrast, 3)

        if contrast < self.MIN_CONTRAST:
            result["issues"].append("low_contrast")

        # Detect TV static / noise pattern
        noise_score = self._detect_noise(img_array)
        result["scores"]["noise"] = round(noise_score, 3)

        if noise_score > self.NOISE_THRESHOLD:
            result["issues"].append("tv_static")

        # Calculate overall quality score (0-100)
        quality_score = self._calculate_quality_score(result)
        result["scores"]["quality"] = quality_score

        return result

    def _detect_noise(self, img_array: np.ndarray) -> float:
        """
        Detect TV static / noise patterns using high-frequency analysis.

        TV static has high-frequency random variations between adjacent pixels.
        We measure this by computing local variance.
        """
        # Convert to grayscale
        gray = np.mean(img_array, axis=2)

        # Calculate local variance using neighboring pixels
        # High local variance = noisy/static
        padded = np.pad(gray, 1, mode='edge')

        # Compute difference with neighbors
        diff_h = np.abs(gray - padded[1:-1, :-2])  # Left neighbor
        diff_v = np.abs(gray - padded[:-2, 1:-1])  # Top neighbor

        # Average local variation
        local_var = (np.mean(diff_h) + np.mean(diff_v)) / 2

        # Normalize to 0-1 range
        # Natural images typically have local_var < 0.1
        # TV static has local_var > 0.2
        noise_score = min(local_var / 0.25, 1.0)

        return noise_score

    def _calculate_quality_score(self, result: dict) -> int:
        """Calculate overall quality score from 0-100."""
        base_score = 100

        # Deduct points for issues
        issue_penalties = {
            "corrupted": 100,
            "tv_static": 50,
            "low_contrast": 20,
            "too_dark": 30,
            "too_bright": 25,
            "small_file": 40,
            "low_resolution": 30,
            "aspect_ratio": 10,
        }

        for issue in result["issues"]:
            if issue in issue_penalties:
                base_score -= issue_penalties[issue]

        # Additional adjustments based on scores
        if "brightness" in result["scores"]:
            brightness = result["scores"]["brightness"]
            # Optimal brightness around 0.4-0.6
            if 0.3 <= brightness <= 0.7:
                pass
            elif 0.2 <= brightness < 0.3 or 0.7 < brightness <= 0.8:
                base_score -= 5
            else:
                base_score -= 10

        if "contrast" in result["scores"]:
            contrast = result["scores"]["contrast"]
            # Higher contrast is generally better (within reason)
            if contrast >= 0.15:
                pass
            elif contrast >= 0.1:
                base_score -= 5
            else:
                base_score -= 10

        return max(0, min(100, base_score))

    def validate_all(self, progress_callback=None) -> dict:
        """Validate all storyboard panels."""
        panels = self.find_all_panels()
        total = len(panels)

        print(f"\nFound {total} storyboard panels to validate\n")

        for i, panel_path in enumerate(panels):
            if progress_callback:
                progress_callback(i + 1, total, panel_path.name)
            else:
                # Simple progress indicator
                if (i + 1) % 50 == 0 or (i + 1) == total:
                    print(f"  Progress: {i + 1}/{total} panels analyzed")

            result = self.analyze_image(panel_path)

            # Store result
            rel_path = str(panel_path.relative_to(self.storyboards_dir))
            self.results["panels"][rel_path] = result

            # Categorize by issues
            for issue in result["issues"]:
                if issue in self.results["issues"]:
                    self.results["issues"][issue].append(rel_path)

            # Parse act and scene from path
            parts = panel_path.parts
            act = None
            scene = None
            for part in parts:
                if part.startswith("act"):
                    act = part
                elif part.startswith("scene-"):
                    scene = part.split("-panel-")[0]

            if act:
                if act not in self.results["by_act"]:
                    self.results["by_act"][act] = []
                self.results["by_act"][act].append(result)

            if scene:
                if scene not in self.results["by_scene"]:
                    self.results["by_scene"][scene] = []
                self.results["by_scene"][scene].append(result)

        # Generate summary
        self._generate_summary()

        return self.results

    def _generate_summary(self):
        """Generate summary statistics."""
        all_panels = list(self.results["panels"].values())

        total = len(all_panels)
        with_issues = sum(1 for p in all_panels if p["issues"])

        quality_scores = [p["scores"].get("quality", 0) for p in all_panels]
        avg_quality = sum(quality_scores) / total if total > 0 else 0

        self.results["summary"] = {
            "total_panels": total,
            "panels_with_issues": with_issues,
            "panels_passing": total - with_issues,
            "pass_rate": round((total - with_issues) / total * 100, 1) if total > 0 else 0,
            "average_quality_score": round(avg_quality, 1),
            "issue_counts": {
                issue: len(paths) for issue, paths in self.results["issues"].items()
            },
            "by_act": {
                act: {
                    "total": len(panels),
                    "with_issues": sum(1 for p in panels if p["issues"]),
                    "avg_quality": round(sum(p["scores"].get("quality", 0) for p in panels) / len(panels), 1) if panels else 0
                }
                for act, panels in self.results["by_act"].items()
            },
            "validated_at": datetime.now().isoformat(),
        }

    def generate_report(self, output_path: Path = None) -> str:
        """Generate a human-readable report."""
        lines = []
        lines.append("=" * 70)
        lines.append("STORYBOARD QA VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Storyboards directory: {self.storyboards_dir}")

        summary = self.results["summary"]

        lines.append("\n" + "-" * 70)
        lines.append("SUMMARY")
        lines.append("-" * 70)
        lines.append(f"Total panels analyzed: {summary['total_panels']}")
        lines.append(f"Panels passing: {summary['panels_passing']} ({summary['pass_rate']}%)")
        lines.append(f"Panels with issues: {summary['panels_with_issues']}")
        lines.append(f"Average quality score: {summary['average_quality_score']}/100")

        lines.append("\n" + "-" * 70)
        lines.append("BREAKDOWN BY ACT")
        lines.append("-" * 70)
        for act in sorted(summary.get("by_act", {}).keys()):
            act_data = summary["by_act"][act]
            lines.append(f"  {act.upper()}: {act_data['total']} panels, "
                        f"{act_data['with_issues']} with issues, "
                        f"avg quality: {act_data['avg_quality']}")

        lines.append("\n" + "-" * 70)
        lines.append("ISSUES DETECTED")
        lines.append("-" * 70)

        issue_descriptions = {
            "corrupted": "Corrupted/unreadable images",
            "tv_static": "TV static/noise patterns",
            "low_contrast": "Low contrast images",
            "too_dark": "Images too dark",
            "too_bright": "Images too bright/washed out",
            "small_file": "Suspiciously small files",
            "low_resolution": "Below minimum resolution",
            "aspect_ratio": "Unusual aspect ratio",
        }

        for issue_type, paths in self.results["issues"].items():
            if paths:
                lines.append(f"\n### {issue_descriptions.get(issue_type, issue_type)} ({len(paths)})")
                for path in paths[:10]:  # Show first 10
                    panel_data = self.results["panels"].get(path, {})
                    quality = panel_data.get("scores", {}).get("quality", "N/A")
                    lines.append(f"  - {path} (quality: {quality})")
                if len(paths) > 10:
                    lines.append(f"  ... and {len(paths) - 10} more")

        # Find lowest quality panels
        lines.append("\n" + "-" * 70)
        lines.append("LOWEST QUALITY PANELS (Bottom 20)")
        lines.append("-" * 70)

        sorted_panels = sorted(
            self.results["panels"].items(),
            key=lambda x: x[1]["scores"].get("quality", 0)
        )[:20]

        for path, data in sorted_panels:
            quality = data["scores"].get("quality", 0)
            issues = ", ".join(data["issues"]) if data["issues"] else "no major issues"
            lines.append(f"  {path}")
            lines.append(f"    Quality: {quality}/100 | Issues: {issues}")

        # Scene-by-scene breakdown for scenes with issues
        lines.append("\n" + "-" * 70)
        lines.append("SCENES NEEDING ATTENTION")
        lines.append("-" * 70)

        problem_scenes = []
        for scene, panels in self.results["by_scene"].items():
            issue_count = sum(1 for p in panels if p["issues"])
            avg_quality = sum(p["scores"].get("quality", 0) for p in panels) / len(panels) if panels else 0
            if issue_count > 0 or avg_quality < 70:
                problem_scenes.append((scene, len(panels), issue_count, avg_quality))

        problem_scenes.sort(key=lambda x: x[3])  # Sort by avg quality

        for scene, total, issues, avg_q in problem_scenes[:15]:
            lines.append(f"  {scene}: {issues}/{total} panels with issues, avg quality: {avg_q:.1f}")

        report = "\n".join(lines)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"\nReport saved to: {output_path}")

        return report


def main():
    parser = argparse.ArgumentParser(description="QA validation for storyboard panels")
    parser.add_argument("--storyboards-dir", type=Path, default=Path("storyboards"),
                        help="Path to storyboards directory")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"),
                        help="Output directory for reports")
    parser.add_argument("--json", action="store_true",
                        help="Also output detailed JSON results")

    args = parser.parse_args()

    # Find storyboards directory
    storyboards_dir = args.storyboards_dir
    if not storyboards_dir.is_absolute():
        # Try relative to script location or cwd
        script_dir = Path(__file__).parent.parent
        if (script_dir / storyboards_dir).exists():
            storyboards_dir = script_dir / storyboards_dir
        elif not storyboards_dir.exists():
            print(f"ERROR: Storyboards directory not found: {storyboards_dir}")
            sys.exit(1)

    print(f"Storyboards directory: {storyboards_dir}")

    # Run validation
    validator = StoryboardQAValidator(storyboards_dir)
    results = validator.validate_all()

    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = args.output_dir / f"qa_report_{timestamp}.txt"

    report = validator.generate_report(report_path)
    print("\n" + report)

    # Save JSON if requested
    if args.json:
        json_path = args.output_dir / f"qa_results_{timestamp}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert results to JSON-serializable format (handle numpy types)
        def convert_to_serializable(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(i) for i in obj]
            return obj

        json_results = convert_to_serializable({
            "summary": results["summary"],
            "issues": results["issues"],
            "panels": {
                path: {
                    "filename": data["filename"],
                    "issues": data["issues"],
                    "scores": data["scores"],
                    "metadata": data["metadata"],
                }
                for path, data in results["panels"].items()
            }
        })

        with open(json_path, "w") as f:
            json.dump(json_results, f, indent=2)
        print(f"JSON results saved to: {json_path}")

    # Exit with error code if critical issues found
    critical_issues = len(results["issues"]["corrupted"]) + len(results["issues"]["tv_static"])
    if critical_issues > 0:
        print(f"\n⚠️  Found {critical_issues} critical issues (corrupted or TV static)")
        sys.exit(1)

    print("\n✓ QA validation complete")


if __name__ == "__main__":
    main()
