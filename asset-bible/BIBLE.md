# Asset Bible

**Status:** In progress
**Purpose:** Single locked source of truth for character and location references. All shot generation and validation must reference these locked assets.

R2 bucket root for the bible: `r2:rex-assets/asset-bible/`
Public R2 URL prefix: `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/`

---

## Characters

### LOCKED (approved turnarounds)

| Character | Server path | R2 URL |
|-----------|-------------|--------|
| Mia | `asset-bible/characters/mia_turnaround_APPROVED.png` | `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/mia_turnaround_APPROVED.png` |
| Leo | `asset-bible/characters/leo_turnaround_APPROVED.png` | `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/leo_turnaround_APPROVED.png` |
| Gabe | `asset-bible/characters/gabe_turnaround_APPROVED.png` | `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/gabe_turnaround_APPROVED.png` |
| Nina | `asset-bible/characters/nina_turnaround_APPROVED.png` | `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/nina_turnaround_APPROVED.png` |

### CANDIDATES (awaiting Bruno's pick — see "FOR BRUNO TO REVIEW" below)

| Character | Best candidate (R2 URL) | Alternatives directory |
|-----------|-------------------------|------------------------|
| Ruben | [ruben_turnaround.png](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/ruben_turnaround.png) | `asset-bible/characters/ruben-alts/` |
| Jetplane | _in progress (Blender ortho turnaround)_ | `asset-bible/characters/jetplane-alts/` |

### MISSING (need source art from Bruno)

- **Jenny** — no usable source art on disk. Cached/older docs describe her as blonde; the correct hair color is **DARK BROWN**.

---

## Locations

### CANDIDATES (awaiting Bruno's pick — one plate per location)

| Location | Best candidate (R2 URL) | Source |
|----------|-------------------------|--------|
| Family living room | [living_room.png](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/locations/living_room.png) | `assets/environments/bornsztein_home/bornsztein_home_living_room.png` |
| Magic minivan interior | [minivan.png](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/locations/minivan.png) | `assets/environments/family_car/family_car_interior.png` |
| Jurassic swamp / jungle | _in progress_ | |
| Cave hideout | _in progress_ | |

---

## Manifests

| File | Description |
|------|-------------|
| `asset-bible/manifests/scene-01.json` | 9 shots for Scene 1 (INT. HOME — EVENING). characters, wardrobe, key_props, camera, panel_url per shot. |

---

## How to use

When generating any shot, the pipeline MUST:

1. Look up the shot in the relevant `manifests/scene-XX.json`.
2. Use the locked character reference image(s) for every `characters[]` entry.
3. Use the locked location plate for the `location` value.
4. Include every `key_props` entry in the prompt and validate they survive into the final image.
5. Honor `wardrobe` per character.

Drift away from these locked refs is the bug we are preventing.
