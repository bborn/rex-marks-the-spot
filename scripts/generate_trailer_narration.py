#!/usr/bin/env python3
"""
Generate trailer narration using ElevenLabs API.

Generates a warm, enthusiastic narration for the trailer intro.
Uses the Sarah voice (warm female) for family-friendly tone.
"""

import os
import sys
from pathlib import Path

try:
    from elevenlabs import ElevenLabs, VoiceSettings
except ImportError:
    print("ERROR: elevenlabs package not installed.")
    print("Install with: pip install elevenlabs")
    sys.exit(1)

# Get API key
API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not API_KEY:
    print("ERROR: ELEVENLABS_API_KEY environment variable not set")
    sys.exit(1)

client = ElevenLabs(api_key=API_KEY)

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Narration configuration
NARRATION_LINES = [
    {
        "id": "trailer-narration",
        "text": "What happens when a simple date night... becomes a Jurassic adventure? "
                "Meet the family behind Fairy Dinosaur Date Night — "
                "an animated movie made entirely with AI.",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Sarah - warm, family-friendly
        "settings": VoiceSettings(
            stability=0.65,
            similarity_boost=0.8,
            style=0.35,
            use_speaker_boost=True,
        ),
    },
]


def main():
    print("=" * 60)
    print("Trailer Narration Generation (ElevenLabs)")
    print("=" * 60)

    for line in NARRATION_LINES:
        output_file = OUTPUT_DIR / f"{line['id']}.mp3"
        print(f"\nGenerating: {line['id']}")
        print(f"  Text: {line['text'][:80]}...")
        print(f"  Voice: Sarah (warm, family-friendly)")

        try:
            audio = client.text_to_speech.convert(
                voice_id=line["voice_id"],
                text=line["text"],
                model_id="eleven_multilingual_v2",
                voice_settings=line["settings"],
            )

            with open(output_file, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            print(f"  Saved: {output_file}")
            size_kb = output_file.stat().st_size / 1024
            print(f"  Size: {size_kb:.1f} KB")

        except Exception as e:
            print(f"  ERROR: {e}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("Narration generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
