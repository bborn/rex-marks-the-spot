#!/usr/bin/env python3
"""Generate placeholder SVG images for storyboard panels."""

import os

# Panel definitions: (scene_num, panel_count, scene_title, panel_descriptions)
SCENES = [
    (1, 9, "INT. HOME - EVENING", [
        "Wide Establishing - Living room, storm outside, kids on couch",
        "Medium - Leo in dinosaur pajamas hugging toy",
        "Tracking - Nina putting on earrings, multitasking",
        "Two-Shot - Gabe and Nina, overlapping dialogue",
        "Insert - Jenny absorbed in phone",
        "Close-up - TV flickering with static",
        "OTS - Kids watching TV, parents in background",
        "Close-up - Mia looking up, concerned",
        "Close-up - Gabe hesitates, Nina glares",
    ]),
    (2, 3, "EXT. HOUSE - NIGHT", [
        "Wide - House exterior, storm, lightning",
        "Tracking - Parents rush through rain to car",
        "Low Angle - Lightning cracks across sky",
    ]),
    (3, 4, "INT. CAR - NIGHT", [
        "Two-Shot - Gabe driving, Nina searching",
        "Insert - Phone showing 'Calling Nina'",
        "POV - Rain-obscured road through windshield",
        "Close-up - Nina, concerned expression",
    ]),
    (4, 3, "INT. HOUSE - MONTAGE", [
        "Wide - Peaceful living room, kids watching TV",
        "Insert - Jenny texting, absorbed",
        "Insert - Nina's phone buzzing under cushion",
    ]),
    (5, 4, "EXT. ROAD - TIME WARP", [
        "POV - TIME WARP opens ahead of car",
        "Interior - Terror reaction, blue light",
        "Wide - Car enters massive blue portal",
        "Close-up - Car consumed by vortex",
    ]),
    (6, 4, "INT. HOUSE - SIMULTANEOUSLY", [
        "Wide - TV explodes with static/sparks",
        "Reaction - All three startled",
        "Low Light - Room dark, eerie atmosphere",
        "Insert - Nina's phone glowing supernatural blue",
    ]),
    (7, 6, "INT. CAR - JURASSIC DAY", [
        "Close-up - Nina wakes, confused",
        "POV - Trashed car interior, debris",
        "Insert - Toy dinosaur on dashboard",
        "Two-Shot - Nina rouses unconscious Gabe",
        "POV - Lush prehistoric vegetation outside",
        "Wide - Full Jurassic swamp reveal",
    ]),
    (8, 9, "EXT. JURASSIC SWAMP - T-REX", [
        "Wide - Parents emerge from crashed car",
        "POV - Exploring exotic prehistoric plants",
        "Medium - Time warp and weird creature (Jetplane)",
        "Close-up - Ground rumbles, water ripples",
        "Reaction - Weird creature flees in terror",
        "Wide - T-REX APPEARS (Hero Shot)",
        "Close-up - T-Rex head, terrifying detail",
        "Low Angle - T-Rex SMASHES the car",
        "Tracking - Parents flee into jungle",
    ]),
    (9, 7, "EXT. JURASSIC BRUSH - CHASE", [
        "Steadicam - Chase through giant ferns",
        "POV - Looking back at T-Rex, too close",
        "Wide - T-Rex crashes through jungle",
        "Medium - Second dinosaur blocks path",
        "Two-Shot - Running and arguing",
        "POV - Cave entrance spotted",
        "Tracking - Slide into cave, T-Rex arrives",
    ]),
    (10, 7, "INT. CAVE - EMOTIONAL CLIMAX", [
        "Wide - Cave interior, T-Rex at entrance",
        "Insert - T-Rex claws scraping at entrance",
        "Two-Shot - Parents huddle together",
        "Wide - Reacting to dinosaur battle sounds",
        "Close-up - Nina, determination forming",
        "Two-Shot - Both realize they left the kids",
        "Insert - Phone in Nina's hand (END ACT 1)",
    ]),
]

# Color schemes for different scene types
SCENE_COLORS = {
    1: ("#FFE4B5", "#8B4513", "Warm Home"),  # Warm amber
    2: ("#2F4F4F", "#87CEEB", "Storm Night"),  # Dark storm
    3: ("#1C1C1C", "#4169E1", "Car Interior"),  # Dark car
    4: ("#FFE4B5", "#8B4513", "Warm Home"),  # Warm amber
    5: ("#0096FF", "#FFFFFF", "Time Warp"),  # Blue vortex
    6: ("#1C1C1C", "#0096FF", "Dark House"),  # Dark with blue
    7: ("#90EE90", "#228B22", "Jurassic"),  # Green jungle
    8: ("#90EE90", "#8B4513", "Swamp/T-Rex"),  # Green/brown
    9: ("#228B22", "#8B4513", "Chase"),  # Dense green
    10: ("#2F4F4F", "#FFD700", "Cave"),  # Dark cave
}

