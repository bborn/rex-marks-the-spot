# Leo Bornsztein - Official Color Palette

## Primary Colors

### Hair
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Base | Chestnut Brown | #8B5A2B | 139, 90, 43 | Main hair color (matches Mia) |
| Highlight | Warm Caramel | #C4956A | 196, 149, 106 | Sun-lit cowlicks |
| Shadow | Dark Umber | #5C3317 | 92, 51, 23 | Depth areas |

### Skin Tone
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Base | Warm Peach | #F5D0B5 | 245, 208, 181 | Main skin (matches Mia) |
| Blush | Rose Pink | #ECA5A5 | 236, 165, 165 | Cheeks (more prominent than Mia) |
| Freckles | Soft Tan | #C9956C | 201, 149, 108 | Nose and cheeks |
| Shadow | Warm Shadow | #D4A574 | 212, 165, 116 | Shaded areas |
| Highlight | Cream | #FFF5E6 | 255, 245, 230 | Lit areas |

### Eyes
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Iris | Warm Brown | #6B4423 | 107, 68, 35 | Main eye color (family match) |
| Iris Highlight | Amber | #A67B3D | 166, 123, 61 | Wonder effect |
| Pupil | Deep Black | #1A1A1A | 26, 26, 26 | Center |
| Sclera | Soft White | #FFFEF5 | 255, 254, 245 | Larger visible area due to big eyes |
| Catchlight | Pure White | #FFFFFF | 255, 255, 255 | Multiple for "sparkle" effect |
| Tear | Clear Blue | #C5E1F5 | 197, 225, 245 | Watery eyes moments |

---

## Costume Colors

### Primary Outfit (Adventure)

#### Green Dinosaur T-Shirt
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Base | Bright Green | #22C55E | 34, 197, 94 | Main shirt color |
| Shadow | Forest Green | #16A34A | 22, 163, 74 | Folds |
| Highlight | Lime | #4ADE80 | 74, 222, 128 | Lit areas |
| Dino Graphic | Orange | #F97316 | 249, 115, 22 | T-Rex print |
| Dino Outline | Dark Brown | #78350F | 120, 53, 15 | Graphic detail |

#### Khaki Cargo Shorts
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Base | Khaki | #C4A76C | 196, 167, 108 | Main color |
| Shadow | Dark Khaki | #A08850 | 160, 136, 80 | Pockets, folds |
| Highlight | Light Khaki | #D4C090 | 212, 192, 144 | Worn areas |
| Button | Brass | #B5894E | 181, 137, 78 | Pocket buttons |

#### Sneakers
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Main | Bright Blue | #3B82F6 | 59, 130, 246 | Shoe upper |
| Accent | Vibrant Orange | #F97316 | 249, 115, 22 | Stripes, velcro |
| Sole | Off-White | #F5F5F5 | 245, 245, 245 | Rubber sole |
| Velcro | Gray | #9CA3AF | 156, 163, 175 | Straps |

### Toy Dinosaur (Signature Prop)
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Body | Toy Green | #34D399 | 52, 211, 153 | Plastic body |
| Spots | Bright Yellow | #FBBF24 | 251, 191, 36 | Decorative dots |
| Eyes | Black Bead | #1F2937 | 31, 41, 55 | Toy eyes |

---

## Pajama Colors (Opening Scene)
| Element | Color Name | Hex Code | RGB | Usage |
|---------|------------|----------|-----|-------|
| Base | Sunny Yellow | #FDE047 | 253, 224, 71 | Main fabric |
| Pattern | Navy Blue | #1E3A5F | 30, 58, 95 | Rocket ships |
| Pattern Accent | Red | #EF4444 | 239, 68, 68 | Rocket flames |
| Cuffs | Orange Trim | #FB923C | 251, 146, 60 | Collar/cuffs |

---

## Emotional Color Notes

### Blush Increase
- Fear: Blush reduces, slight pale
- Crying: Blush increases significantly, nose reddens
- Embarrassment: Ears and cheeks flush
- Cold: Blue tint to lips and nose

### Tear Rendering
- Tears catch light with high specularity
- Track marks show on cheeks
- Eyes redden slightly around when crying

### Freckle Visibility
- More visible in bright light
- Subtle in shadows
- Never disappear entirely

---

## Color Harmony

### Sibling Connection
- Same hair color as Mia (family)
- Same eye color (family)
- Same skin tone (family)
- Different costume colors (individual identity)

### With Mia
- His green complements her purple (opposite spectrum)
- Creates visual balance in two-shots
- Easy to distinguish in group scenes

### With Jetplane
- Leo's green shirt connects to Jetplane's scales
- Orange accents echo Jetplane's warm tones
- Natural visual pairing for their friendship

---

## Technical Notes

### For 3D Rendering
- Subsurface scattering: Higher than Mia (softer, more translucent child skin)
- Hair needs chaos - multiple control points for cowlicks
- Freckles via texture map, not geometry
- Big eyes need large, clear catchlights

### Tear Rendering
- Transparent shader with fresnel
- Slight blue tint in shadows
- High glossiness for fresh tears
- Matte for tear tracks (dried)

### For 2D Concept Art
- Emphasize roundness in all shapes
- Larger head proportion than Mia
- Eyes should dominate face
- Freckles placed in consistent pattern
