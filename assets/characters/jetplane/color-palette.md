# Jetplane - Official Color Palette

## Primary Body Colors

### Main Scales
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Base | Soft Teal | #4DB6AC | 77, 182, 172 | Primary body color |
| Belly | Cream Yellow | #FFF8E1 | 255, 248, 225 | Underside |
| Back Ridge | Deeper Teal | #26A69A | 38, 166, 154 | Spines/scales |
| Shadow | Teal Shadow | #00897B | 0, 137, 123 | Depth areas |
| Highlight | Light Teal | #80CBC4 | 128, 203, 196 | Lit areas |

### Neck Ruff (Feathery Collar)
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Base | Warm Cream | #FFECB3 | 255, 236, 179 | Main ruff |
| Highlight | Soft White | #FFF8E1 | 255, 248, 225 | Tips |
| Shadow | Golden | #FFD54F | 255, 213, 79 | Depth |

### Tail
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Base | Body Teal | #4DB6AC | 77, 182, 172 | Matches body |
| Tuft | Warm Orange | #FFB74D | 255, 183, 77 | Tail tip fluff |
| Tuft Highlight | Light Orange | #FFCC80 | 255, 204, 128 | Lit areas |

---

## Facial Colors

### Eyes
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Iris | Bright Yellow | #FFEB3B | 255, 235, 59 | Main eye color (per script) |
| Iris Ring | Golden Yellow | #FDD835 | 253, 216, 53 | Outer definition |
| Pupil | Black | #1A1A1A | 26, 26, 26 | Large, round |
| Sclera | Soft White | #FFFEF5 | 255, 254, 245 | Eye whites |
| Catchlight 1 | Pure White | #FFFFFF | 255, 255, 255 | Main sparkle |
| Catchlight 2 | Soft White | #FFF8E1 | 255, 248, 225 | Secondary |
| Happy Sparkle | Pink | #FF80AB | 255, 128, 171 | Extra joy indicator |

### Mouth/Tongue
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Tongue | Healthy Pink | #F48FB1 | 244, 143, 177 | Occasionally visible |
| Mouth Interior | Soft Pink | #FFCDD2 | 255, 205, 210 | When open |
| Teeth | Off-White | #FFFEF5 | 255, 254, 245 | Small, not scary |

### Ear-Frills
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Base | Soft Coral | #FFAB91 | 255, 171, 145 | Main membrane |
| Edge | Warm Pink | #FF8A80 | 255, 138, 128 | Outer edge |
| Veins | Deeper Coral | #FF7043 | 255, 112, 67 | Subtle veining |
| Translucent | 80% opacity | - | - | Light passes through |

### Nose/Snout
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Nostrils | Dark Teal | #00796B | 0, 121, 107 | Small dots |
| Snout Tip | Slightly Pink | #B2DFDB | 178, 223, 219 | Lighter than body |

---

## Limb Colors

### Feet/Toe Beans
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Foot Top | Body Teal | #4DB6AC | 77, 182, 172 | Matches body |
| Toe Beans | Soft Pink | #FFCDD2 | 255, 205, 210 | Adorable pads |
| Claws | Cream | #FFECB3 | 255, 236, 179 | Not threatening |

### Arms/Hands
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Base | Body Teal | #4DB6AC | 77, 182, 172 | Matches body |
| Palm | Lighter | #80CBC4 | 128, 203, 196 | Inside |
| Claws | Cream | #FFECB3 | 255, 236, 179 | Small, cute |

---

## Rainbow Fart Colors

### The Full Spectrum
When Jetplane eats mixed candy or needs full rainbow:

| Color | Name | Hex Code | RGB |
|-------|------|----------|-----|
| Red | Cherry | #EF5350 | 239, 83, 80 |
| Orange | Tangerine | #FF7043 | 255, 112, 67 |
| Yellow | Lemon | #FFEE58 | 255, 238, 88 |
| Green | Lime | #66BB6A | 102, 187, 106 |
| Blue | Blueberry | #42A5F5 | 66, 165, 245 |
| Indigo | Grape | #5C6BC0 | 92, 107, 192 |
| Violet | Berry | #AB47BC | 171, 71, 188 |

### Single Color Farts (Based on Candy)
| Candy Eaten | Fart Color | Hex Code |
|-------------|------------|----------|
| Blue candy | Blue | #42A5F5 |
| Red candy | Red | #EF5350 |
| Yellow candy | Yellow | #FFEE58 |
| Purple candy | Purple | #AB47BC |
| Green candy | Green | #66BB6A |
| Orange candy | Orange | #FF7043 |
| Mixed/Rainbow | Full spectrum | (all) |

### Fart Cloud Effects
| Element | Color Name | Hex Code | Usage |
|---------|------------|----------|-------|
| Sparkle | Gold glitter | #FFD700 | Magical particles |
| Glow | White core | #FFFFFF | Luminance |
| Trail | Fading color | varies | Dissipation |

---

## Emotional Color Variations

### Happy/Excited
- Body slightly more saturated
- Eyes extra sparkly (add pink catchlight)
- Ear-frills flush pinker

### Scared
- Body slightly desaturated
- Eyes enlarged, more white showing
- Ear-frills pale

### Brave/Heroic
- Body saturated and warm
- Eyes intense yellow
- Overall slight golden glow

---

## Size Form Differences

### Small Form
- Standard saturation
- Soft, plush appearance
- Cuter proportions

### Large Form
- Slightly more saturated/vibrant
- More defined muscle shading
- Same overall palette

---

## Technical Notes

### For 3D Rendering

#### Skin/Scales
- Subsurface scattering: Light value for translucency
- Slight iridescence on scales
- Roughness: 0.6-0.7 (soft look)

#### Eyes
- High gloss (0.1 roughness)
- Subsurface for depth
- Multiple procedural catchlights
- Ambient occlusion in corners

#### Ear-Frills
- Translucent shader
- Backlit capability (light through membrane)
- Vein normal map

#### Neck Ruff
- Feather-like displacement
- Soft falloff
- Reacts to wind/movement

#### Rainbow Farts
- Particle system with color gradient
- Glow/bloom in post
- Sparkle particles
- Dissipation over distance

### For 2D Concept Art
- Keep saturation consistent
- Eyes are focal point
- Belly always lighter
- Ear-frills should read even in silhouette
- Rainbow farts: magical, not gross

### Merchandise Color Specifications
For consistent reproduction across merchandise:

| Item | Notes |
|------|-------|
| Plush | Use Pantone equivalents for fabric |
| Action Figures | Paint chips for approval |
| Print | CMYK conversion needed |
| Digital | Use hex codes directly |
