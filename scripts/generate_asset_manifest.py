#!/usr/bin/env python3
"""
Generate a JSON manifest of all R2 assets for the WIP page.

This creates a manifest.json file that lists all media assets in R2 with
their paths, sizes, modification times, and categories for easy display.

Usage:
  python3 generate_asset_manifest.py                    # Upload to R2
  python3 generate_asset_manifest.py --output FILE      # Save to local file
  python3 generate_asset_manifest.py --output docs/manifest.json  # For GitHub Pages
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

R2_BUCKET = "r2:rex-assets"
R2_PUBLIC_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev"

# Media file extensions to include
MEDIA_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
    '.mp4', '.mov', '.webm', '.avi',
    '.mp3', '.wav', '.ogg', '.m4a',
    '.glb', '.gltf', '.fbx', '.obj', '.blend'
}

# Category mapping based on path patterns
CATEGORY_PATTERNS = [
    ('storyboards/', 'Storyboards'),
    ('characters/', 'Characters'),
    ('assets/characters/', 'Characters'),
    ('assets/creatures/', 'Creatures'),
    ('assets/environments/', 'Environments'),
    ('assets/branding/', 'Branding'),
    ('assets/audio/', 'Audio'),
    ('assets/props/', 'Props'),
    ('animatics/', 'Animatics'),
    ('renders/', 'Renders'),
]


def get_category(path: str) -> str:
    """Determine the category based on file path."""
    path_lower = path.lower()
    for pattern, category in CATEGORY_PATTERNS:
        if pattern in path_lower:
            return category
    return 'Other'


def get_asset_type(path: str) -> str:
    """Determine asset type from extension."""
    ext = Path(path).suffix.lower()
    if ext in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}:
        return 'image'
    elif ext in {'.mp4', '.mov', '.webm', '.avi'}:
        return 'video'
    elif ext in {'.mp3', '.wav', '.ogg', '.m4a'}:
        return 'audio'
    elif ext in {'.glb', '.gltf', '.fbx', '.obj', '.blend'}:
        return '3d'
    return 'other'


def is_media_file(path: str) -> bool:
    """Check if file is a media file we want to display."""
    return Path(path).suffix.lower() in MEDIA_EXTENSIONS


def run_rclone_lsjson():
    """Get JSON listing of all files in R2 bucket."""
    result = subprocess.run(
        ['rclone', 'lsjson', R2_BUCKET, '--recursive'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error running rclone: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def generate_manifest():
    """Generate the asset manifest."""
    print("Fetching file list from R2...")
    files = run_rclone_lsjson()

    # Filter to media files only
    media_files = [f for f in files if is_media_file(f['Path'])]

    print(f"Found {len(media_files)} media files out of {len(files)} total files")

    # Transform to our manifest format
    assets = []
    for f in media_files:
        path = f['Path']
        assets.append({
            'path': path,
            'name': f['Name'],
            'url': f"{R2_PUBLIC_URL}/{path}",
            'size': f['Size'],
            'modTime': f['ModTime'],
            'category': get_category(path),
            'type': get_asset_type(path),
        })

    # Sort by modification time (newest first)
    assets.sort(key=lambda x: x['modTime'], reverse=True)

    # Group by category for summary
    categories = {}
    for asset in assets:
        cat = asset['category']
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1

    manifest = {
        'generated': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'totalAssets': len(assets),
        'categories': categories,
        'assets': assets,
    }

    return manifest


def upload_manifest(manifest: dict):
    """Upload manifest to R2."""
    # Write to temp file
    temp_file = Path('/tmp/manifest.json')
    with open(temp_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Uploading manifest to R2...")
    result = subprocess.run(
        ['rclone', 'copy', str(temp_file), R2_BUCKET + '/'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error uploading manifest: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"Manifest uploaded to {R2_PUBLIC_URL}/manifest.json")


def save_manifest_local(manifest: dict, output_path: str):
    """Save manifest to a local file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate R2 asset manifest')
    parser.add_argument('--output', '-o', help='Save to local file instead of uploading to R2')
    args = parser.parse_args()

    manifest = generate_manifest()

    # Print summary
    print(f"\nManifest Summary:")
    print(f"  Total assets: {manifest['totalAssets']}")
    print(f"  Categories:")
    for cat, count in sorted(manifest['categories'].items()):
        print(f"    {cat}: {count}")

    if args.output:
        # Save locally (for GitHub Pages)
        save_manifest_local(manifest, args.output)
    else:
        # Upload to R2
        upload_manifest(manifest)

    print("\nDone!")


if __name__ == '__main__':
    main()
