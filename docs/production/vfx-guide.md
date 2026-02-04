# VFX Production Guide - Fairy Dinosaur Date Night

## Overview

This guide documents the visual effects required for the film, covering the four primary magic effect categories. Each section includes color specifications, Blender shader setups, and animation guidelines.

---

## 1. Fairy Dust Particles

Fairy dust is Ruben's signature magic effect. It has two distinct states: **Failed Magic** (when spells don't work) and **Working Magic** (successful spells).

### Color Palette

#### Failed Magic (Fizzle State)
| Element | Hex Code | RGB | Description |
|---------|----------|-----|-------------|
| Weak Spark | #FDE68A | 253, 230, 138 | Initial fizzle glow |
| Gray Smoke | #9CA3AF | 156, 163, 175 | Dissipating failure |
| Orange Sputter | #FB923C | 251, 146, 60 | Misfire crackle |

#### Working Magic (Success State)
| Element | Hex Code | RGB | Description |
|---------|----------|-----|-------------|
| Primary Blue | #60A5FA | 96, 165, 250 | Main fairy glow |
| Secondary Purple | #A78BFA | 167, 139, 250 | Accent swirl |
| Gold Sparkle | #FBBF24 | 251, 191, 36 | Classic fairy dust |
| White Core | #FFFFFF | 255, 255, 255 | Power center |

### Blender Setup

#### Particle System Configuration

```python
# Fairy Dust Particle Settings
particle_settings = {
    'count': 500,          # Working magic: 500, Failed: 150
    'lifetime': 60,        # frames
    'emit_from': 'VOLUME',
    'physics_type': 'NEWTON',
    'mass': 0.001,
    'drag': 0.1,
    'brownian': 0.8,       # Random floating motion
}

# Emission over time (keyframed)
# Working magic: sustained emission
# Failed magic: sharp burst then nothing
```

#### Shader Node Setup (Fairy Dust Particle Material)

