#!/usr/bin/env python3
"""
Generate original music for Fairy Dinosaur Date Night using Meta's MusicGen.

This script generates .wav and .mp3 files for various movie themes using the
MusicGen model from Hugging Face.
"""

import os
import scipy.io.wavfile
from pathlib import Path

import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "audio" / "themes"

# Music themes for the movie - optimized for MusicGen
MOVIE_THEMES = {
    "main_theme": {
        "prompt": "orchestral adventure soundtrack, hopeful heroic theme with strings and french horns, whimsical family movie music, warm and uplifting, full orchestra",
        "duration_seconds": 30,
    },
    "adventure_music": {
        "prompt": "exciting orchestral adventure music, driving percussion, brass fanfares, epic journey theme, cinematic and triumphant, fantasy movie soundtrack",
        "duration_seconds": 30,
    },
    "emotional_moment": {
        "prompt": "emotional orchestral piece, gentle piano with soft strings, heartfelt and tender, touching family reunion music, hopeful resolution",
        "duration_seconds": 30,
    },
    "jetplane_theme": {
        "prompt": "playful quirky orchestral theme, comedic bassoon and clarinet, pizzicato strings, whimsical cartoon music, fun and silly character theme",
        "duration_seconds": 25,
    },
    "magic_theme": {
        "prompt": "magical ethereal music, celeste and music box, gentle sparkle sounds, fairy tale soundtrack, enchanting and mystical",
        "duration_seconds": 25,
    },
    "danger_chase": {
        "prompt": "intense chase music, pounding drums, suspenseful brass, action movie soundtrack, dinosaur attack theme, urgent and dramatic",
        "duration_seconds": 25,
    },
}


def generate_music_with_musicgen(model, processor, prompt: str, duration_seconds: int = 30) -> torch.Tensor:
    """Generate music using MusicGen model."""
    # Prepare inputs
    inputs = processor(
        text=[prompt],
        padding=True,
        return_tensors="pt",
    )

    # Move to GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Calculate max new tokens based on duration
    # MusicGen generates at ~50 tokens per second of audio
    max_new_tokens = int(duration_seconds * 50)

    print(f"  Generating {duration_seconds}s of audio ({max_new_tokens} tokens)...")

    # Generate
    with torch.no_grad():
        audio_values = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
        )

    return audio_values


def save_audio(audio_values: torch.Tensor, filepath: Path, sample_rate: int = 32000):
    """Save audio tensor as WAV file."""
    # Move to CPU and convert
    audio_np = audio_values[0, 0].cpu().numpy()

    # Normalize to prevent clipping
    audio_np = audio_np / max(abs(audio_np.max()), abs(audio_np.min()), 1e-6)

    # Convert to int16
    audio_int16 = (audio_np * 32767).astype('int16')

    # Save as WAV
    scipy.io.wavfile.write(str(filepath), sample_rate, audio_int16)
    print(f"  Saved: {filepath}")


def convert_wav_to_mp3(wav_path: Path) -> Path:
    """Convert WAV to MP3 using ffmpeg if available."""
    mp3_path = wav_path.with_suffix('.mp3')
    result = os.system(f'ffmpeg -y -i "{wav_path}" -codec:a libmp3lame -qscale:a 2 "{mp3_path}" 2>/dev/null')
    if result == 0 and mp3_path.exists():
        print(f"  Converted to: {mp3_path}")
        return mp3_path
    return None


def main():
    """Generate all music themes for the movie."""
    print("=" * 60)
    print("Fairy Dinosaur Date Night - MusicGen Music Generation")
    print("=" * 60)
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Check for GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Load model and processor
    print("Loading MusicGen model (facebook/musicgen-small)...")
    print("This may take a few minutes on first run...")

    processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
    model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
    model = model.to(device)

    sample_rate = model.config.audio_encoder.sampling_rate
    print(f"Model loaded! Sample rate: {sample_rate}Hz")
    print()

    # Generate each theme
    generated_files = []

    for theme_name, config in MOVIE_THEMES.items():
        print(f"[{theme_name}]")
        print(f"  Prompt: {config['prompt'][:50]}...")

        try:
            # Generate audio
            audio_values = generate_music_with_musicgen(
                model,
                processor,
                config["prompt"],
                config["duration_seconds"]
            )

            # Save as WAV
            wav_path = OUTPUT_DIR / f"{theme_name}.wav"
            save_audio(audio_values, wav_path, sample_rate)
            generated_files.append(wav_path)

            # Try to convert to MP3
            mp3_path = convert_wav_to_mp3(wav_path)
            if mp3_path:
                generated_files.append(mp3_path)

            print(f"  SUCCESS!")

        except Exception as e:
            print(f"  ERROR: {e}")

        print()

    print("=" * 60)
    print("Music generation complete!")
    print(f"Generated {len(generated_files)} files:")
    for f in generated_files:
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")
    print("=" * 60)


if __name__ == "__main__":
    main()
