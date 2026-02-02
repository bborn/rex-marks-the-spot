#!/usr/bin/env python3
"""Create side-by-side comparison images for social media."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "social-media" / "images"

# Comparison pairs: (before_path, after_path, output_name)
COMPARISONS = [
    (
        PROJECT_ROOT / "storyboards" / "act1" / "panels" / "scene-01-panel-01.png",
        PROJECT_ROOT / "storyboards" / "sketches" / "scene-01-panel-01-sketch.png",
        "storyboard-style-comparison-1.png"
    ),
    (
        PROJECT_ROOT / "storyboards" / "act2" / "panels" / "scene-20-panel-01.png",
        PROJECT_ROOT / "storyboards" / "sketches" / "scene-20-panel-01-sketch.png",
        "storyboard-style-comparison-2.png"
    ),
]


def create_comparison(before_path: Path, after_path: Path, output_name: str) -> Path:
    """Create a side-by-side comparison image with labels."""

    # Load images
    before_img = Image.open(before_path)
    after_img = Image.open(after_path)

    # Resize to same height if needed
    target_height = 400

    # Calculate new widths maintaining aspect ratio
    before_ratio = before_img.width / before_img.height
    after_ratio = after_img.width / after_img.height

    before_new_width = int(target_height * before_ratio)
    after_new_width = int(target_height * after_ratio)

    before_img = before_img.resize((before_new_width, target_height), Image.Resampling.LANCZOS)
    after_img = after_img.resize((after_new_width, target_height), Image.Resampling.LANCZOS)

    # Create canvas
    padding = 20
    label_height = 40
    gap = 30  # Gap between images

    total_width = before_img.width + gap + after_img.width + (padding * 2)
    total_height = target_height + label_height + (padding * 2)

    # Create white background
    canvas = Image.new('RGB', (total_width, total_height), color='#1a1a2e')
    draw = ImageDraw.Draw(canvas)

    # Try to load a font, fall back to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()

    # Calculate positions
    before_x = padding
    after_x = padding + before_img.width + gap
    image_y = padding + label_height

    # Draw labels
    before_label = "BEFORE: 3D Rendered"
    after_label = "AFTER: Pencil Sketch"

    # Center labels above images
    before_label_x = before_x + (before_img.width // 2)
    after_label_x = after_x + (after_img.width // 2)
    label_y = padding + 10

    draw.text((before_label_x, label_y), before_label, fill='#ff6b6b', font=font, anchor='mm')
    draw.text((after_label_x, label_y), after_label, fill='#4ecdc4', font=font, anchor='mm')

    # Paste images
    canvas.paste(before_img, (before_x, image_y))
    canvas.paste(after_img, (after_x, image_y))

    # Add subtle border around images
    draw.rectangle(
        [before_x - 2, image_y - 2, before_x + before_img.width + 2, image_y + before_img.height + 2],
        outline='#ff6b6b', width=2
    )
    draw.rectangle(
        [after_x - 2, image_y - 2, after_x + after_img.width + 2, image_y + after_img.height + 2],
        outline='#4ecdc4', width=2
    )

    # Save
    output_path = OUTPUT_DIR / output_name
    canvas.save(output_path, quality=95)
    print(f"Created: {output_path}")

    return output_path


def main():
    """Create all comparison images."""
    print("Creating storyboard comparison images...")
    print("=" * 50)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for before_path, after_path, output_name in COMPARISONS:
        if not before_path.exists():
            print(f"Missing: {before_path}")
            continue
        if not after_path.exists():
            print(f"Missing: {after_path}")
            continue

        create_comparison(before_path, after_path, output_name)

    print("=" * 50)
    print("Done!")


if __name__ == "__main__":
    main()
