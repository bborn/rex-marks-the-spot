"""Composite the 4 Jetplane ortho view PNGs into a single turnaround sheet.

Layout: 2x2 grid (front, side, back, three_quarter), white background, labeled.
Output: asset-bible/characters/jetplane_turnaround.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
ALT = REPO / "asset-bible" / "characters" / "jetplane-alts"
OUT = REPO / "asset-bible" / "characters" / "jetplane_turnaround.png"

views = [
    ("front", "FRONT"),
    ("side", "SIDE"),
    ("back", "BACK"),
    ("three_quarter", "3/4"),
]

tile_w, tile_h = 800, 1000
pad = 20
label_h = 60
sheet_w = tile_w * 2 + pad * 3
sheet_h = (tile_h + label_h) * 2 + pad * 3

sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
draw = ImageDraw.Draw(sheet)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
except IOError:
    font = ImageFont.load_default()

for i, (key, label) in enumerate(views):
    src = ALT / f"jetplane_view_{key}.png"
    if not src.exists():
        raise FileNotFoundError(src)
    img = Image.open(src).convert("RGBA")
    # Flatten onto pure white (some views are RGBA with transparent edges).
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
    img = bg.resize((tile_w, tile_h), Image.LANCZOS)

    col = i % 2
    row = i // 2
    x = pad + col * (tile_w + pad)
    y = pad + row * (tile_h + label_h + pad)

    # Label.
    text_bbox = draw.textbbox((0, 0), label, font=font)
    tw = text_bbox[2] - text_bbox[0]
    draw.text((x + tile_w // 2 - tw // 2, y + 10), label, fill=(60, 60, 60), font=font)
    # Image below label.
    sheet.paste(img, (x, y + label_h))

# Header.
header = "JETPLANE — character turnaround (Blender ortho, working pick)"
text_bbox = draw.textbbox((0, 0), header, font=font)
tw = text_bbox[2] - text_bbox[0]
# Compose final with extra top header strip.
final_h = sheet_h + 80
final = Image.new("RGB", (sheet_w, final_h), (255, 255, 255))
draw2 = ImageDraw.Draw(final)
draw2.text((sheet_w // 2 - tw // 2, 20), header, fill=(30, 30, 30), font=font)
final.paste(sheet, (0, 80))

final.save(OUT, "PNG", optimize=True)
print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {final.size})")
