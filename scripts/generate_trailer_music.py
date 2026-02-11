#!/usr/bin/env python3
"""
Generate a 45-second trailer music track for Fairy Dinosaur Date Night.

Follows the trailer-audio-plan.md mood progression:
  0-4s:   Warm, inviting (piano/strings)
  4-8s:   Magical swell (shimmer, bells, crescendo)
  8-18s:  Playful adventure theme (pizzicato strings, light percussion)
  18-24s: Dramatic tension build (deeper brass, timpani hit)
  24-30s: Techy/futuristic underlay (synth arps, electronic pulse)
  30-39s: Building energy, combining orchestral + electronic
  39-45s: Resolving finale with big hit on "SUBSCRIBE" beat

Output: WAV 48kHz 16-bit (per audio plan spec) + MP3 via ffmpeg
"""

import numpy as np
from scipy.io import wavfile
from pathlib import Path
import subprocess
import sys

SAMPLE_RATE = 48000  # 48kHz per audio plan spec
DURATION = 45  # seconds
TOTAL_SAMPLES = SAMPLE_RATE * DURATION
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "audio"

# Note frequencies (Hz)
NOTES = {
    'C2': 65.41, 'D2': 73.42, 'E2': 82.41, 'F2': 87.31, 'G2': 98.00, 'A2': 110.00, 'B2': 123.47,
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50, 'D6': 1174.66, 'E6': 1318.51,
    'Bb3': 233.08, 'Eb4': 311.13, 'Ab4': 415.30, 'Bb4': 466.16,
    'F#4': 369.99, 'F#5': 739.99, 'G#4': 415.30, 'G#5': 830.61,
}


def time_to_samples(t):
    """Convert seconds to sample count."""
    return int(t * SAMPLE_RATE)


def generate_tone(freq, duration_s, harmonics=None):
    """Generate a tone with optional harmonics."""
    n = time_to_samples(duration_s)
    t = np.linspace(0, duration_s, n, False)
    if harmonics is None:
        harmonics = [(1.0, 1.0), (0.3, 2.0), (0.15, 3.0), (0.07, 4.0)]
    signal = np.zeros(n)
    for amp, h in harmonics:
        signal += amp * np.sin(2 * np.pi * freq * h * t)
    return signal / (np.max(np.abs(signal)) + 1e-6)


def piano_tone(freq, duration_s):
    """Piano-like tone with fast attack and exponential decay."""
    n = time_to_samples(duration_s)
    t = np.linspace(0, duration_s, n, False)
    harmonics = [(1.0, 1.0), (0.6, 2.0), (0.3, 3.0), (0.15, 4.0), (0.08, 5.0)]
    signal = np.zeros(n)
    for amp, h in harmonics:
        signal += amp * np.sin(2 * np.pi * freq * h * t)
    # Piano envelope: fast attack, exponential decay
    envelope = np.exp(-3.0 * t / duration_s)
    envelope[:min(int(0.005 * SAMPLE_RATE), n)] *= np.linspace(0, 1, min(int(0.005 * SAMPLE_RATE), n))
    return signal * envelope / (np.max(np.abs(signal * envelope)) + 1e-6)


def shimmer_tone(freq, duration_s):
    """Shimmering bell/celesta-like tone."""
    n = time_to_samples(duration_s)
    t = np.linspace(0, duration_s, n, False)
    # Bell-like: strong high partials
    harmonics = [(1.0, 1.0), (0.8, 2.5), (0.6, 4.0), (0.4, 5.5), (0.2, 7.0)]
    signal = np.zeros(n)
    for amp, h in harmonics:
        signal += amp * np.sin(2 * np.pi * freq * h * t)
    # Tremolo
    tremolo = 1.0 + 0.3 * np.sin(2 * np.pi * 6 * t)
    envelope = np.exp(-2.0 * t / duration_s)
    signal = signal * envelope * tremolo
    return signal / (np.max(np.abs(signal)) + 1e-6)


def pizzicato_tone(freq, duration_s):
    """Short, plucky pizzicato string."""
    n = time_to_samples(duration_s)
    t = np.linspace(0, duration_s, n, False)
    harmonics = [(1.0, 1.0), (0.5, 2.0), (0.25, 3.0), (0.1, 4.0)]
    signal = np.zeros(n)
    for amp, h in harmonics:
        signal += amp * np.sin(2 * np.pi * freq * h * t)
    # Very fast decay
    envelope = np.exp(-8.0 * t / duration_s)
    envelope[:min(int(0.002 * SAMPLE_RATE), n)] *= np.linspace(0, 1, min(int(0.002 * SAMPLE_RATE), n))
    return signal * envelope / (np.max(np.abs(signal * envelope)) + 1e-6)


