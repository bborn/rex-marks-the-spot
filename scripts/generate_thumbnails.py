#!/usr/bin/env python3
"""
Generate annotated thumbnail compositions for key scenes.
Shows basic composition shapes with color blocking and annotations.
"""

from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = "docs/production/color-script/thumbnails"
os.makedirs(OUTPUT_DIR, exist_ok=True)

WIDTH = 640
HEIGHT = 360  # 16:9 aspect ratio

def get_font(size=12, bold=False):
    """Get a font, falling back to default if needed."""
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_home_evening_thumbnail():
    """Scene 1: Home Evening - Warm domestic chaos."""
    img = Image.new('RGB', (WIDTH, HEIGHT), color='#FFF5E6')
    draw = ImageDraw.Draw(img)

    # Background warm glow
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill='#FFF5E6')

    # Window with storm outside
    draw.rectangle([450, 50, 600, 200], fill='#3D5A73', outline='#5C3D2E', width=4)

    # TV area
    draw.rectangle([50, 100, 200, 200], fill='#333333', outline='#5C3D2E', width=3)
    draw.text((90, 140), "TV", fill='white', font=get_font(14))

    # Couch with kids (simplified shapes)
    draw.ellipse([80, 220, 140, 280], fill='#C67B3C')  # Mia
    draw.ellipse([150, 230, 200, 280], fill='#C67B3C')  # Leo

    # Parents rushing (silhouettes)
    draw.polygon([(320, 150), (360, 300), (280, 300)], fill='#2C2C2C')  # Gabe
    draw.polygon([(400, 160), (440, 300), (360, 300)], fill='#2C2C2C')  # Nina

    # Dinosaur toys scattered
    for pos in [(100, 300), (250, 320), (400, 290)]:
        draw.ellipse([pos[0], pos[1], pos[0]+30, pos[1]+20], fill='#4A7C59')

    # Warm light sources
    draw.ellipse([500, 280, 560, 340], fill='#FFD59E', outline='#E8A45C', width=2)

    # Color annotations
    font = get_font(10)
    draw.text((10, HEIGHT-60), "WARM AMBER: Safety, home", fill='#E8A45C', font=font)
    draw.text((10, HEIGHT-45), "DARK SILHOUETTES: Parents leaving", fill='#5C3D2E', font=font)
    draw.text((10, HEIGHT-30), "STORM BLUE: Threat outside", fill='#3D5A73', font=font)
    draw.text((10, HEIGHT-15), "Scene 1: HOME EVENING", fill='black', font=get_font(11, bold=True))

    img.save(os.path.join(OUTPUT_DIR, "01-home-evening.png"))
    print("Created: 01-home-evening.png")


def create_time_warp_thumbnail():
    """Scene 5: Time Warp - Supernatural inciting incident."""
    img = Image.new('RGB', (WIDTH, HEIGHT), color='#0A1628')
    draw = ImageDraw.Draw(img)

    # Void background
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill='#0A1628')

    # Central vortex - concentric circles
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    colors = ['#FF00FF', '#7B2FBE', '#00C8FF', '#00E5FF', '#FFFFFF']
    for i, color in enumerate(colors):
        size = 150 - i * 25
        draw.ellipse([center_x - size, center_y - size,
                      center_x + size, center_y + size], fill=color)

    # Lightning bolts (simplified)
    draw.line([(100, 50), (180, 150), (140, 150), (200, 250)], fill='#FFFFFF', width=3)
    draw.line([(500, 30), (450, 130), (480, 130), (400, 220)], fill='#FFFFFF', width=3)

    # Car silhouette being pulled in
    draw.polygon([(200, 200), (300, 180), (350, 200), (320, 260), (220, 260)], fill='#1A1A1A')

    # Energy particles
    for pos in [(50, 100), (580, 80), (100, 280), (550, 250), (300, 50)]:
        draw.ellipse([pos[0], pos[1], pos[0]+15, pos[1]+15], fill='#00C8FF')

    # Color annotations
    font = get_font(10)
    draw.text((10, HEIGHT-60), "ELECTRIC BLUE: Portal energy", fill='#00C8FF', font=font)
    draw.text((10, HEIGHT-45), "PURPLE: Supernatural magic", fill='#7B2FBE', font=font)
    draw.text((10, HEIGHT-30), "WHITE: Blinding intensity", fill='#FFFFFF', font=font)
    draw.text((10, HEIGHT-15), "Scene 5: TIME WARP", fill='white', font=get_font(11, bold=True))

    img.save(os.path.join(OUTPUT_DIR, "05-time-warp.png"))
    print("Created: 05-time-warp.png")


