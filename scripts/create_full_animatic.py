#!/usr/bin/env python3
"""
Create Full Movie Animatic for "Fairy Dinosaur Date Night"

Combines Act 1, Act 2, and Act 3 storyboard panels into a single MP4 video
with title cards between acts.

Uses ffmpeg's concat demuxer for efficient video generation.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# Configuration
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
FPS = 24
TITLE_DURATION = 4  # seconds for title cards
ACT_TITLE_DURATION = 3  # seconds for act title cards

# For a reasonable review animatic, use shorter fixed durations
REVIEW_SECONDS_PER_PANEL = 2  # 2 seconds per panel for director review


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def create_title_card(text: str, subtitle: str = "", output_path: Path = None) -> Image.Image:
    """Create a title card image."""
    img = Image.new('RGB', (FRAME_WIDTH, FRAME_HEIGHT), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fallback to default
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except (OSError, IOError):
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (FRAME_WIDTH - text_width) // 2
    y = (FRAME_HEIGHT - text_height) // 2 - 50

    # Draw main title with golden color
    draw.text((x, y), text, fill=(255, 200, 100), font=title_font)

    # Draw subtitle if provided
    if subtitle:
        bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        sub_width = bbox[2] - bbox[0]
        sub_x = (FRAME_WIDTH - sub_width) // 2
        sub_y = y + text_height + 40
        draw.text((sub_x, sub_y), subtitle, fill=(180, 180, 200), font=subtitle_font)

    if output_path:
        img.save(output_path, quality=95)

    return img


def resize_panel(panel_path: Path, output_path: Path):
    """Resize a panel to fit the frame while maintaining aspect ratio."""
    img = Image.open(panel_path)

    # Create black background
    result = Image.new('RGB', (FRAME_WIDTH, FRAME_HEIGHT), color=(0, 0, 0))

    # Calculate scaling to fit
    scale_w = FRAME_WIDTH / img.width
    scale_h = FRAME_HEIGHT / img.height
    scale = min(scale_w, scale_h)

    new_width = int(img.width * scale)
    new_height = int(img.height * scale)

    # Resize with high quality
    img_resized = img.resize((new_width, new_height), Image.LANCZOS)

    # Center on background
    x = (FRAME_WIDTH - new_width) // 2
    y = (FRAME_HEIGHT - new_height) // 2

    result.paste(img_resized, (x, y))
    result.save(output_path, quality=95)


def get_sorted_panels(panels_dir: Path) -> list:
    """Get panels sorted by scene and panel number."""
    panels = list(panels_dir.glob("scene-*.png"))

    def sort_key(p):
        # Extract scene and panel numbers from filename like scene-01-panel-02.png
        name = p.stem
        parts = name.split('-')
        scene_num = int(parts[1])
        panel_num = int(parts[3])
        return (scene_num, panel_num)

    return sorted(panels, key=sort_key)


def create_animatic(output_path: str, review_mode: bool = True):
    """Create the full movie animatic using ffmpeg concat demuxer."""
    root = get_project_root()

    # Source directories
    act1_panels = root / "docs" / "storyboards" / "act1" / "panels"
    act2_panels = root / "docs" / "storyboards" / "act2" / "panels"
    act3_panels = root / "storyboards" / "act3" / "panels"

    # Panel duration
    panel_duration = REVIEW_SECONDS_PER_PANEL if review_mode else 3

    # Create temp directory for processed frames
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        processed_dir = temp_path / "processed"
        processed_dir.mkdir()

        # List to track all images and their durations for the concat file
        concat_entries = []
        total_panels = 0

        def add_image_entry(img_path: Path, duration: float):
            """Add an image entry to the concat list."""
            nonlocal total_panels
            # Escape path for ffmpeg concat file
            escaped_path = str(img_path).replace("'", "'\\''")
            concat_entries.append(f"file '{escaped_path}'")
            concat_entries.append(f"duration {duration}")
            total_panels += 1

        def process_and_add_panel(panel_path: Path, idx: int, prefix: str, duration: float):
            """Process a panel image and add it to the list."""
            processed_path = processed_dir / f"{prefix}_{idx:04d}.png"
            resize_panel(panel_path, processed_path)
            add_image_entry(processed_path, duration)

        print("Creating Full Movie Animatic for 'Fairy Dinosaur Date Night'", flush=True)
        print("=" * 60, flush=True)

        # Movie Title Card
        print("Creating movie title card...", flush=True)
        title_path = processed_dir / "title_main.png"
        create_title_card("FAIRY DINOSAUR DATE NIGHT", "An AI-Generated Animated Movie", title_path)
        add_image_entry(title_path, TITLE_DURATION)

        # ACT 1
        print("\nProcessing Act 1...", flush=True)
        act1_title_path = processed_dir / "title_act1.png"
        create_title_card("ACT ONE", "The Inciting Incident", act1_title_path)
        add_image_entry(act1_title_path, ACT_TITLE_DURATION)

        act1_files = get_sorted_panels(act1_panels)
        print(f"  Found {len(act1_files)} panels", flush=True)
        for i, panel in enumerate(act1_files):
            process_and_add_panel(panel, i, "act1", panel_duration)
            if (i + 1) % 20 == 0:
                print(f"  Processed {i + 1}/{len(act1_files)} panels", flush=True)
        print(f"  Act 1 complete: {len(act1_files)} panels", flush=True)

        # ACT 2
        print("\nProcessing Act 2...", flush=True)
        act2_title_path = processed_dir / "title_act2.png"
        create_title_card("ACT TWO", "The Investigation", act2_title_path)
        add_image_entry(act2_title_path, ACT_TITLE_DURATION)

        act2_files = get_sorted_panels(act2_panels)
        print(f"  Found {len(act2_files)} panels", flush=True)
        for i, panel in enumerate(act2_files):
            process_and_add_panel(panel, i, "act2", panel_duration)
            if (i + 1) % 20 == 0:
                print(f"  Processed {i + 1}/{len(act2_files)} panels", flush=True)
        print(f"  Act 2 complete: {len(act2_files)} panels", flush=True)

        # ACT 3
        print("\nProcessing Act 3...", flush=True)
        act3_title_path = processed_dir / "title_act3.png"
        create_title_card("ACT THREE", "The Rescue", act3_title_path)
        add_image_entry(act3_title_path, ACT_TITLE_DURATION)

        act3_files = get_sorted_panels(act3_panels)
        print(f"  Found {len(act3_files)} panels", flush=True)
        for i, panel in enumerate(act3_files):
            process_and_add_panel(panel, i, "act3", panel_duration)
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(act3_files)} panels", flush=True)
        print(f"  Act 3 complete: {len(act3_files)} panels", flush=True)

        # End Title Card
        print("\nAdding end title card...", flush=True)
        end_title_path = processed_dir / "title_end.png"
        create_title_card("THE END", "Thank you for watching", end_title_path)
        add_image_entry(end_title_path, TITLE_DURATION)

        # The concat demuxer needs the last image repeated without duration
        escaped_end_path = str(end_title_path).replace("'", "'\"'\"'")
        concat_entries.append(f"file '{escaped_end_path}'")

        # Write concat file
        concat_file = temp_path / "concat.txt"
        with open(concat_file, 'w') as f:
            f.write('\n'.join(concat_entries))

        # Calculate total duration
        total_duration = (
            TITLE_DURATION +  # Main title
            ACT_TITLE_DURATION +  # Act 1 title
            len(act1_files) * panel_duration +
            ACT_TITLE_DURATION +  # Act 2 title
            len(act2_files) * panel_duration +
            ACT_TITLE_DURATION +  # Act 3 title
            len(act3_files) * panel_duration +
            TITLE_DURATION  # End title
        )
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)

        print(f"\nTotal panels: {len(act1_files) + len(act2_files) + len(act3_files)}", flush=True)
        print(f"Total duration: {minutes}:{seconds:02d}", flush=True)

        # Generate video with ffmpeg using concat demuxer
        print(f"\nGenerating MP4 video: {output_path}", flush=True)

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-vf", f"fps={FPS}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path
        ]

        print(f"Running: {' '.join(ffmpeg_cmd)}", flush=True)

        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr}", flush=True)
            raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")

        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\nAnimatic created successfully: {output_path}", flush=True)
        print(f"File size: {file_size:.1f} MB", flush=True)

        return output_path


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Create full movie animatic")
    parser.add_argument(
        "-o", "--output",
        default="renders/fairy_dinosaur_date_night_animatic.mp4",
        help="Output MP4 file path"
    )
    parser.add_argument(
        "--full-timing",
        action="store_true",
        help="Use full animatic timing (longer video) instead of review timing"
    )

    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    create_animatic(str(output_path), review_mode=not args.full_timing)


if __name__ == "__main__":
    main()
