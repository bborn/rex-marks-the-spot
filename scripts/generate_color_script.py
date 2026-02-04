#!/usr/bin/env python3
"""
Color Script Generator for "Fairy Dinosaur Date Night"

Generates color palette strips and annotated thumbnails showing the
emotional color progression through the film.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Output directory
OUTPUT_DIR = "docs/production/color-script"
PALETTES_DIR = os.path.join(OUTPUT_DIR, "palettes")
THUMBNAILS_DIR = os.path.join(OUTPUT_DIR, "thumbnails")

# Ensure directories exist
os.makedirs(PALETTES_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

# Color palettes by scene/emotional beat
# Each palette: [primary, secondary, accent, shadow, highlight]

COLOR_PALETTES = {
    # ACT 1 - HOME (Warm, Safe, Cozy)
    "act1_scene01_home_evening": {
        "name": "Home Evening - Safety & Warmth",
        "mood": "Cozy, safe, domestic chaos",
        "colors": ["#E8A45C", "#C67B3C", "#FFD59E", "#5C3D2E", "#FFF5E6"],
        "color_names": ["Amber Glow", "Wood Brown", "Warm Cream", "Shadow", "Highlight"],
        "description": "Warm amber tungsten lighting. Cozy suburban home filled with love and gentle chaos."
    },

    # ACT 1 - STORM BREWING (Ominous Transition)
    "act1_scene02_storm_exterior": {
        "name": "Storm Exterior - Foreboding",
        "mood": "Ominous, unsettling, transition",
        "colors": ["#3D5A73", "#1E3A4C", "#7BA3BE", "#0F1F2B", "#A8C4D9"],
        "color_names": ["Storm Blue", "Dark Sky", "Lightning Flash", "Night Shadow", "Rain Reflection"],
        "description": "Cold desaturated blues. Storm clouds gathering. Warmth of home visible through windows."
    },

    # ACT 1 - CAR IN RAIN (Tension)
    "act1_scene03_car_night": {
        "name": "Car Night - Building Tension",
        "mood": "Confined, tense, rain-lashed",
        "colors": ["#2C4A5E", "#8B5A2B", "#5C8AAD", "#1A2E3D", "#D4B896"],
        "color_names": ["Night Blue", "Dashboard Amber", "Headlight Glow", "Deep Shadow", "Skin Tone"],
        "description": "Cool blue-gray exterior with warm dashboard glow. Rain streaks on windows."
    },

    # ACT 1 - TIME WARP (Supernatural Magic)
    "act1_scene05_time_warp": {
        "name": "Time Warp - Supernatural",
        "mood": "Magical, terrifying, otherworldly",
        "colors": ["#00C8FF", "#7B2FBE", "#FFFFFF", "#0A1628", "#FF00FF"],
        "color_names": ["Electric Blue", "Portal Purple", "Energy White", "Void Black", "Magic Pink"],
        "description": "Intense electric blues and purples. Blinding white energy. Swirling vortex effect."
    },

    # ACT 1 - AFTERMATH (Shock)
    "act1_scene06_aftermath": {
        "name": "House Aftermath - Shock",
        "mood": "Stunned silence, eerie, uncertain",
        "colors": ["#2D3E50", "#8B7355", "#00BFFF", "#0F1923", "#E8DFD0"],
        "color_names": ["Dark Room", "Warm Wood", "Phone Glow", "Shadows", "Moonlight"],
        "description": "Dark interior with only moonlight and mysterious phone glow. Silence after chaos."
    },

    # ACT 1 - JURASSIC SWAMP (Wonder)
    "act1_scene07_jurassic_wonder": {
        "name": "Jurassic Awakening - Wonder",
        "mood": "Awe, discovery, primal beauty",
        "colors": ["#4A7C59", "#8FBC8F", "#FFD700", "#2F4F2F", "#E6F2E6"],
        "color_names": ["Lush Green", "Fern Light", "Golden Sun", "Deep Forest", "Mist"],
        "description": "Saturated prehistoric greens. Golden morning light filtering through giant ferns."
    },

    # ACT 1 - T-REX REVEAL (Terror)
    "act1_scene08_trex_terror": {
        "name": "T-Rex Reveal - Terror",
        "mood": "Primal fear, danger, survival",
        "colors": ["#3D5C3D", "#6B4423", "#FFE4B5", "#1A2B1A", "#8B0000"],
        "color_names": ["Dark Jungle", "Dinosaur Brown", "Danger Highlight", "Deep Shadow", "Blood Red"],
        "description": "Shadows deepen. Greens become threatening. Warm highlights only on characters' faces."
    },

    # ACT 1 - CAVE (Fear & Connection)
    "act1_scene10_cave": {
        "name": "Cave Refuge - Fear & Hope",
        "mood": "Trapped, desperate, but connected",
        "colors": ["#3D3D3D", "#5C4033", "#00BFFF", "#1A1A1A", "#C9A86C"],
        "color_names": ["Cave Gray", "Earth Brown", "Phone Glow", "Deep Dark", "Warm Skin"],
        "description": "Dark cave with phone providing only hope. Warm skin tones against cold stone."
    },

    # ACT 2 - INVESTIGATION (Clinical)
    "act2_investigation": {
        "name": "Investigation - Uncertainty",
        "mood": "Clinical, institutional, suspicious",
        "colors": ["#7D8C93", "#5C6B73", "#F5F5DC", "#3D4A52", "#B8860B"],
        "color_names": ["Office Gray", "Steel Blue", "Fluorescent", "Shadow", "Wood Accent"],
        "description": "Desaturated institutional colors. Fluorescent lighting. Stark and uncomfortable."
    },

    # ACT 2 - RUBEN INTRO (Magic in Mundane)
    "act2_ruben_magic": {
        "name": "Ruben's Magic - Hope Emerges",
        "mood": "Magical possibility in ordinary setting",
        "colors": ["#4A5568", "#9F7AEA", "#FFD700", "#1A202C", "#E8E4F0"],
        "color_names": ["Station Gray", "Fairy Purple", "Magic Gold", "Night", "Sparkle"],
        "description": "Mundane police station with subtle magical iridescence. Mop wand glows faintly."
    },

    # ACT 2 - JURASSIC TREE NIGHT (Emotional)
    "act2_jurassic_tree": {
        "name": "Tree at Sunset - Emotional",
        "mood": "Vulnerable, intimate, hopeful",
        "colors": ["#FF6B35", "#C44536", "#2D3436", "#FFE66D", "#7B2D26"],
        "color_names": ["Sunset Orange", "Sky Red", "Silhouette", "Golden Light", "Deep Warm"],
        "description": "Beautiful Jurassic sunset. Parents as silhouettes. Last light of day as hope."
    },

    # ACT 2 - ESCAPE & CHASE (Energy)
    "act2_chase": {
        "name": "Chase Sequence - High Energy",
        "mood": "Excitement, danger, urgency",
        "colors": ["#1A1A2E", "#E94560", "#0F3460", "#16213E", "#FF6B6B"],
        "color_names": ["Night", "Police Red", "Blue Flash", "Street Shadow", "Brake Light"],
        "description": "Night chase with red and blue police lights. High contrast and motion."
    },

    # ACT 3 - JETPLANE COLORS (Joy)
    "act3_jetplane_farts": {
        "name": "Jetplane's Colors - Joy & Wonder",
        "mood": "Magical, whimsical, unexpected beauty",
        "colors": ["#FF6B6B", "#4ECDC4", "#FFE66D", "#9B59B6", "#3498DB"],
        "color_names": ["Candy Red", "Teal", "Yellow", "Purple", "Blue"],
        "description": "Rainbow fart plumes! Vibrant candy colors against prehistoric greens."
    },

    # ACT 3 - CANYON BRIDGE (Peril)
    "act3_canyon": {
        "name": "Canyon Crossing - Peril",
        "mood": "Vertigo, danger, teamwork",
        "colors": ["#8B4513", "#4A7C59", "#87CEEB", "#2F4F2F", "#DEB887"],
        "color_names": ["Canyon Red", "Jungle Green", "Sky Blue", "Depth", "Crayon"],
        "description": "Vast canyon depth. Vertigo-inducing scale. Fragile crayon bridge colors."
    },

    # ACT 3 - CLIMAX (Danger & Magic)
    "act3_climax": {
        "name": "Final Confrontation - All at Stake",
        "mood": "Maximum tension, magic, hope",
        "colors": ["#2D3436", "#00C8FF", "#6B4423", "#FFD700", "#8B0000"],
        "color_names": ["Storm Dark", "Portal Blue", "T-Rex Brown", "Magic Gold", "Danger Red"],
        "description": "Dark and dangerous with portal blue and magic gold as beacons of hope."
    },

    # ACT 3 - RETURN HOME (Relief)
    "act3_return": {
        "name": "Return Home - Relief",
        "mood": "Safety, exhaustion, joy",
        "colors": ["#2C3E50", "#E94560", "#0F3460", "#FFE66D", "#E8DFD0"],
        "color_names": ["Night Street", "Police Red", "Blue Light", "Street Light", "Warm Face"],
        "description": "Night street with police lights, but warm skin tones dominate. Safe at last."
    },

    # EPILOGUE - MORNING (Resolution)
    "epilogue_morning": {
        "name": "New Morning - Resolution",
        "mood": "Joy, warmth, new beginning",
        "colors": ["#FFE4B5", "#E8A45C", "#87CEEB", "#8FBC8F", "#FFF5E6"],
        "color_names": ["Morning Gold", "Amber Warm", "Clear Sky", "Garden Green", "Bright White"],
        "description": "Full return to warmth. Golden morning light. Family together. Rainbow plumes from chimney."
    },
}

def create_palette_strip(palette_data, filename, width=1200, height=200):
    """Create a horizontal color strip image with labels."""
    colors = palette_data["colors"]
    num_colors = len(colors)
    color_width = width // num_colors

    # Create image
    img = Image.new('RGB', (width, height + 80), color='white')
    draw = ImageDraw.Draw(img)

    # Draw color blocks
    for i, color in enumerate(colors):
        x1 = i * color_width
        x2 = (i + 1) * color_width

        # Convert hex to RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)

        draw.rectangle([x1, 0, x2, height], fill=(r, g, b))

        # Add color name label
        label = palette_data["color_names"][i]
        # Use default font
        text_color = 'black' if (r + g + b) > 380 else 'white'

        # Center text in color block
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = x1 + (color_width - text_width) // 2
        draw.text((text_x, height - 25), label, fill=text_color, font=font)

        # Add hex code below
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        except:
            small_font = font

        hex_bbox = draw.textbbox((0, 0), color, font=small_font)
        hex_width = hex_bbox[2] - hex_bbox[0]
        hex_x = x1 + (color_width - hex_width) // 2
        draw.text((hex_x, height + 10), color, fill='black', font=small_font)

    # Add title
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        title_font = font

    draw.text((10, height + 35), palette_data["name"], fill='black', font=title_font)

    # Add mood
    try:
        mood_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", 12)
    except:
        mood_font = font

    draw.text((10, height + 58), f"Mood: {palette_data['mood']}", fill='#666666', font=mood_font)

    img.save(filename, 'PNG')
    print(f"Created: {filename}")


def create_overview_strip(width=1800, height=150):
    """Create a master color flow strip showing the entire film's color progression."""

    # Define the color flow sections with their dominant colors
    color_flow = [
        ("#E8A45C", "HOME", 120),        # Warm home
        ("#3D5A73", "STORM", 40),         # Storm
        ("#2C4A5E", "CAR", 40),            # Car night
        ("#00C8FF", "WARP", 30),           # Time warp
        ("#2D3E50", "SHOCK", 30),          # Aftermath
        ("#4A7C59", "WONDER", 80),         # Jurassic wonder
        ("#3D5C3D", "TERROR", 60),         # T-Rex terror
        ("#3D3D3D", "CAVE", 50),           # Cave
        ("#7D8C93", "INVEST", 80),         # Investigation
        ("#9F7AEA", "MAGIC", 60),          # Ruben magic
        ("#FF6B35", "SUNSET", 50),         # Jurassic sunset
        ("#E94560", "CHASE", 70),          # Chase
        ("#4ECDC4", "COLORS", 60),         # Jetplane colors
        ("#8B4513", "CANYON", 50),         # Canyon
        ("#00C8FF", "CLIMAX", 60),         # Climax
        ("#2C3E50", "RETURN", 40),         # Return
        ("#FFE4B5", "MORNING", 100),       # New morning
    ]

    img = Image.new('RGB', (width, height + 50), color='white')
    draw = ImageDraw.Draw(img)

    # Calculate total width units
    total_units = sum(c[2] for c in color_flow)

    # Draw color sections with gradient blending
    x = 0
    for color_hex, label, units in color_flow:
        section_width = int((units / total_units) * width)

        r = int(color_hex[1:3], 16)
        g = int(color_hex[3:5], 16)
        b = int(color_hex[5:7], 16)

        draw.rectangle([x, 0, x + section_width, height], fill=(r, g, b))

        # Add label
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
        except:
            font = ImageFont.load_default()

        text_color = 'white' if (r + g + b) < 380 else 'black'
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        if section_width > text_width + 10:
            draw.text((x + 5, height - 20), label, fill=text_color, font=font)

        x += section_width

    # Add title
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        title_font = font

    draw.text((10, height + 10), "FAIRY DINOSAUR DATE NIGHT - Complete Color Script Flow", fill='black', font=title_font)

    # Add act markers
    try:
        act_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except:
        act_font = font

    draw.text((50, height + 30), "ACT 1: Setup & Jurassic", fill='#666', font=act_font)
    draw.text((650, height + 30), "ACT 2: Investigation & Escape", fill='#666', font=act_font)
    draw.text((1300, height + 30), "ACT 3: Adventure & Resolution", fill='#666', font=act_font)

    filename = os.path.join(OUTPUT_DIR, "color-flow-overview.png")
    img.save(filename, 'PNG')
    print(f"Created: {filename}")