def brass_tone(freq, duration_s):
    """Warm brass-like tone."""
    n = time_to_samples(duration_s)
    t = np.linspace(0, duration_s, n, False)
    harmonics = [(1.0, 1.0), (0.8, 2.0), (0.6, 3.0), (0.5, 4.0), (0.3, 5.0), (0.15, 6.0)]
    signal = np.zeros(n)
    for amp, h in harmonics:
        signal += amp * np.sin(2 * np.pi * freq * h * t)
    # Brass envelope: slower attack
    attack_n = min(int(0.05 * SAMPLE_RATE), n)
    envelope = np.ones(n)
    envelope[:attack_n] = np.linspace(0, 1, attack_n)
    release_n = min(int(0.1 * SAMPLE_RATE), n)
    envelope[-release_n:] = np.linspace(1, 0, release_n)
    return signal * envelope / (np.max(np.abs(signal * envelope)) + 1e-6)


def synth_arp_tone(freq, duration_s):
    """Electronic synth arp tone."""
    n = time_to_samples(duration_s)
    t = np.linspace(0, duration_s, n, False)
    # Saw-like
    signal = np.zeros(n)
    for h in range(1, 8):
        signal += ((-1) ** (h + 1)) * np.sin(2 * np.pi * freq * h * t) / h
    envelope = np.exp(-4.0 * t / duration_s)
    envelope[:min(int(0.003 * SAMPLE_RATE), n)] *= np.linspace(0, 1, min(int(0.003 * SAMPLE_RATE), n))
    return signal * envelope / (np.max(np.abs(signal * envelope)) + 1e-6)


def generate_noise_hit(duration_s, decay_rate=15.0):
    """Generate a percussive noise hit (timpani/impact)."""
    n = time_to_samples(duration_s)
    t = np.linspace(0, duration_s, n, False)
    noise = np.random.randn(n)
    # Low pass via smoothing
    kernel_size = 50
    kernel = np.ones(kernel_size) / kernel_size
    noise = np.convolve(noise, kernel, mode='same')
    # Add low frequency body
    body = np.sin(2 * np.pi * 60 * t) * 0.8 + np.sin(2 * np.pi * 90 * t) * 0.4
    signal = noise * 0.4 + body * 0.6
    envelope = np.exp(-decay_rate * t / duration_s)
    return signal * envelope / (np.max(np.abs(signal * envelope)) + 1e-6)


def add_to_mix(mix, signal, start_s, volume=1.0):
    """Add a signal to the mix at a specific time position."""
    start = time_to_samples(start_s)
    end = min(start + len(signal), len(mix))
    actual_len = end - start
    if actual_len > 0:
        mix[start:end] += signal[:actual_len] * volume


def crossfade(mix, start_s, duration_s, direction='in'):
    """Apply a crossfade to a section of the mix."""
    start = time_to_samples(start_s)
    n = time_to_samples(duration_s)
    end = min(start + n, len(mix))
    actual_n = end - start
    if direction == 'in':
        mix[start:end] *= np.linspace(0, 1, actual_n)
    else:
        mix[start:end] *= np.linspace(1, 0, actual_n)


