#!/usr/bin/env python3
"""
Generate synthesized music for Fairy Dinosaur Date Night using scipy/numpy.

This creates actual audio files without needing external APIs.
"""

import numpy as np
from scipy.io import wavfile
from pathlib import Path

# Configuration
SAMPLE_RATE = 44100
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "audio" / "music"

# Musical notes (frequencies in Hz)
NOTES = {
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50,
    # Sharps/flats
    'Bb3': 233.08, 'Eb4': 311.13, 'Ab4': 415.30, 'Bb4': 466.16, 'Eb5': 622.25,
    'F#4': 369.99, 'F#5': 739.99,
}


def generate_tone(freq, duration, sample_rate=SAMPLE_RATE):
    """Generate a pure sine wave tone."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sin(2 * np.pi * freq * t)


def generate_rich_tone(freq, duration, sample_rate=SAMPLE_RATE, harmonics=None):
    """Generate a tone with harmonics for richer sound."""
    if harmonics is None:
        harmonics = [(1.0, 1.0), (0.5, 2.0), (0.25, 3.0), (0.125, 4.0)]

    t = np.linspace(0, duration, int(sample_rate * duration), False)
    signal = np.zeros_like(t)

    for amplitude, harmonic in harmonics:
        signal += amplitude * np.sin(2 * np.pi * freq * harmonic * t)

    return signal / np.max(np.abs(signal) + 0.001)


def apply_envelope(signal, attack=0.05, decay=0.1, sustain=0.7, release=0.2):
    """Apply ADSR envelope to a signal."""
    length = len(signal)
    envelope = np.ones(length)

    attack_samples = int(attack * length)
    decay_samples = int(decay * length)
    release_samples = int(release * length)
    sustain_samples = length - attack_samples - decay_samples - release_samples

    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

    if decay_samples > 0:
        start = attack_samples
        envelope[start:start + decay_samples] = np.linspace(1, sustain, decay_samples)

    if sustain_samples > 0:
        start = attack_samples + decay_samples
        envelope[start:start + sustain_samples] = sustain

    if release_samples > 0:
        start = length - release_samples
        envelope[start:] = np.linspace(sustain, 0, release_samples)

    return signal * envelope


def play_note(note, duration, volume=0.5, rich=True):
    """Generate a musical note with envelope."""
    freq = NOTES.get(note, 440)

    if rich:
        signal = generate_rich_tone(freq, duration)
    else:
        signal = generate_tone(freq, duration)

    signal = apply_envelope(signal, attack=0.02, decay=0.1, sustain=0.6, release=0.15)
    return signal * volume


def play_chord(notes, duration, volume=0.4):
    """Generate a chord from multiple notes."""
    chord = np.zeros(int(SAMPLE_RATE * duration))
    for note in notes:
        chord += play_note(note, duration, volume / len(notes), rich=True)
    return chord


def add_reverb(signal, decay=0.3, delay_ms=50):
    """Add simple reverb effect."""
    delay_samples = int(SAMPLE_RATE * delay_ms / 1000)
    output = signal.copy()

    for i in range(1, 5):
        delayed = np.zeros_like(signal)
        offset = delay_samples * i
        if offset < len(signal):
            delayed[offset:] = signal[:-offset] * (decay ** i)
            output += delayed

    return output / np.max(np.abs(output) + 0.001)


def generate_main_theme():
    """Generate the main theme - hopeful, orchestral adventure feel."""
    print("Generating main_theme.wav...")

    # Main melody (30 seconds)
    melody_notes = [
        ('C4', 0.5), ('E4', 0.5), ('G4', 0.75), ('C5', 0.75),
        ('B4', 0.5), ('G4', 0.5), ('E4', 0.5), ('G4', 1.0),
        ('A4', 0.5), ('G4', 0.5), ('F4', 0.5), ('E4', 0.5),
        ('D4', 0.75), ('E4', 0.25), ('F4', 0.5), ('G4', 1.0),

        ('C4', 0.5), ('E4', 0.5), ('G4', 0.75), ('C5', 0.75),
        ('D5', 0.5), ('E5', 0.5), ('D5', 0.5), ('C5', 1.0),
        ('B4', 0.5), ('A4', 0.5), ('G4', 0.5), ('F4', 0.5),
        ('E4', 0.75), ('D4', 0.25), ('C4', 1.5),
    ]

    # Bass line
    bass_notes = [
        ('C3', 2.0), ('G3', 2.0), ('A3', 2.0), ('G3', 2.0),
        ('C3', 2.0), ('G3', 2.0), ('F3', 2.0), ('C3', 2.0),
    ]

    # Build melody track
    melody = []
    for note, dur in melody_notes:
        melody.append(play_note(note, dur, volume=0.6))
    melody = np.concatenate(melody)

    # Build bass track
    bass = []
    for note, dur in bass_notes:
        bass.append(play_note(note, dur, volume=0.35, rich=True))
    bass = np.concatenate(bass)

    # Pad to match lengths
    max_len = max(len(melody), len(bass))
    melody = np.pad(melody, (0, max_len - len(melody)))
    bass = np.pad(bass, (0, max_len - len(bass)))

    # Add chords
    chord_progression = [
        (['C4', 'E4', 'G4'], 2.0),
        (['G3', 'B3', 'D4'], 2.0),
        (['A3', 'C4', 'E4'], 2.0),
        (['G3', 'B3', 'D4'], 2.0),
        (['C4', 'E4', 'G4'], 2.0),
        (['G3', 'B3', 'D4'], 2.0),
        (['F3', 'A3', 'C4'], 2.0),
        (['C4', 'E4', 'G4'], 2.0),
    ]

    chords = []
    for notes, dur in chord_progression:
        chords.append(play_chord(notes, dur, volume=0.3))
    chords = np.concatenate(chords)
    chords = np.pad(chords, (0, max_len - len(chords)))

    # Mix tracks
    mix = melody * 0.5 + bass * 0.25 + chords * 0.25

    # Loop to make it longer (30 seconds total)
    target_samples = SAMPLE_RATE * 30
    loops_needed = int(np.ceil(target_samples / len(mix)))
    mix = np.tile(mix, loops_needed)[:target_samples]

    # Add reverb
    mix = add_reverb(mix, decay=0.25)

    # Fade in/out
    fade_samples = SAMPLE_RATE
    mix[:fade_samples] *= np.linspace(0, 1, fade_samples)
    mix[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    return mix


def generate_adventure_music():
    """Generate adventure/action music - faster, more exciting."""
    print("Generating adventure_music.wav...")

    # Fast-paced melody
    melody_notes = [
        ('E4', 0.25), ('G4', 0.25), ('A4', 0.25), ('B4', 0.25),
        ('C5', 0.5), ('B4', 0.25), ('A4', 0.25),
        ('G4', 0.25), ('A4', 0.25), ('B4', 0.25), ('C5', 0.25),
        ('D5', 0.5), ('C5', 0.25), ('B4', 0.25),

        ('E5', 0.5), ('D5', 0.25), ('C5', 0.25),
        ('B4', 0.5), ('A4', 0.25), ('G4', 0.25),
        ('A4', 0.25), ('B4', 0.25), ('C5', 0.25), ('D5', 0.25),
        ('E5', 1.0),

        ('E4', 0.25), ('G4', 0.25), ('A4', 0.25), ('B4', 0.25),
        ('C5', 0.5), ('D5', 0.25), ('E5', 0.25),
        ('D5', 0.25), ('C5', 0.25), ('B4', 0.25), ('A4', 0.25),
        ('G4', 1.0),
    ]

    # Driving bass
    bass_notes = [
        ('E3', 0.25), ('E3', 0.25), ('E3', 0.25), ('E3', 0.25),
        ('A3', 0.25), ('A3', 0.25), ('A3', 0.25), ('A3', 0.25),
        ('G3', 0.25), ('G3', 0.25), ('G3', 0.25), ('G3', 0.25),
        ('D3', 0.25), ('D3', 0.25), ('D3', 0.25), ('D3', 0.25),
    ] * 3

    melody = []
    for note, dur in melody_notes:
        melody.append(play_note(note, dur, volume=0.65))
    melody = np.concatenate(melody)

    bass = []
    for note, dur in bass_notes:
        bass.append(play_note(note, dur, volume=0.4, rich=True))
    bass = np.concatenate(bass)

    # Percussion-like hits (using very short, punchy notes)
    perc_pattern = [0.25] * 32
    perc = []
    for dur in perc_pattern:
        hit = generate_tone(80, dur) * 0.3
        hit = apply_envelope(hit, attack=0.01, decay=0.1, sustain=0.1, release=0.1)
        perc.append(hit)
    perc = np.concatenate(perc)

    # Pad to match
    max_len = max(len(melody), len(bass), len(perc))
    melody = np.pad(melody, (0, max_len - len(melody)))
    bass = np.pad(bass, (0, max_len - len(bass)))
    perc = np.pad(perc, (0, max_len - len(perc)))

    mix = melody * 0.45 + bass * 0.35 + perc * 0.2

    # Loop to 30 seconds
    target_samples = SAMPLE_RATE * 30
    loops_needed = int(np.ceil(target_samples / len(mix)))
    mix = np.tile(mix, loops_needed)[:target_samples]

    mix = add_reverb(mix, decay=0.2, delay_ms=30)

    # Fade in/out
    fade_samples = int(SAMPLE_RATE * 0.5)
    mix[:fade_samples] *= np.linspace(0, 1, fade_samples)
    mix[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    return mix


def generate_emotional_moment():
    """Generate emotional/tender music - slower, more gentle."""
    print("Generating emotional_moment.wav...")

    # Slow, gentle melody
    melody_notes = [
        ('E4', 1.0), ('G4', 0.5), ('A4', 0.5),
        ('B4', 1.5), ('A4', 0.5),
        ('G4', 1.0), ('E4', 0.5), ('D4', 0.5),
        ('E4', 2.0),

        ('A4', 1.0), ('B4', 0.5), ('C5', 0.5),
        ('D5', 1.5), ('C5', 0.5),
        ('B4', 1.0), ('A4', 0.5), ('G4', 0.5),
        ('A4', 2.0),

        ('E5', 1.5), ('D5', 0.5),
        ('C5', 1.0), ('B4', 1.0),
        ('A4', 1.0), ('G4', 0.5), ('F4', 0.5),
        ('E4', 2.0),
    ]

    # Gentle arpeggios
    arp_notes = [
        ('C4', 0.5), ('E4', 0.5), ('G4', 0.5), ('C5', 0.5),
        ('A3', 0.5), ('C4', 0.5), ('E4', 0.5), ('A4', 0.5),
        ('G3', 0.5), ('B3', 0.5), ('D4', 0.5), ('G4', 0.5),
        ('C4', 0.5), ('E4', 0.5), ('G4', 0.5), ('C5', 0.5),
    ] * 3

    melody = []
    for note, dur in melody_notes:
        tone = play_note(note, dur, volume=0.55)
        melody.append(tone)
    melody = np.concatenate(melody)

    arp = []
    for note, dur in arp_notes:
        tone = play_note(note, dur, volume=0.3, rich=True)
        arp.append(tone)
    arp = np.concatenate(arp)

    # Pad chords
    pad_chords = [
        (['C4', 'E4', 'G4'], 4.0),
        (['A3', 'C4', 'E4'], 4.0),
        (['G3', 'B3', 'D4'], 4.0),
        (['C4', 'E4', 'G4'], 4.0),
    ]

    pads = []
    for notes, dur in pad_chords:
        chord = play_chord(notes, dur, volume=0.2)
        chord = apply_envelope(chord, attack=0.3, decay=0.1, sustain=0.5, release=0.3)
        pads.append(chord)
    pads = np.concatenate(pads)

    # Match lengths
    max_len = max(len(melody), len(arp), len(pads))
    melody = np.pad(melody, (0, max_len - len(melody)))
    arp = np.pad(arp, (0, max_len - len(arp)))
    pads = np.pad(pads, (0, max_len - len(pads)))

    mix = melody * 0.45 + arp * 0.3 + pads * 0.25

    # Loop to 30 seconds
    target_samples = SAMPLE_RATE * 30
    loops_needed = int(np.ceil(target_samples / len(mix)))
    mix = np.tile(mix, loops_needed)[:target_samples]

    # More reverb for emotional feel
    mix = add_reverb(mix, decay=0.35, delay_ms=70)

    # Gentle fade in/out
    fade_samples = int(SAMPLE_RATE * 1.5)
    mix[:fade_samples] *= np.linspace(0, 1, fade_samples)
    mix[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    return mix


def normalize_and_save(audio, filename):
    """Normalize audio and save as WAV file."""
    # Normalize to prevent clipping
    audio = audio / (np.max(np.abs(audio)) + 0.001)

    # Convert to 16-bit PCM
    audio_16bit = (audio * 32767).astype(np.int16)

    # Save
    filepath = OUTPUT_DIR / filename
    wavfile.write(filepath, SAMPLE_RATE, audio_16bit)
    print(f"  Saved: {filepath} ({len(audio_16bit) / SAMPLE_RATE:.1f} seconds)")


def main():
    """Generate all music tracks."""
    print("=" * 60)
    print("Fairy Dinosaur Date Night - Synthesized Music Generation")
    print("=" * 60)
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate each track
    tracks = [
        (generate_main_theme, "main_theme.wav"),
        (generate_adventure_music, "adventure_music.wav"),
        (generate_emotional_moment, "emotional_moment.wav"),
    ]

    for generator, filename in tracks:
        audio = generator()
        normalize_and_save(audio, filename)
        print()

    print("=" * 60)
    print("Music generation complete!")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
