# Asset Bible

**Status:** Locked - 7 character turnarounds + 4 location plates + Scene 1 manifest
**Purpose:** Single locked source of truth for character and location references. All shot generation and validation MUST reference these locked assets. Drift away from them is the bug this pipeline exists to prevent.

- R2 bucket root: `r2:rex-assets/asset-bible/`
- Public URL prefix: `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/`

The character turnarounds are the canonical "character lock" set (locked 2026-02-07), also published per-character at `r2:rex-assets/characters/<name>/<name>_turnaround_APPROVED.png`. That per-character path is the upstream source of truth - always check it before generating a new turnaround.

---

## Characters - all 7 LOCKED

| Character | Bible path | R2 URL |
|-----------|------------|--------|
| Mia | `asset-bible/characters/mia_turnaround_APPROVED.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/mia_turnaround_APPROVED.png |
| Leo | `asset-bible/characters/leo_turnaround_APPROVED.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/leo_turnaround_APPROVED.png |
| Gabe | `asset-bible/characters/gabe_turnaround_APPROVED.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/gabe_turnaround_APPROVED.png |
| Nina | `asset-bible/characters/nina_turnaround_APPROVED.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/nina_turnaround_APPROVED.png |
| Jenny | `asset-bible/characters/jenny_turnaround_APPROVED.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/jenny_turnaround_APPROVED.png |
| Ruben | `asset-bible/characters/ruben_turnaround_APPROVED.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/ruben_turnaround_APPROVED.png |
| Jetplane | `asset-bible/characters/jetplane_turnaround_APPROVED.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/characters/jetplane_turnaround_APPROVED.png |

Note: Mia also has an animation-friendly variant `mia_turnaround_APPROVED_ALT.png` (in `r2:rex-assets/characters/mia/`). Per CLAUDE.md, use the ALT for 3D/animation work; the standard APPROVED above is the identity reference for validation.

---

## Locations - 4 plates LOCKED

| Location | Bible path | R2 URL |
|----------|------------|--------|
| Family living room | `asset-bible/locations/living_room.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/locations/living_room.png |
| Magic minivan interior | `asset-bible/locations/minivan.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/locations/minivan.png |
| Jurassic swamp / jungle | `asset-bible/locations/swamp.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/locations/swamp.png |
| Cave hideout | `asset-bible/locations/cave.png` | https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/asset-bible/locations/cave.png |

Location plates were selected from existing canonical environment art. If a canonical "location lock" set is later confirmed, replace these from that source.

---

## Manifests

| File | Description |
|------|-------------|
| `asset-bible/manifests/scene-01.json` | 9 shots for Scene 1 (INT. HOME - EVENING). Per shot: characters, per-character wardrobe, key_props, camera, panel_url. |

---

## How to use

When generating any shot, the pipeline MUST:

1. Look up the shot in the relevant `manifests/scene-XX.json`.
2. Use the locked character turnaround for every `characters[]` entry - for IDENTITY (face, hair, build) only.
3. Use the locked location plate for the `location` value.
4. Take per-character clothing from the manifest `wardrobe` field, NOT from the turnaround (a turnaround is an identity card, not a dress code).
5. Include every `key_props` entry and validate they survive into the final image.