def create_act_summary(act_num, palettes_list, width=1600, height=400):
    """Create a vertical summary for each act."""

    num_palettes = len(palettes_list)
    row_height = height // num_palettes

    img = Image.new('RGB', (width, height + 60), color='white')
    draw = ImageDraw.Draw(img)

    y = 0
    for palette_key in palettes_list:
        palette = COLOR_PALETTES[palette_key]
        colors = palette["colors"]
        color_width = (width - 200) // len(colors)

        # Draw scene name
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        except:
            font = ImageFont.load_default()

        draw.text((5, y + row_height // 3), palette["name"][:25], fill='black', font=font)

        # Draw color blocks
        x = 200
        for color in colors:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            draw.rectangle([x, y + 5, x + color_width, y + row_height - 5], fill=(r, g, b))
            x += color_width

        y += row_height

    # Add title
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        title_font = font

    draw.text((10, height + 15), f"Act {act_num} Color Summary", fill='black', font=title_font)

    filename = os.path.join(OUTPUT_DIR, f"act{act_num}-color-summary.png")
    img.save(filename, 'PNG')
    print(f"Created: {filename}")


def main():
    print("Generating color script images for 'Fairy Dinosaur Date Night'...\n")

    # Create individual palette strips
    for key, palette in COLOR_PALETTES.items():
        filename = os.path.join(PALETTES_DIR, f"{key}.png")
        create_palette_strip(palette, filename)

    print()

    # Create overview strip
    create_overview_strip()

    # Create act summaries
    act1_palettes = [
        "act1_scene01_home_evening",
        "act1_scene02_storm_exterior",
        "act1_scene03_car_night",
        "act1_scene05_time_warp",
        "act1_scene06_aftermath",
        "act1_scene07_jurassic_wonder",
        "act1_scene08_trex_terror",
        "act1_scene10_cave",
    ]

    act2_palettes = [
        "act2_investigation",
        "act2_ruben_magic",
        "act2_jurassic_tree",
        "act2_chase",
    ]

    act3_palettes = [
        "act3_jetplane_farts",
        "act3_canyon",
        "act3_climax",
        "act3_return",
        "epilogue_morning",
    ]

    create_act_summary(1, act1_palettes)
    create_act_summary(2, act2_palettes)
    create_act_summary(3, act3_palettes)

    print(f"\nColor script generation complete!")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