def create_svg(scene_num, panel_num, scene_title, panel_desc):
    """Generate an SVG placeholder for a panel."""
    bg_color, text_color, mood = SCENE_COLORS[scene_num]

    # Determine if this is a major VFX scene
    is_vfx = scene_num in [5, 8, 9]
    vfx_indicator = " [VFX]" if is_vfx else ""

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
  <defs>
    <linearGradient id="bg{scene_num}_{panel_num}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{bg_color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{adjust_color(bg_color, -30)};stop-opacity:1" />
    </linearGradient>
    <filter id="shadow">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.3"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="1920" height="1080" fill="url(#bg{scene_num}_{panel_num})"/>

  <!-- Frame border -->
  <rect x="20" y="20" width="1880" height="1040" fill="none" stroke="{text_color}" stroke-width="4" rx="10"/>

  <!-- Scene indicator top -->
  <rect x="50" y="50" width="400" height="60" fill="{text_color}" rx="5" opacity="0.9"/>
  <text x="70" y="92" font-family="Arial, sans-serif" font-size="28" font-weight="bold" fill="{bg_color}">
    Scene {scene_num:02d} - Panel {panel_num:02d}{vfx_indicator}
  </text>

  <!-- Mood indicator -->
  <text x="1850" y="92" font-family="Arial, sans-serif" font-size="24" fill="{text_color}" text-anchor="end" opacity="0.7">
    {mood}
  </text>

  <!-- Scene title -->
  <text x="960" y="180" font-family="Arial, sans-serif" font-size="42" font-weight="bold" fill="{text_color}" text-anchor="middle" filter="url(#shadow)">
    {scene_title}
  </text>

  <!-- Panel description box -->
  <rect x="160" y="380" width="1600" height="200" fill="{text_color}" opacity="0.15" rx="10"/>
  <text x="960" y="500" font-family="Arial, sans-serif" font-size="36" fill="{text_color}" text-anchor="middle">
    {panel_desc}
  </text>

  <!-- Placeholder composition guides -->
  <line x1="640" y1="20" x2="640" y2="1060" stroke="{text_color}" stroke-width="1" stroke-dasharray="10,5" opacity="0.3"/>
  <line x1="1280" y1="20" x2="1280" y2="1060" stroke="{text_color}" stroke-width="1" stroke-dasharray="10,5" opacity="0.3"/>
  <line x1="20" y1="360" x2="1900" y2="360" stroke="{text_color}" stroke-width="1" stroke-dasharray="10,5" opacity="0.3"/>
  <line x1="20" y1="720" x2="1900" y2="720" stroke="{text_color}" stroke-width="1" stroke-dasharray="10,5" opacity="0.3"/>

  <!-- Action area indicator -->
  <rect x="460" y="600" width="1000" height="350" fill="none" stroke="{text_color}" stroke-width="2" stroke-dasharray="20,10" rx="20" opacity="0.4"/>
  <text x="960" y="790" font-family="Arial, sans-serif" font-size="24" fill="{text_color}" text-anchor="middle" opacity="0.5">
    [AI-GENERATED STORYBOARD IMAGE]
  </text>

  <!-- Footer info -->
  <text x="50" y="1040" font-family="Arial, sans-serif" font-size="18" fill="{text_color}" opacity="0.6">
    Fairy Dinosaur Date Night - Act 1 Storyboard
  </text>
  <text x="1870" y="1040" font-family="Arial, sans-serif" font-size="18" fill="{text_color}" text-anchor="end" opacity="0.6">
    scene-{scene_num:02d}-panel-{panel_num:02d}.png
  </text>
</svg>'''
    return svg

def adjust_color(hex_color, amount):
    """Adjust a hex color by amount."""
    hex_color = hex_color.lstrip('#')
    r = max(0, min(255, int(hex_color[0:2], 16) + amount))
    g = max(0, min(255, int(hex_color[2:4], 16) + amount))
    b = max(0, min(255, int(hex_color[4:6], 16) + amount))
    return f"#{r:02x}{g:02x}{b:02x}"

def main():
    """Generate all placeholder SVG files."""
    output_dir = os.path.dirname(os.path.abspath(__file__))

    total_panels = 0
    for scene_num, panel_count, scene_title, descriptions in SCENES:
        for panel_idx, desc in enumerate(descriptions, 1):
            filename = f"scene-{scene_num:02d}-panel-{panel_idx:02d}.svg"
            filepath = os.path.join(output_dir, filename)

            svg_content = create_svg(scene_num, panel_idx, scene_title, desc)

            with open(filepath, 'w') as f:
                f.write(svg_content)

            print(f"Created: {filename}")
            total_panels += 1

    print(f"\nGenerated {total_panels} placeholder panels")

if __name__ == "__main__":
    main()