def generate_trailer_music():
    """Generate the full 45-second trailer score."""
    print("Generating 45-second trailer music...")
    print(f"Sample rate: {SAMPLE_RATE}Hz, Duration: {DURATION}s")

    mix = np.zeros(TOTAL_SAMPLES)

    # ===== SECTION 1: Warm intro (0-4s) - Piano + soft strings =====
    print("  Section 1: Warm intro (0-4s)...")

    # Gentle piano melody in C major
    piano_melody = [
        (0.0, 'C4', 0.8), (0.8, 'E4', 0.6), (1.4, 'G4', 0.8),
        (2.2, 'A4', 0.6), (2.8, 'G4', 1.0),
    ]
    for t, note, dur in piano_melody:
        add_to_mix(mix, piano_tone(NOTES[note], dur), t, volume=0.35)

    # Warm pad underneath
    pad_notes = [('C3', 'E3', 'G3')]
    for notes in pad_notes:
        chord = np.zeros(time_to_samples(4.0))
        for note in notes:
            chord += generate_tone(NOTES[note], 4.0, harmonics=[(1.0, 1), (0.3, 2), (0.1, 3)]) * 0.15
        # Slow swell
        n = len(chord)
        chord *= np.linspace(0, 0.8, n) * np.exp(-0.3 * np.linspace(0, 4, n))
        add_to_mix(mix, chord, 0.5, volume=0.25)

    # ===== SECTION 2: Magical swell (4-8s) - Shimmer, bells =====
    print("  Section 2: Magical swell (4-8s)...")

    shimmer_melody = [
        (4.0, 'E5', 0.4), (4.4, 'G5', 0.4), (4.8, 'C6', 0.6),
        (5.4, 'B5', 0.4), (5.8, 'G5', 0.4), (6.2, 'E5', 0.6),
        (6.8, 'G5', 0.4), (7.2, 'C6', 0.8),
    ]
    for t, note, dur in shimmer_melody:
        add_to_mix(mix, shimmer_tone(NOTES[note], dur), t, volume=0.3)

    # Rising pad
    swell_pad = np.zeros(time_to_samples(4.0))
    for note in ['C4', 'E4', 'G4', 'C5']:
        swell_pad += generate_tone(NOTES[note], 4.0) * 0.12
    n = len(swell_pad)
    swell_pad *= np.linspace(0.2, 1.0, n)  # crescendo
    add_to_mix(mix, swell_pad, 4.0, volume=0.3)

    # ===== SECTION 3: Playful adventure (8-18s) - Pizzicato + percussion =====
    print("  Section 3: Playful adventure (8-18s)...")

    # Pizzicato melody - bouncy C major theme
    pizz_melody = [
        (8.0, 'C5', 0.2), (8.25, 'E5', 0.2), (8.5, 'G5', 0.2), (8.75, 'C6', 0.3),
        (9.1, 'B5', 0.2), (9.35, 'G5', 0.2), (9.6, 'E5', 0.3),
        (10.0, 'D5', 0.2), (10.25, 'F5', 0.2), (10.5, 'A5', 0.2), (10.75, 'C6', 0.3),
        (11.1, 'B5', 0.2), (11.35, 'A5', 0.2), (11.6, 'G5', 0.3),
        (12.0, 'C5', 0.2), (12.25, 'E5', 0.2), (12.5, 'G5', 0.3),
        (12.85, 'A5', 0.2), (13.1, 'G5', 0.2), (13.35, 'E5', 0.3),
        (13.7, 'F5', 0.2), (13.95, 'E5', 0.2), (14.2, 'D5', 0.3),
        (14.55, 'C5', 0.4),
        # Repeat with variation
        (15.0, 'E5', 0.2), (15.25, 'G5', 0.2), (15.5, 'C6', 0.2), (15.75, 'E6', 0.3),
        (16.1, 'D6', 0.2), (16.35, 'C6', 0.2), (16.6, 'B5', 0.3),
        (17.0, 'A5', 0.2), (17.25, 'G5', 0.2), (17.5, 'E5', 0.2), (17.75, 'C5', 0.25),
    ]
    for t, note, dur in pizz_melody:
        add_to_mix(mix, pizzicato_tone(NOTES[note], dur), t, volume=0.35)

    # Light percussion (subtle kicks on beats)
    bpm = 125
    beat_dur = 60.0 / bpm
    for beat in range(int((18 - 8) / beat_dur)):
        t = 8.0 + beat * beat_dur
        if t < 18.0:
            add_to_mix(mix, generate_noise_hit(0.1, decay_rate=25), t, volume=0.12)

    # Light bass line
    bass_notes_sec3 = [
        (8.0, 'C3', 1.0), (9.0, 'G3', 1.0), (10.0, 'A3', 1.0), (11.0, 'G3', 1.0),
        (12.0, 'C3', 1.0), (13.0, 'F3', 1.0), (14.0, 'G3', 1.0), (15.0, 'C3', 1.0),
        (16.0, 'A3', 1.0), (17.0, 'G3', 1.0),
    ]
    for t, note, dur in bass_notes_sec3:
        add_to_mix(mix, piano_tone(NOTES[note], dur), t, volume=0.2)

    # ===== SECTION 4: Dramatic tension (18-24s) - Brass + timpani =====
    print("  Section 4: Dramatic tension (18-24s)...")

    # Big timpani hit at 18s (syncs with "went VERY wrong")
    add_to_mix(mix, generate_noise_hit(1.0, decay_rate=4.0), 18.0, volume=0.5)

    # Deep brass chords
    brass_chords = [
        (18.5, ['C3', 'G3', 'C4', 'E4'], 1.5),
        (20.0, ['D3', 'A3', 'D4', 'F4'], 1.5),
        (21.5, ['G2', 'D3', 'G3', 'B3'], 1.5),
        (23.0, ['C3', 'G3', 'C4', 'E4'], 1.0),
    ]
    for t, notes, dur in brass_chords:
        for note in notes:
            add_to_mix(mix, brass_tone(NOTES[note], dur), t, volume=0.18)

    # Tension building - rising brass line
    rising_notes = [
        (18.5, 'E4', 0.4), (19.0, 'F4', 0.4), (19.5, 'G4', 0.4),
        (20.0, 'A4', 0.5), (20.5, 'B4', 0.5),
        (21.0, 'C5', 0.6), (21.6, 'D5', 0.6),
        (22.2, 'E5', 0.8),
    ]
    for t, note, dur in rising_notes:
        add_to_mix(mix, brass_tone(NOTES[note], dur), t, volume=0.2)

    # Timpani accents
    add_to_mix(mix, generate_noise_hit(0.5, decay_rate=6.0), 20.0, volume=0.3)
    add_to_mix(mix, generate_noise_hit(0.5, decay_rate=6.0), 22.0, volume=0.35)

    # ===== SECTION 5: Techy underlay (24-30s) - Synth arps + electronic =====
    print("  Section 5: Techy underlay (24-30s)...")

    # Synth arpeggio pattern
    arp_pattern = [
        'C4', 'E4', 'G4', 'C5', 'G4', 'E4',
        'A3', 'C4', 'E4', 'A4', 'E4', 'C4',
        'F3', 'A3', 'C4', 'F4', 'C4', 'A3',
        'G3', 'B3', 'D4', 'G4', 'D4', 'B3',
    ]
    arp_note_dur = 0.12
    for i, note in enumerate(arp_pattern * 2):  # repeat pattern
        t = 24.0 + i * arp_note_dur
        if t < 30.0:
            add_to_mix(mix, synth_arp_tone(NOTES[note], arp_note_dur * 1.5), t, volume=0.2)

    # Electronic pulse (sub-bass)
    pulse_n = time_to_samples(6.0)
    t_pulse = np.linspace(0, 6.0, pulse_n, False)
    pulse = np.sin(2 * np.pi * 1.5 * t_pulse) * 0.3  # Slow pulse
    sub = np.sin(2 * np.pi * 55 * t_pulse) * 0.2  # Sub bass
    add_to_mix(mix, pulse * sub, 24.0, volume=0.4)

    # Continuing beat
    for beat in range(int(6 / beat_dur)):
        t = 24.0 + beat * beat_dur
        if t < 30.0:
            add_to_mix(mix, generate_noise_hit(0.08, decay_rate=30), t, volume=0.15)

    # ===== SECTION 6: Building energy (30-39s) - Combined orchestral + electronic =====
    print("  Section 6: Building energy (30-39s)...")

    # Combined melody - triumphant
    triumph_melody = [
        (30.0, 'C5', 0.4), (30.4, 'D5', 0.4), (30.8, 'E5', 0.4),
        (31.2, 'G5', 0.6), (31.8, 'E5', 0.3), (32.1, 'G5', 0.3),
        (32.4, 'C6', 0.8),
        (33.2, 'B5', 0.3), (33.5, 'A5', 0.3), (33.8, 'G5', 0.4),
        (34.2, 'A5', 0.4), (34.6, 'G5', 0.4), (35.0, 'E5', 0.6),
        (35.6, 'D5', 0.3), (35.9, 'E5', 0.3), (36.2, 'G5', 0.6),
        (36.8, 'C6', 0.4), (37.2, 'D6', 0.4), (37.6, 'E6', 0.8),
        (38.4, 'D6', 0.3), (38.7, 'C6', 0.3),
    ]
    for t, note, dur in triumph_melody:
        # Both brass and shimmer for combined sound
        add_to_mix(mix, brass_tone(NOTES[note], dur), t, volume=0.2)
        add_to_mix(mix, shimmer_tone(NOTES[note], dur), t, volume=0.15)

    # Driving synth arps continue
    fast_arp = ['C4', 'G4', 'E4', 'C5', 'G4', 'C4', 'E4', 'G4']
    for i, note in enumerate(fast_arp * 5):
        t = 30.0 + i * 0.15
        if t < 39.0:
            add_to_mix(mix, synth_arp_tone(NOTES[note], 0.2), t, volume=0.12)

    # Strong bass
    bass_sec6 = [
        (30.0, 'C2', 1.5), (31.5, 'G2', 1.5), (33.0, 'A2', 1.5),
        (34.5, 'G2', 1.5), (36.0, 'F2', 1.5), (37.5, 'G2', 1.5),
    ]
    for t, note, dur in bass_sec6:
        add_to_mix(mix, brass_tone(NOTES[note], dur), t, volume=0.22)

    # Percussion gets heavier
    for beat in range(int(9 / beat_dur)):
        t = 30.0 + beat * beat_dur
        if t < 39.0:
            add_to_mix(mix, generate_noise_hit(0.1, decay_rate=20), t, volume=0.2)
            # Off-beat hi-hat-like
            t_offbeat = t + beat_dur / 2
            if t_offbeat < 39.0:
                hat = np.random.randn(time_to_samples(0.03)) * 0.08
                hat *= np.exp(-30 * np.linspace(0, 0.03, len(hat)))
                add_to_mix(mix, hat, t_offbeat, volume=0.15)

    # ===== SECTION 7: Finale (39-45s) - Big resolving hit =====
    print("  Section 7: Resolving finale (39-45s)...")

    # Big chord hit at start of finale
    add_to_mix(mix, generate_noise_hit(1.5, decay_rate=2.5), 39.0, volume=0.5)

    finale_chord_notes = ['C3', 'G3', 'C4', 'E4', 'G4', 'C5', 'E5']
    for note in finale_chord_notes:
        tone = brass_tone(NOTES[note], 3.0)
        add_to_mix(mix, tone, 39.0, volume=0.15)
        shimmer = shimmer_tone(NOTES[note], 2.0)
        add_to_mix(mix, shimmer, 39.0, volume=0.1)

    # "SUBSCRIBE" beat at ~42s
    add_to_mix(mix, generate_noise_hit(0.8, decay_rate=5.0), 42.0, volume=0.45)
    for note in ['C4', 'E4', 'G4', 'C5']:
        add_to_mix(mix, shimmer_tone(NOTES[note], 1.5), 42.0, volume=0.2)

    # Final resolving melody
    finale_melody = [
        (39.5, 'E5', 0.4), (39.9, 'G5', 0.4), (40.3, 'C6', 1.0),
        (41.3, 'G5', 0.4), (41.7, 'C6', 0.8),
        (42.5, 'E6', 0.5), (43.0, 'D6', 0.5), (43.5, 'C6', 1.5),
    ]
    for t, note, dur in finale_melody:
        add_to_mix(mix, piano_tone(NOTES[note], dur), t, volume=0.25)
        add_to_mix(mix, shimmer_tone(NOTES[note], dur), t, volume=0.15)

    # ===== POST-PROCESSING =====
    print("  Post-processing...")

    # Global reverb
    delay_samples = int(SAMPLE_RATE * 0.04)
    reverb_mix = mix.copy()
    for i in range(1, 6):
        offset = delay_samples * i
        decay = 0.3 ** i
        if offset < len(mix):
            reverb_mix[offset:] += mix[:-offset] * decay
    mix = reverb_mix

    # Fade in (first 0.5s) and fade out (last 1s)
    fade_in_n = time_to_samples(0.5)
    fade_out_n = time_to_samples(1.0)
    mix[:fade_in_n] *= np.linspace(0, 1, fade_in_n)
    mix[-fade_out_n:] *= np.linspace(1, 0, fade_out_n)

    # 2-3 frames of silence at start/end (per audio plan)
    silence_frames = time_to_samples(0.1)
    mix[:silence_frames] = 0
    mix[-silence_frames:] = 0

    # Mix at -6dB (per audio plan: leave headroom for narration)
    mix *= 0.5  # -6dB

    # Normalize
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.9  # Leave a little headroom

    return mix


def main():
    print("=" * 60)
    print("Fairy Dinosaur Date Night - Trailer Music Generation")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate the music
    audio = generate_trailer_music()

    # Save as WAV (48kHz 16-bit)
    wav_path = OUTPUT_DIR / "trailer-music.wav"
    audio_16bit = (audio * 32767).astype(np.int16)
    wavfile.write(wav_path, SAMPLE_RATE, audio_16bit)
    print(f"\nSaved WAV: {wav_path} ({len(audio_16bit) / SAMPLE_RATE:.1f}s)")

    # Convert to MP3 using ffmpeg
    mp3_path = OUTPUT_DIR / "trailer-music.mp3"
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', str(wav_path),
            '-codec:a', 'libmp3lame', '-b:a', '192k',
            str(mp3_path)
        ], check=True, capture_output=True)
        print(f"Saved MP3: {mp3_path}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Warning: Could not convert to MP3 ({e}). WAV file is available.")

    print("\n" + "=" * 60)
    print("Trailer music generation complete!")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