def create_jurassic_wonder_thumbnail():
    """Scene 7-8: Jurassic Wonder - Prehistoric beauty."""
    img = Image.new('RGB', (WIDTH, HEIGHT), color='#E6F2E6')
    draw = ImageDraw.Draw(img)

    # Misty sky
    draw.rectangle([0, 0, WIDTH, 100], fill='#D4E8D4')

    # Giant ferns (left and right)
    for x_base in [0, 550]:
        for y in range(50, 300, 40):
            draw.polygon([(x_base, y+40), (x_base+80, y), (x_base+60, y+40)], fill='#4A7C59')

    # Central clearing
    draw.ellipse([200, 150, 440, 350], fill='#8FBC8F')

    # Golden sunbeam
    draw.polygon([(320, 0), (250, 200), (390, 200)], fill='#FFD700')

    # Car wreck (small)
    draw.rectangle([280, 220, 360, 260], fill='#5C5C5C')

    # Parents tiny figures (silhouettes showing awe)
    draw.ellipse([300, 180, 320, 210], fill='#2C2C2C')
    draw.ellipse([340, 185, 355, 210], fill='#2C2C2C')

    # Mist layers
    for y in [280, 300, 320]:
        draw.rectangle([0, y, WIDTH, y+10], fill='#E6F2E6')

    # Color annotations
    font = get_font(10)
    draw.text((10, HEIGHT-60), "LUSH GREEN: Prehistoric life", fill='#4A7C59', font=font)
    draw.text((10, HEIGHT-45), "GOLDEN: Morning sun, hope", fill='#FFD700', font=font)
    draw.text((10, HEIGHT-30), "MIST: Atmosphere, mystery", fill='#8FBC8F', font=font)
    draw.text((10, HEIGHT-15), "Scenes 7-8: JURASSIC WONDER", fill='#2F4F2F', font=get_font(11, bold=True))

    img.save(os.path.join(OUTPUT_DIR, "07-jurassic-wonder.png"))
    print("Created: 07-jurassic-wonder.png")


