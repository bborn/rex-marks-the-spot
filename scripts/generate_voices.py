#!/usr/bin/env python3
"""
Generate character voice samples for Fairy Dinosaur Date Night using ElevenLabs.
Creates actual .mp3 files for each character.
"""

import os
import sys
from pathlib import Path
from elevenlabs import ElevenLabs, VoiceSettings

# Get API key from environment
API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not API_KEY:
    print("ERROR: ELEVENLABS_API_KEY environment variable not set")
    print("Please set it with: export ELEVENLABS_API_KEY='your-key-here'")
    sys.exit(1)

client = ElevenLabs(api_key=API_KEY)

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "audio" / "voices"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Character voice configurations
# Using ElevenLabs pre-made voices that match character profiles
CHARACTERS = {
    "gabe": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam - deep male, authoritative
        "settings": VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.3,
            use_speaker_boost=True
        ),
        "lines": [
            "We'll be back by eleven. Midnight. No later.",
            "Promise?",
            "I'm going to get us killed?! What about them!?",
            "Leo! You were amazing! Way to go!",
            "Kids! Breakfast! I told them I couldn't make it. Promised Mia we'd go to the lizard shop.",
        ]
    },
    "nina": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Sarah - warm female, intelligent
        "settings": VoiceSettings(
            stability=0.6,
            similarity_boost=0.8,
            style=0.4,
            use_speaker_boost=True
        ),
        "lines": [
            "So there's chicken nuggets in the freezer, corn dogs, they can have anything you want.",
            "You weren't nice to her. You're too hard on her.",
            "It was a time warp!",
            "I want us to stop working so much. Take a road trip. Travel more.",
            "They're OK!!!",
        ]
    },
    "mia": {
        "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica - Playful, Bright, Warm (young girl)
        "settings": VoiceSettings(
            stability=0.5,
            similarity_boost=0.7,
            style=0.6,  # Slightly expressive for 8-year-old
            use_speaker_boost=True
        ),
        "lines": [
            "Will you be back for bedtime?",
            "Promise?",
            "It was the storm. That storm did something with them. I know it.",
            "We're coming to save you!",
            "I promise, dad.",
        ]
    },
    "leo": {
        "voice_id": "N2lVS1w4EtoT3dr4eOWO",  # Callum - Husky Trickster (characters/animation)
        "settings": VoiceSettings(
            stability=0.35,
            similarity_boost=0.6,
            style=0.8,  # Very expressive for energetic 5-year-old
            use_speaker_boost=True
        ),
        "lines": [
            "I don't want to go to bed!",
            "I drove a police car! We crashed into a tree!",
            "His name is... JETPLANE!",
            "He farts colors!",
            "Mommy! Momma!!!!",
        ]
    },
    "ruben": {
        "voice_id": "onwK4e9ZLuTAKqWW03F9",  # Daniel - mature, world-weary
        "settings": VoiceSettings(
            stability=0.4,
            similarity_boost=0.7,
            style=0.5,
            use_speaker_boost=True
        ),
        "lines": [
            "I'm forty-nine, ok!? I'm not really a janitor, ok!",
            "I'm your fairy godfather.",
            "I'm kind of... on the fairy naughty list.",
            "We don't have much time.",
            "Blippity goop! Slippity doob! Rugula vorsteen, frabula jin!",
        ]
    },
}


def list_available_voices():
    """List all available voices to help find the best matches."""
    print("Fetching available voices...")
    response = client.voices.get_all()
    print("\nAvailable voices:")
    for voice in response.voices:
        print(f"  - {voice.name}: {voice.voice_id} ({voice.labels})")
    return response.voices


def generate_character_voice(character_name: str, config: dict):
    """Generate voice samples for a single character."""
    char_dir = OUTPUT_DIR / character_name
    char_dir.mkdir(exist_ok=True)

    print(f"\n=== Generating voice for {character_name.upper()} ===")

    for i, line in enumerate(config["lines"], 1):
        output_file = char_dir / f"{character_name}_{i:02d}.mp3"
        print(f"  [{i}/{len(config['lines'])}] Generating: {line[:50]}...")

        try:
            audio = client.text_to_speech.convert(
                voice_id=config["voice_id"],
                text=line,
                model_id="eleven_multilingual_v2",
                voice_settings=config["settings"]
            )

            # Write the audio to file
            with open(output_file, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            print(f"       Saved: {output_file}")
        except Exception as e:
            print(f"       ERROR: {e}")

    print(f"  Done! Files saved to {char_dir}/")


def main():
    print("=" * 60)
    print("Fairy Dinosaur Date Night - Character Voice Generation")
    print("=" * 60)

    # First list available voices so we can verify/adjust
    if "--list-voices" in sys.argv:
        list_available_voices()
        return

    # Generate for specific character or all
    if len(sys.argv) > 1 and sys.argv[1] != "--list-voices":
        char = sys.argv[1].lower()
        if char in CHARACTERS:
            generate_character_voice(char, CHARACTERS[char])
        else:
            print(f"Unknown character: {char}")
            print(f"Available: {', '.join(CHARACTERS.keys())}")
    else:
        # Generate all characters
        for char_name, config in CHARACTERS.items():
            generate_character_voice(char_name, config)

    print("\n" + "=" * 60)
    print("Voice generation complete!")
    print(f"Audio files saved to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