1. **Principled BSDF** + **Emission** mix
2. Add **Gradient Texture** mapped to particle age
3. Use **ColorRamp** with gold (#FBBF24) to transparent
4. **Emission Strength**: 5.0 for working, 0.8 for failed

```
[Particle Info] --> [Math: Age/Lifetime] --> [ColorRamp] --> [Mix Shader]
                                                              |
                                    [Principled BSDF] --------|
                                    [Emission Shader] --------|
                                              |
                                    [Material Output]
```

#### Key Animation Notes
- **Working magic**: Particles spiral upward, linger, then fade
- **Failed magic**: Particles fall immediately, sputter out with smoke puff
- **Timing**: Working magic = sustained 2-3 seconds, Failed = 0.5 seconds

---

## 2. Mop-Wand Glow Effects

Ruben's mop functions as his wand. The glow state indicates magic readiness and success.

### Color Palette

| State | Hex Code | RGB | Description |
|-------|----------|-----|-------------|
| Idle (Tarnished) | #B8960B | 184, 150, 11 | No active magic |
| Charging | #FBBF24 | 251, 191, 36 | Building power |
| Active (Working) | #60A5FA | 96, 165, 250 | Spell casting |
| Misfire | #FB923C | 251, 146, 60 | Spell failing |
| Full Power | #FFFFFF | 255, 255, 255 | Heroic moment core |

### Blender Setup

#### Light Configuration

Create a point light parented to the mop handle tip:

```python
# Mop-Wand Light Settings
light_settings = {
    'type': 'POINT',
    'energy_idle': 50,
    'energy_active': 500,
    'energy_heroic': 2000,
    'color_idle': (0.72, 0.59, 0.04),      # #B8960B
    'color_active': (0.38, 0.65, 0.98),    # #60A5FA
    'color_heroic': (1.0, 1.0, 1.0),       # #FFFFFF
    'radius': 0.3,
    'shadow_soft_size': 0.5,
}
```

#### Shader Node Setup (Mop Handle Material)

Layer emission over the base material:

```
[Object Info: Random] --> [Mix RGB] --> [Emission] --> [Mix Shader] --> [Output]
                              |                            |
               [Noise Texture] |              [Base Material]
                              |
        (Creates magical flickering)
```

#### Glow Post-Processing (Compositing)
1. Render mop with **Object Index** pass
2. Use **ID Mask** to isolate mop
3. Apply **Glare** node (Fog Glow, size 8, threshold 0.5)
4. Composite back with **Add** blend mode

---

## 3. Portal / Time Warp Effects

The time warp is the central VFX piece - a swirling blue vortex of energy.

### Color Palette

| Element | Hex Code | RGB | Description |
|---------|----------|-----|-------------|
| Core | #FFFFFF | 255, 255, 255 | Bright center |
| Inner Ring | #93C5FD | 147, 197, 253 | Light blue |
| Middle Ring | #60A5FA | 96, 165, 250 | Primary blue |
| Outer Ring | #3B82F6 | 59, 130, 246 | Deeper blue |
| Edge Glow | #1D4ED8 | 29, 78, 216 | Dark blue outline |
| Lightning | #A78BFA | 167, 139, 250 | Purple accents |
| Particle Debris | #FBBF24 | 251, 191, 36 | Golden sparks |

### Portal States

1. **Opening**: Expanding from a point, energy crackling
2. **Stable**: Spinning vortex, roughly backpack-sized (per screenplay)
3. **Active (Transportation)**: Full size, pulling effect
4. **Closing**: Shrinking, flickering, urgent

### Blender Setup

#### Geometry

1. Create a **Circle mesh** (32 vertices)
2. Extrude inward multiple times for concentric rings
3. Add **Subdivision Surface** modifier (level 2)
4. Apply **Displace** modifier with animated noise texture

#### Shader Node Setup (Portal Material)

```
[Texture Coordinate] --> [Mapping: Animated Rotation] --> [Gradient Texture: Radial]
                                                                    |
                                                          [ColorRamp: Blue gradient]
                                                                    |
[Noise Texture] ----> [Mix RGB] -----------------------------------|
                          |                                        |
                    [Wave Texture: Spiral]                   [Emission]
                                                                    |
                                                        [Material Output]
```

#### Animation Requirements

```python
# Portal Rotation Animation
portal_rotation = {
    'axis': 'Z',
    'speed': 360,      # degrees per 4 seconds (stable)
    'speed_closing': 720,  # faster when closing
    'noise_influence': 0.3,  # wobble
}

# Shader animation (keyframe texture offset)
# Animate Mapping node Z-rotation: 0 to 360 over 120 frames
```

#### Particle System (Portal Debris)

```python
portal_particles = {
    'type': 'EMITTER',
    'count': 200,
    'lifetime': 30,
    'emit_from': 'EDGE',
    'velocity_normal': -2.0,  # Pull toward center
    'velocity_tangent': 5.0,  # Spiral motion
    'field_type': 'VORTEX',
    'field_strength': 10.0,
}
```

#### Reference
See existing concept art: `assets/environments/time_warp_effect/`

---

## 4. Jetplane Rainbow Fart Trails

The signature comedic effect - colorful gas plumes from Jetplane based on candy consumption.

### Color Palette (Full Rainbow Spectrum)

| Color | Name | Hex Code | RGB | Candy Source |
|-------|------|----------|-----|--------------|
| Red | Cherry | #EF5350 | 239, 83, 80 | Red candy |
| Orange | Tangerine | #FF7043 | 255, 112, 67 | Orange candy |
| Yellow | Lemon | #FFEE58 | 255, 238, 88 | Yellow candy |
| Green | Lime | #66BB6A | 102, 187, 106 | Green candy |
| Blue | Blueberry | #42A5F5 | 66, 165, 245 | Blue candy |
| Indigo | Grape | #5C6BC0 | 92, 107, 192 | Mixed |
| Violet | Berry | #AB47BC | 171, 71, 188 | Purple candy |

### Effect Characteristics

Per screenplay: The farts are **visible colored plumes** that:
- Rise upward into the sky
- Can be seen from distance (used as signal)
- Sequence matches candy eaten (blue-red-blue = blue, red, blue farts)
- Are comedic but not gross - more magical than biological

### Blender Setup

#### Smoke/Fluid Simulation

Use Blender's **Quick Smoke** or **Mantaflow** for realistic plumes:

```python
smoke_domain_settings = {
    'resolution': 128,
    'time_scale': 0.8,        # Slightly slower for magical feel
    'vorticity': 0.5,
    'buoyancy_density': -0.5,  # Rise upward
    'dissolve_speed': 60,      # Fade over time
}

smoke_flow_settings = {
    'flow_type': 'SMOKE',
    'surface_distance': 0.5,
    'initial_velocity': (0, 0, 3.0),  # Upward burst
    'temperature': 1.5,
}
```

#### Color Control (Per-Fart)

Animate the **Color Grid** attribute or use material nodes:

```
[Attribute: density] --> [Math: Greater Than 0.1] --> [Mix Shader]
                                                          |
                              [Principled Volume] --------|
                              (Base color animated)       |
                                                          |
                              [Emission: Glow] -----------|
                                                          |
                                              [Volume Output]
```

#### Material Shader (Rainbow Fart Cloud)

```python
# Animated color based on frame/sequence
# Keyframe the Principled Volume color:

frame_0:   color = (0.26, 0.65, 0.96, 1.0)   # Blue #42A5F5
frame_30:  color = (0.94, 0.33, 0.31, 1.0)   # Red #EF5350
frame_60:  color = (0.26, 0.65, 0.96, 1.0)   # Blue again
```

#### Sparkle Particles

Add a secondary particle system for magical sparkles within the cloud:

```python
sparkle_settings = {
    'count': 50,
    'lifetime': 20,
    'size': 0.02,
    'emit_from': 'VOLUME',  # Inside smoke domain
    'material': 'gold_sparkle',  # #FFD700
}
```

#### Animation Timing

| Event | Duration | Notes |
|-------|----------|-------|
| Initial burst | 10 frames | Fast expansion |
| Rise phase | 60 frames | Upward motion |
| Dissipation | 30 frames | Fade to transparent |
| Total visible | ~100 frames | 4 seconds at 24fps |

---

## 5. Compositing & Post-Processing

### Render Passes Required

1. **Combined** - Main render
2. **Emit** - Isolate glowing elements
3. **Mist** - Depth for volumetrics
4. **Object Index** - Per-object glow control

### Glow/Bloom Pipeline

```
[Render Layers] --> [Glare: Fog Glow] --> [Mix: Add] --> [Composite]
                          |
                    Size: 8
                    Threshold: 0.8
                    Quality: High
```

### Color Grading

- Magic scenes: Boost blue channel slightly (+5%)
- Failed magic: Desaturate (-15%)
- Heroic moments: Increase contrast, warm highlights

---

## 6. Asset References

### Existing Concept Art

| Effect | Location | Status |
|--------|----------|--------|
| Time Warp Tunnel | `assets/environments/time_warp_effect/time_warp_effect_tunnel.png` | Complete |
| Small Portal | `assets/environments/time_warp_effect/time_warp_effect_small_portal.png` | Complete |
| Closing Portal | `assets/environments/time_warp_effect/time_warp_effect_closing_portal.png` | Complete |

### VFX Concept Art

| Effect | Location | Status |
|--------|----------|--------|
| Mop-Wand Glow (Working) | `assets/vfx/concepts/mop_wand_glow_working.png` | Complete |
| Fairy Dust - Failed | `assets/vfx/concepts/fairy_dust_failed.png` | Complete |
| Portal/Time Warp | `assets/vfx/concepts/portal_time_warp.png` | Complete |
| Rainbow Fart Trail | `assets/vfx/concepts/rainbow_fart_trail.png` | Complete |

### Character References

- Ruben magic colors: `assets/characters/ruben/color-palette.md`
- Jetplane fart colors: `assets/characters/jetplane/color-palette.md`

---

## 7. Scene-by-Scene VFX Breakdown

### Act 1

| Scene | Effect | Notes |
|-------|--------|-------|
| EXT. ROAD - NIGHT | Time Warp Opening | Massive, violent, lit by lightning |
| INT. HOUSE | TV Explosion Poof | Small magical burst |
| EXT. JURASSIC SWAMP | Small Portal (residual) | Backpack-sized, slowly closing |

### Act 2

| Scene | Effect | Notes |
|-------|--------|-------|
| INT. POLICE STATION | Ruben's Failed Magic | Squeaky wheel, ceiling hole, door jam |
| INT. POLICE STATION | Ruben's Working Magic | Freeze spell on McNattin |
| Chase Sequence | Mop-Wand Ignition | Car start spell |
| EXT. JURASSIC FOREST | Rainbow Fart Signals | Blue-red-blue sequence |
| CANYON BRIDGE | Magic Bridge Creation | Crayons + hair binder transformation |
| CANYON | Leo Rescue | Levitation spell (working!) |

### Act 3

| Scene | Effect | Notes |
|-------|--------|-------|
| CANYON EDGE | Teleportation Spell | Blue mist, group transport |
| EXT. SWAMP | Giant Jetplane Transformation | Bigitty saurus spell |
| EXT. STREET | Shrink Spell | Dibitty saurus |
| Final Scene | Chimney Fart Plumes | Comedic ending rainbow |

---

## 8. Technical Specifications

### Resolution & Frame Rate
- **Render Resolution**: 1920x1080 (HD) or 3840x2160 (4K)
- **Frame Rate**: 24fps
- **Samples**: 256 minimum for volumetrics

### Performance Optimization

1. **Portals**: Bake particle simulations
2. **Smoke/Farts**: Cache fluid simulations
3. **Fairy Dust**: Use particle instancing
4. **Compositing**: Render VFX on separate layers

### File Naming Convention

```
[effect-type]_[state]_[frame-range].exr

Examples:
portal_opening_001-120.exr
fairy_dust_working_001-060.exr
rainbow_fart_blue_001-100.exr
```

---

## 9. Quick Reference Cards

### Ruben's Magic Color Quick Reference

```
FAILED:   Spark #FDE68A → Smoke #9CA3AF → Sputter #FB923C
WORKING:  Core #FFFFFF → Blue #60A5FA → Purple #A78BFA → Gold #FBBF24
```

### Portal Color Quick Reference

```
CENTER → EDGE:  #FFFFFF → #93C5FD → #60A5FA → #3B82F6 → #1D4ED8
```

### Rainbow Fart Quick Reference

```
R:#EF5350  O:#FF7043  Y:#FFEE58  G:#66BB6A  B:#42A5F5  I:#5C6BC0  V:#AB47BC
```
