#!/usr/bin/env python3
"""
Generate original music for Fairy Dinosaur Date Night using Gemini Lyria RealTime.

This script generates .wav files for various movie themes using the Gemini API.
"""

import asyncio
import os
import wave
import struct
from pathlib import Path
from typing import Optional

from google import genai

# Configuration
API_KEY = os.environ.get("GEMINI_API_KEY")
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "audio"

# Music themes for the movie
MOVIE_THEMES = {
    "main_theme": {
        "prompt": "orchestral adventure theme, hopeful and brave, string melody with woodwind countermelody, french horn heroic moments, light percussion driving feel, family movie soundtrack, whimsical and warm",
        "bpm": 120,
        "duration_seconds": 60,
        "brightness": 0.7,
        "density": 0.6,
    },
    "jetplane_theme": {
        "prompt": "quirky comedic orchestral theme, playful bassoon and clarinet, pizzicato strings, whimsical percussion, cartoon comedy music, silly and fun, dinosaur character theme",
        "bpm": 130,
        "duration_seconds": 45,
        "brightness": 0.8,
        "density": 0.5,
    },
    "ruben_fairy_theme": {
        "prompt": "magical ethereal theme, celeste and music box, gentle strings pizzicato, sparkle sounds, slightly melancholic undertone, fairy godfather character, magical but rusty, nostalgic",
        "bpm": 80,
        "duration_seconds": 45,
        "brightness": 0.6,
        "density": 0.4,
    },
    "time_warp_theme": {
        "prompt": "tense otherworldly theme, synthesizer pads, low brass, building tension, time travel portal music, mysterious and suspenseful, ethereal drone",
        "bpm": 90,
        "duration_seconds": 30,
        "brightness": 0.3,
        "density": 0.5,
    },
    "danger_chase": {
        "prompt": "intense chase music, pounding percussion, low brass trombone tuba, primal dread, dinosaur attack, suspenseful action, timpani and dramatic strings",
        "bpm": 150,
        "duration_seconds": 45,
        "brightness": 0.4,
        "density": 0.8,
    },
    "family_reunion": {
        "prompt": "emotional orchestral crescendo, warm strings, triumphant brass, heartfelt reunion theme, family movie climax, hopeful and joyful resolution, full orchestra",
        "bpm": 100,
        "duration_seconds": 60,
        "brightness": 0.7,
        "density": 0.7,
    },
}


async def generate_music_track(
    session,
    theme_name: str,
    prompt: str,
    bpm: int = 120,
    duration_seconds: int = 30,
    brightness: float = 0.5,
    density: float = 0.5,
) -> bytes:
    """Generate a music track using Lyria RealTime."""
    print(f"  Generating '{theme_name}'...")
    print(f"    Prompt: {prompt[:60]}...")
    print(f"    BPM: {bpm}, Duration: {duration_seconds}s")

    audio_chunks = []

    # Configure the generation
    await session.set_weighted_prompts(
        prompts=[{"text": prompt, "weight": 1.0}]
    )
    await session.set_music_generation_config(
        config={
            "bpm": bpm,
            "temperature": 1.0,
            "brightness": brightness,
            "density": density,
            "guidance": 4.0,
        }
    )

    # Start playback and collect audio
    await session.play()

    # Calculate expected samples (48kHz stereo)
    expected_samples = duration_seconds * 48000 * 2 * 2  # 48kHz * stereo * 16-bit
    collected_bytes = 0

    try:
        async for response in session.receive():
            if hasattr(response, 'server_content') and response.server_content:
                if hasattr(response.server_content, 'audio_chunks'):
                    for chunk in response.server_content.audio_chunks:
                        if hasattr(chunk, 'data'):
                            audio_chunks.append(chunk.data)
                            collected_bytes += len(chunk.data)

            # Check if we've collected enough
            if collected_bytes >= expected_samples:
                break

    except asyncio.TimeoutError:
        print(f"    Timeout after collecting {collected_bytes} bytes")

    await session.pause()

    return b''.join(audio_chunks)


def save_wav(audio_data: bytes, filepath: Path):
    """Save raw PCM audio data as WAV file (48kHz, 16-bit stereo)."""
    with wave.open(str(filepath), 'wb') as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(48000)  # 48kHz
        wav_file.writeframes(audio_data)
    print(f"    Saved: {filepath}")


async def main():
    """Generate all music themes for the movie."""
    if not API_KEY:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        return

    print("=" * 60)
    print("Fairy Dinosaur Date Night - Music Generation")
    print("=" * 60)
    print()

    # Create output directories
    themes_dir = OUTPUT_DIR / "themes"
    themes_dir.mkdir(parents=True, exist_ok=True)

    # Initialize client
    client = genai.Client(
        api_key=API_KEY,
        http_options={'api_version': 'v1alpha'}
    )

    print(f"Connecting to Lyria RealTime model...")

    try:
        async with client.aio.live.music.connect(
            model='models/lyria-realtime-exp'
        ) as session:
            print("Connected successfully!")
            print()

            for theme_name, config in MOVIE_THEMES.items():
                print(f"[{theme_name}]")

                try:
                    audio_data = await generate_music_track(
                        session,
                        theme_name,
                        config["prompt"],
                        bpm=config["bpm"],
                        duration_seconds=config["duration_seconds"],
                        brightness=config.get("brightness", 0.5),
                        density=config.get("density", 0.5),
                    )

                    if audio_data:
                        output_path = themes_dir / f"{theme_name}.wav"
                        save_wav(audio_data, output_path)
                        print(f"    SUCCESS: Generated {len(audio_data)} bytes")
                    else:
                        print(f"    WARNING: No audio data received")

                    # Reset context between tracks
                    await session.reset_context()

                except Exception as e:
                    print(f"    ERROR: {e}")

                print()

        print("=" * 60)
        print("Music generation complete!")
        print(f"Output directory: {themes_dir}")
        print("=" * 60)

    except Exception as e:
        print(f"Connection error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
