#!/usr/bin/env python3
"""
Generate social media teaser images from best storyboard panels.

Creates optimized images for:
- Twitter/X: 1200x675 (16:9 landscape)
- Instagram: 1080x1080 (square) and 1080x1350 (4:5 portrait)
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
STORYBOARDS_DOC = PROJECT_ROOT / "docs" / "storyboards"
STORYBOARDS_SRC = PROJECT_ROOT / "storyboards"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "social-media"

# Social media dimensions
TWITTER_SIZE = (1200, 675)  # 16:9
INSTAGRAM_SQUARE = (1080, 1080)  # 1:1
INSTAGRAM_PORTRAIT = (1080, 1350)  # 4:5

# Best panels selected from storyboard review (scores 4.8-5.0)
BEST_PANELS = [
    # Format: (source_path, name, description, category)
    ("docs/storyboards/act1/panels/scene-05-panel-02.png", "portal-terror", "Parents terrified by portal", "dramatic"),
    ("docs/storyboards/act1/panels/scene-05-panel-03.png", "car-portal", "Car entering portal", "action"),
    ("docs/storyboards/act1/panels/scene-05-panel-01.png", "portal-vortex", "Magical vortex", "vfx"),
    ("docs/storyboards/act1/panels/scene-06-panel-02.png", "kids-closeup", "Three kids reaction", "character"),
    ("docs/storyboards/act1/panels/scene-07-panel-03.png", "dino-toy", "Toy dinosaur sunset", "emotional"),
    ("docs/storyboards/act1/panels/scene-02-panel-01.png", "house-storm", "House in storm", "atmosphere"),
    ("docs/storyboards/act1/panels/scene-02-panel-02.png", "rain-run", "Running in rain", "action"),
    ("docs/storyboards/act1/panels/scene-03-panel-04.png", "nina-car", "Nina in car", "character"),
    ("storyboards/act2/panels/scene-21-panel-01.png", "tree-branch", "Parents on tree branch", "romantic"),
]


def smart_crop(img: Image.Image, target_size: tuple) -> Image.Image:
    """
    Smart crop an image to target size, focusing on center/subject.
    Uses cover-style cropping (fills entire frame, crops overflow).
    """
    target_w, target_h = target_size
    target_ratio = target_w / target_h

    img_w, img_h = img.size
    img_ratio = img_w / img_h

    if img_ratio > target_ratio:
        # Image is wider - crop sides
        new_w = int(img_h * target_ratio)
        left = (img_w - new_w) // 2
        box = (left, 0, left + new_w, img_h)
    else:
        # Image is taller - crop top/bottom
        new_h = int(img_w / target_ratio)
        top = (img_h - new_h) // 2
        box = (0, top, img_w, top + new_h)

    cropped = img.crop(box)
    return cropped.resize(target_size, Image.Resampling.LANCZOS)


def add_subtle_branding(img: Image.Image, text: str = "rexmarksthespot.com") -> Image.Image:
    """Add subtle watermark/branding to bottom right."""
    img = img.copy()
    draw = ImageDraw.Draw(img)

    # Try to load a font, fall back to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()

    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Position in bottom right with padding
    padding = 15
    x = img.width - text_w - padding
    y = img.height - text_h - padding

    # Draw shadow then text
    draw.text((x+1, y+1), text, fill=(0, 0, 0, 128), font=font)
    draw.text((x, y), text, fill=(255, 255, 255, 200), font=font)

    return img


def create_teaser_set(source_path: Path, name: str, description: str) -> dict:
    """Create a full set of social media images from a source panel."""
    results = {}

    # Open source image
    img = Image.open(source_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Create Twitter version (16:9)
    twitter_img = smart_crop(img, TWITTER_SIZE)
    twitter_img = add_subtle_branding(twitter_img)
    twitter_path = OUTPUT_DIR / "twitter" / f"{name}_twitter.jpg"
    twitter_img.save(twitter_path, "JPEG", quality=92)
    results['twitter'] = twitter_path

    # Create Instagram square (1:1)
    insta_square = smart_crop(img, INSTAGRAM_SQUARE)
    insta_square = add_subtle_branding(insta_square)
    square_path = OUTPUT_DIR / "instagram" / f"{name}_square.jpg"
    insta_square.save(square_path, "JPEG", quality=92)
    results['instagram_square'] = square_path

    # Create Instagram portrait (4:5) - best for feed
    insta_portrait = smart_crop(img, INSTAGRAM_PORTRAIT)
    insta_portrait = add_subtle_branding(insta_portrait)
    portrait_path = OUTPUT_DIR / "instagram" / f"{name}_portrait.jpg"
    insta_portrait.save(portrait_path, "JPEG", quality=92)
    results['instagram_portrait'] = portrait_path

    return results


def main():
    """Generate all social media teaser images."""
    print("Generating social media teaser images...")
    print(f"Output directory: {OUTPUT_DIR}")

    # Ensure output directories exist
    (OUTPUT_DIR / "twitter").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "instagram").mkdir(parents=True, exist_ok=True)

    generated = []

    for source_rel, name, description, category in BEST_PANELS:
        source_path = PROJECT_ROOT / source_rel

        if not source_path.exists():
            print(f"  SKIP: {source_rel} (file not found)")
            continue

        print(f"  Processing: {name} ({category})")
        try:
            results = create_teaser_set(source_path, name, description)
            generated.append({
                'name': name,
                'description': description,
                'category': category,
                'files': results
            })
            print(f"    -> Created {len(results)} versions")
        except Exception as e:
            print(f"    ERROR: {e}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Generated {len(generated)} teaser sets")
    print(f"Total files: {len(generated) * 3}")
    print(f"\nTwitter images: {OUTPUT_DIR / 'twitter'}")
    print(f"Instagram images: {OUTPUT_DIR / 'instagram'}")

    # Print files by category
    print("\nBy category:")
    categories = {}
    for item in generated:
        cat = item['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item['name'])

    for cat, names in categories.items():
        print(f"  {cat}: {', '.join(names)}")

    return generated


if __name__ == "__main__":
    main()
