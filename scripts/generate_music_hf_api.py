#!/usr/bin/env python3
"""
Generate original music for Fairy Dinosaur Date Night using Hugging Face Inference API.

This uses the hosted MusicGen model to avoid local memory issues.
"""

import os
import requests
import time
from pathlib import Path

# Configuration
HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "audio" / "themes"
API_URL = "https://router.huggingface.co/hf-inference/models/facebook/musicgen-small"

# Music themes for the movie
MOVIE_THEMES = {
    "main_theme": {
        "prompt": "orchestral adventure soundtrack, hopeful heroic theme with strings and french horns, whimsical family movie music, warm and uplifting, full orchestra, cinematic",
    },
    "adventure_music": {
        "prompt": "exciting orchestral adventure music, driving percussion, brass fanfares, epic journey theme, cinematic and triumphant, fantasy movie soundtrack, action",
    },
    "emotional_moment": {
        "prompt": "emotional orchestral piece, gentle piano with soft strings, heartfelt and tender, touching family reunion music, hopeful resolution, cinematic",
    },
}


def query_musicgen(prompt: str, max_retries: int = 5) -> bytes:
    """Query the MusicGen model via Hugging Face Inference API."""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt}

    for attempt in range(max_retries):
        print(f"    Attempt {attempt + 1}/{max_retries}...")

        response = requests.post(API_URL, headers=headers, json=payload, timeout=300)

        if response.status_code == 200:
            return response.content
        elif response.status_code == 503:
            # Model is loading
            try:
                wait_time = response.json().get("estimated_time", 30)
                print(f"    Model loading, waiting {wait_time:.0f}s...")
                time.sleep(min(wait_time, 60))
            except:
                time.sleep(30)
        else:
            print(f"    Error {response.status_code}: {response.text[:200]}")
            if attempt < max_retries - 1:
                time.sleep(10)

    return None


def main():
    """Generate all music themes for the movie."""
    if not HF_TOKEN:
        print("ERROR: HF_TOKEN or HUGGING_FACE_HUB_TOKEN environment variable not set")
        return

    print("=" * 60)
    print("Fairy Dinosaur Date Night - HF Inference API Music Generation")
    print("=" * 60)
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Generate each theme
    generated_files = []

    for theme_name, config in MOVIE_THEMES.items():
        print(f"[{theme_name}]")
        print(f"  Prompt: {config['prompt'][:60]}...")

        try:
            # Generate audio via API
            audio_data = query_musicgen(config["prompt"])

            if audio_data and len(audio_data) > 1000:
                # The API returns FLAC audio, save it
                flac_path = OUTPUT_DIR / f"{theme_name}.flac"
                with open(flac_path, "wb") as f:
                    f.write(audio_data)
                print(f"  Saved: {flac_path} ({len(audio_data)/1024:.1f} KB)")
                generated_files.append(flac_path)

                # Convert to MP3
                mp3_path = OUTPUT_DIR / f"{theme_name}.mp3"
                result = os.system(f'ffmpeg -y -i "{flac_path}" -codec:a libmp3lame -qscale:a 2 "{mp3_path}" 2>/dev/null')
                if result == 0 and mp3_path.exists():
                    print(f"  Converted: {mp3_path}")
                    generated_files.append(mp3_path)

                print(f"  SUCCESS!")
            else:
                print(f"  WARNING: No audio data received or too small")

        except Exception as e:
            print(f"  ERROR: {e}")

        print()

    print("=" * 60)
    print("Music generation complete!")
    print(f"Generated {len(generated_files)} files:")
    for f in generated_files:
        if f.exists():
            size_kb = f.stat().st_size / 1024
            print(f"  - {f.name} ({size_kb:.1f} KB)")
    print("=" * 60)


if __name__ == "__main__":
    main()