def create_trex_reveal_thumbnail():
    """Scene 8: T-Rex Reveal - Terror moment."""
    img = Image.new('RGB', (WIDTH, HEIGHT), color='#1A2B1A')
    draw = ImageDraw.Draw(img)

    # Dark jungle background
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill='#1A2B1A')

    # Dark jungle shapes
    for x in range(0, WIDTH, 80):
        draw.polygon([(x, 0), (x+60, HEIGHT//2), (x+30, HEIGHT)], fill='#2F4F2F')

    # T-Rex silhouette (massive)
    draw.polygon([
        (350, 50),   # head top
        (450, 80),   # jaw
        (480, 150),  # neck
        (550, 200),  # back
        (600, 350),  # tail
        (400, 350),  # legs
        (380, 300),
        (320, 350),
        (280, 200),  # chest
        (300, 100),  # throat
    ], fill='#6B4423')

    # T-Rex eye (menacing)
    draw.ellipse([370, 60, 390, 80], fill='#FFE4B5')
    draw.ellipse([375, 65, 385, 75], fill='#8B0000')

    # Parents running (small, warm highlight)
    draw.ellipse([100, 280, 130, 320], fill='#E8A45C')
    draw.ellipse([140, 285, 165, 320], fill='#E8A45C')

    # Danger highlight on ground
    draw.rectangle([50, 320, 200, 350], fill='#8B0000')

    # Color annotations
    font = get_font(10)
    draw.text((10, HEIGHT-60), "DARK GREEN: Danger, shadows", fill='#3D5C3D', font=font)
    draw.text((10, HEIGHT-45), "WARM SKIN: Human vulnerability", fill='#FFE4B5', font=font)
    draw.text((10, HEIGHT-30), "RED EYE: Predator, threat", fill='#8B0000', font=font)
    draw.text((10, HEIGHT-15), "Scene 8: T-REX REVEAL", fill='white', font=get_font(11, bold=True))

    img.save(os.path.join(OUTPUT_DIR, "08-trex-reveal.png"))
    print("Created: 08-trex-reveal.png")


def create_ruben_magic_thumbnail():
    """Scene 20: Ruben's Magic - Fairy godfather introduction."""
    img = Image.new('RGB', (WIDTH, HEIGHT), color='#1A202C')
    draw = ImageDraw.Draw(img)

    # Dark police station interior
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill='#1A202C')

    # Fluorescent light strip
    draw.rectangle([200, 20, 440, 40], fill='#F5F5DC', outline='#4A5568', width=2)

    # Filing cabinets
    draw.rectangle([20, 100, 100, 300], fill='#4A5568')
    draw.rectangle([540, 100, 620, 300], fill='#4A5568')

    # Ruben with mop/wand (center)
    draw.ellipse([280, 150, 340, 200], fill='#C9A86C')  # head
    draw.rectangle([290, 200, 330, 300], fill='#5C5C5C')  # body

    # Magic mop with glow
    draw.line([(320, 180), (380, 100)], fill='#A0522D', width=5)
    draw.ellipse([365, 80, 400, 110], fill='#9F7AEA')  # magic glow

    # Sparkles around
    for pos in [(200, 100), (420, 150), (150, 200), (480, 120), (350, 80)]:
        draw.polygon([
            (pos[0], pos[1]-8),
            (pos[0]+4, pos[1]),
            (pos[0], pos[1]+8),
            (pos[0]-4, pos[1])
        ], fill='#FFD700')

    # Kids watching (small)
    draw.ellipse([180, 270, 210, 300], fill='#C9A86C')
    draw.ellipse([220, 275, 245, 300], fill='#C9A86C')

    # Color annotations
    font = get_font(10)
    draw.text((10, HEIGHT-60), "STATION GRAY: Mundane setting", fill='#4A5568', font=font)
    draw.text((10, HEIGHT-45), "FAIRY PURPLE: Magic possibility", fill='#9F7AEA', font=font)
    draw.text((10, HEIGHT-30), "GOLD SPARKLES: Hope emerging", fill='#FFD700', font=font)
    draw.text((10, HEIGHT-15), "Scene 20: RUBEN'S MAGIC", fill='white', font=get_font(11, bold=True))

    img.save(os.path.join(OUTPUT_DIR, "20-ruben-magic.png"))
    print("Created: 20-ruben-magic.png")


def create_chase_thumbnail():
    """Scenes 22-23: Chase Sequence - High energy escape."""
    img = Image.new('RGB', (WIDTH, HEIGHT), color='#16213E')
    draw = ImageDraw.Draw(img)

    # Night street background
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill='#16213E')

    # Road
    draw.polygon([(0, 280), (WIDTH, 280), (WIDTH, HEIGHT), (0, HEIGHT)], fill='#1A1A2E')
    draw.line([(WIDTH//2, 280), (WIDTH//2, HEIGHT)], fill='#FFE66D', width=3)

    # Police car (chasing)
    draw.rectangle([450, 230, 580, 280], fill='#4A5568')
    draw.ellipse([530, 210, 570, 230], fill='#E94560')  # red light
    draw.ellipse([460, 210, 500, 230], fill='#0F3460')  # blue light

    # Kids' car (fleeing)
    draw.rectangle([100, 230, 230, 280], fill='#4A5568')
    draw.rectangle([100, 280, 120, 310], fill='#1A1A1A')  # wheel
    draw.rectangle([210, 280, 230, 310], fill='#1A1A1A')  # wheel

    # Light streaks
    for y in [240, 260, 270]:
        draw.line([(250, y), (450, y)], fill='#FF6B6B', width=2)

    # Street lights (above)
    for x in [100, 300, 500]:
        draw.line([(x, 0), (x, 150)], fill='#2D3436', width=4)
        draw.ellipse([x-15, 140, x+15, 170], fill='#FFE66D')

    # Color annotations
    font = get_font(10)
    draw.text((10, HEIGHT-60), "RED/BLUE: Police pursuit", fill='#E94560', font=font)
    draw.text((10, HEIGHT-45), "NIGHT BLUE: Urban danger", fill='#0F3460', font=font)
    draw.text((10, HEIGHT-30), "YELLOW: Street lights, speed", fill='#FFE66D', font=font)
    draw.text((10, HEIGHT-15), "Scenes 22-23: CHASE SEQUENCE", fill='white', font=get_font(11, bold=True))

    img.save(os.path.join(OUTPUT_DIR, "22-chase-sequence.png"))
    print("Created: 22-chase-sequence.png")


def create_jetplane_colors_thumbnail():
    """Act 3: Jetplane's Rainbow Farts - Joy and wonder."""
    img = Image.new('RGB', (WIDTH, HEIGHT), color='#8FBC8F')
    draw = ImageDraw.Draw(img)

    # Jurassic jungle background
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill='#8FBC8F')

    # Trees/ferns
    for x in [0, 100, 500, 580]:
        draw.polygon([(x, HEIGHT), (x+50, 0), (x+100, HEIGHT)], fill='#4A7C59')

    # Jetplane creature (center-left)
    # Body
    draw.ellipse([120, 200, 220, 280], fill='#6B8E23')
    # Head
    draw.ellipse([80, 180, 140, 230], fill='#6B8E23')
    # Eye
    draw.ellipse([95, 190, 115, 210], fill='white')
    draw.ellipse([100, 195, 110, 205], fill='black')

    # Rainbow fart plumes!
    plume_colors = ['#FF6B6B', '#FFE66D', '#4ECDC4', '#9B59B6', '#3498DB']
    for i, color in enumerate(plume_colors):
        y_base = 230 - i * 15
        draw.ellipse([230 + i*40, y_base, 280 + i*40, y_base + 60], fill=color)
        draw.ellipse([260 + i*40, y_base - 20, 300 + i*40, y_base + 30], fill=color)

    # Leo nearby (amazed)
    draw.ellipse([80, 280, 110, 320], fill='#C9A86C')

    # Color annotations
    font = get_font(10)
    draw.text((10, HEIGHT-60), "RAINBOW: Joy, magic, surprise", fill='#FF6B6B', font=font)
    draw.text((10, HEIGHT-45), "GREEN: Prehistoric setting", fill='#4A7C59', font=font)
    draw.text((10, HEIGHT-30), "CANDY COLORS: Childlike wonder", fill='#4ECDC4', font=font)
    draw.text((10, HEIGHT-15), "Act 3: JETPLANE'S COLORS", fill='#2F4F2F', font=get_font(11, bold=True))

    img.save(os.path.join(OUTPUT_DIR, "30-jetplane-colors.png"))
    print("Created: 30-jetplane-colors.png")


def create_morning_resolution_thumbnail():
    """Epilogue: Morning - Full resolution and warmth."""
    img = Image.new('RGB', (WIDTH, HEIGHT), color='#FFE4B5')
    draw = ImageDraw.Draw(img)

    # Warm morning sky
    for y in range(0, HEIGHT//2, 10):
        shade = int(255 - y * 0.3)
        draw.rectangle([0, y, WIDTH, y+10], fill=(255, shade, shade-30))

    # Sun
    draw.ellipse([500, 20, 580, 100], fill='#FFD700')

    # House
    draw.polygon([(200, 180), (350, 80), (500, 180)], fill='#8B4513')  # roof
    draw.rectangle([220, 180, 480, 320], fill='#E8A45C')  # walls
    draw.rectangle([300, 220, 380, 320], fill='#5C3D2E')  # door
    draw.rectangle([240, 200, 290, 250], fill='#87CEEB')  # window
    draw.rectangle([400, 200, 450, 250], fill='#87CEEB')  # window

    # Chimney with rainbow plumes!
    draw.rectangle([420, 100, 450, 180], fill='#8B4513')
    plume_colors = ['#FF6B6B', '#FFE66D', '#4ECDC4', '#9B59B6', '#3498DB']
    for i, color in enumerate(plume_colors):
        draw.ellipse([425 + i*10, 60 - i*15, 455 + i*10, 100 - i*15], fill=color)

    # Family silhouettes in window
    for x in [255, 275, 410, 425]:
        draw.ellipse([x, 210, x+15, 240], fill='#5C3D2E')

    # Green lawn
    draw.rectangle([0, 320, WIDTH, HEIGHT], fill='#8FBC8F')

    # Color annotations
    font = get_font(10)
    draw.text((10, HEIGHT-60), "MORNING GOLD: New day, hope", fill='#E8A45C', font=font)
    draw.text((10, HEIGHT-45), "WARM HOUSE: Safety restored", fill='#8B4513', font=font)
    draw.text((10, HEIGHT-30), "RAINBOW: Magic is now home", fill='#4ECDC4', font=font)
    draw.text((10, HEIGHT-15), "Epilogue: NEW MORNING", fill='#5C3D2E', font=get_font(11, bold=True))

    img.save(os.path.join(OUTPUT_DIR, "99-morning-resolution.png"))
    print("Created: 99-morning-resolution.png")


def main():
    print("Generating annotated thumbnails...\n")

    create_home_evening_thumbnail()
    create_time_warp_thumbnail()
    create_jurassic_wonder_thumbnail()
    create_trex_reveal_thumbnail()
    create_ruben_magic_thumbnail()
    create_chase_thumbnail()
    create_jetplane_colors_thumbnail()
    create_morning_resolution_thumbnail()

    print(f"\nThumbnail generation complete!")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
