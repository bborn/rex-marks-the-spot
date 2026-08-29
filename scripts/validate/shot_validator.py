"""
Reference-aware shot validator.

Compares a generated shot (video file or still image) against:
  - the shot's entry in asset-bible/manifests/scene-XX.json
  - locked character turnarounds for each character in the shot
  - a locked location plate (or storyboard panel) for the shot's location
  - optionally, the previous shot's final keyframe for continuity

For a video, three keyframes are extracted (first / middle / last) with
ffmpeg, then each is graded by Claude vision against all reference images.
Returns structured JSON per keyframe and an aggregated pass/fail.

Usage:
  # validate a single shot
  python scripts/validate/shot_validator.py validate-shot \\
      --manifest asset-bible/manifests/scene-01.json \\
      --shot-id 1A \\
      --footage footage/scene-01/shots/01-shot-1A.mp4 \\
      --characters-dir asset-bible/characters \\
      --locations-dir asset-bible/locations \\
      --out reports/scene-01-1A.json

  # validate every shot in a manifest + render a markdown report
  python scripts/validate/shot_validator.py validate-scene \\
      --manifest asset-bible/manifests/scene-01.json \\
      --footage-dir footage/scene-01/shots \\
      --characters-dir asset-bible/characters \\
      --locations-dir asset-bible/locations \\
      --report reports/scene-01-validation.md
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Vision-backend wiring
#
# The validator supports two interchangeable vision backends:
#   - "claude"  - Anthropic Claude with vision + forced tool use
#   - "gemini"  - Google Gemini with response_schema for structured JSON
#
# Both implement the same _Backend protocol below. The same rubric prompt is
# sent to either model; only the structured-output mechanism differs.
# ---------------------------------------------------------------------------

DEFAULT_BACKEND = "claude" if os.environ.get("ANTHROPIC_API_KEY") else "gemini"
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-5"
# gemini-2.5-flash was the previous default and is NOT fit for this job: on the
# adversarial control set it returned identity 1.00 on all 11 cases, including
# one where the wrong person's turnaround was supplied as the reference.
# gemini-3-flash-preview reproduces the control table exactly, at a comparable
# price. See scripts/validate/controls/ and
# docs/research/identity-validator-repair.md.
DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"

CREDENTIALS_PATH = Path.home() / ".claude" / ".credentials.json"

# Pricing for cost estimation (USD per 1M tokens).
PRICING = {
    "claude-sonnet-4-5":      {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output":  5.00},
    "gemini-2.5-flash":       {"input": 0.30, "output":  2.50},
    "gemini-2.5-pro":         {"input": 1.25, "output": 10.00},
    # Gemini 3 Flash preview pricing was not published on a rate card we could
    # cite at the time of writing, so it is estimated at the 2.5 Flash rate.
    # Token counts are exact in every report; only the dollar conversion is an
    # assumption. If it turns out to price like 2.5 Pro instead, multiply the
    # per-image figure by ~4 (still well under a cent a panel).
    "gemini-3-flash-preview": {"input": 0.30, "output":  2.50},
}


def _get_anthropic_client():
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return anthropic.Anthropic(api_key=api_key)

    if CREDENTIALS_PATH.exists():
        with open(CREDENTIALS_PATH) as f:
            creds = json.load(f)
        oauth = creds.get("claudeAiOauth", {}).get("accessToken")
        if oauth:
            return anthropic.Anthropic(auth_token=oauth)

    raise RuntimeError(
        "No Anthropic credentials available: set ANTHROPIC_API_KEY or "
        f"ensure {CREDENTIALS_PATH} contains a Claude OAuth accessToken."
    )


def _get_gemini_client():
    from google import genai  # type: ignore
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment.")
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# Image / video helpers
# ---------------------------------------------------------------------------

def _sniff_media_type(raw: bytes, path: Path) -> str:
    """Detect image type by magic bytes; fall back to extension.

    Some files in our pipeline have ``.png`` extensions but are actually
    JPEG payloads, which the Anthropic API rejects when the declared
    media_type does not match the bytes.
    """
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith(b"GIF87a") or raw.startswith(b"GIF89a"):
        return "image/gif"
    if raw[0:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    # Fall back to extension
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "image/png")


# Max edge length when downsizing images before sending to Claude. Claude's
# vision tokenizer scales with pixels, and 1.6k is plenty of detail to spot
# hair/wardrobe/face drift while staying well under the API limits.
_MAX_IMAGE_EDGE = 1600


def _encode_image(path: Path) -> dict:
    """Return an Anthropic image content block for the given path.

    Images are downsized to at most _MAX_IMAGE_EDGE on the long side and
    re-encoded as JPEG to keep request payloads small. The media_type is
    detected from the original bytes' magic header (some files have a
    .png extension but JPEG bytes).
    """
    from PIL import Image

    with open(path, "rb") as f:
        raw = f.read()

    img = Image.open(io.BytesIO(raw))
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    w, h = img.size
    long_edge = max(w, h)
    if long_edge > _MAX_IMAGE_EDGE:
        scale = _MAX_IMAGE_EDGE / float(long_edge)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    encoded = buf.getvalue()
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": base64.standard_b64encode(encoded).decode("utf-8"),
        },
    }


def _video_duration(video_path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        str(video_path),
    ], text=True).strip()
    return float(out)


def extract_keyframes(video_path: Path, out_dir: Path) -> list[Path]:
    """Extract first / middle / last keyframes from a video to JPEGs.

    Returns the three image paths in temporal order. Uses ffmpeg in two
    modes: regular seek for first/middle, and `-sseof` (seek-from-end)
    for the last frame, which is reliable on short clips where ``-ss``
    near the duration can run past the last decoded frame.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    duration = _video_duration(video_path)
    stem = video_path.stem

    first_ts = 0.0
    mid_ts = max(duration / 2.0, 0.0)

    paths: list[Path] = []
    # first + middle: standard seek-before-input is fine
    for label, ts in [("first", first_ts), ("mid", mid_ts)]:
        out = out_dir / f"{stem}-{label}.jpg"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", f"{ts:.3f}",
            "-i", str(video_path),
            "-frames:v", "1",
            "-q:v", "3",
            str(out),
        ], check=True)
        if not out.exists():
            raise RuntimeError(f"ffmpeg did not produce keyframe at t={ts:.3f}s for {video_path}")
        paths.insert(len(paths), out)

    # last: seek from end of file, take 1 frame past that point
    last_out = out_dir / f"{stem}-last.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-sseof", "-0.5",
        "-i", str(video_path),
        "-update", "1",
        "-q:v", "3",
        str(last_out),
    ], check=True)
    if not last_out.exists():
        # Final fallback: slow seek (after -i) to duration-0.1s.
        fallback_ts = max(duration - 0.1, 0.0)
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(video_path),
            "-ss", f"{fallback_ts:.3f}",
            "-frames:v", "1",
            "-q:v", "3",
            str(last_out),
        ], check=True)
    if not last_out.exists():
        raise RuntimeError(f"ffmpeg could not extract last frame of {video_path}")
    paths.append(last_out)
    return paths


# ---------------------------------------------------------------------------
# Reference resolution
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    return name.lower().strip()


def resolve_character_refs(
    characters: list[str],
    characters_dir: Path,
) -> tuple[dict[str, Path], list[str]]:
    """Map character names to turnaround image paths.

    Returns (resolved, unresolved_names).
    """
    resolved: dict[str, Path] = {}
    missing: list[str] = []
    if not characters_dir.exists():
        return resolved, list(characters)
    files = list(characters_dir.iterdir())
    for ch in characters:
        slug = _slug(ch)
        match = None
        for f in files:
            if not f.is_file():
                continue
            stem = f.stem.lower()
            if stem.startswith(slug + "_") or stem == slug or stem.startswith(slug + "-"):
                match = f
                break
        if match:
            resolved[ch] = match
        else:
            missing.append(ch)
    return resolved, missing


def resolve_location_ref(
    shot: dict,
    locations_dir: Path,
) -> Optional[Path]:
    """Find a location reference for this shot.

    Strategy: if locations_dir has 'storyboard-<SHOTID>.png', use that; else
    fall back to 'storyboard-1A.png' (provisional living_room plate).
    """
    if not locations_dir.exists():
        return None
    candidate = locations_dir / f"storyboard-{shot['shot_id']}.png"
    if candidate.exists():
        return candidate
    fallback = locations_dir / "storyboard-1A.png"
    if fallback.exists():
        return fallback
    return None


# ---------------------------------------------------------------------------
# Vision validation
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Identity: observation-first grading
#
# The previous version of this file asked the vision model to look at a
# turnaround, look at a keyframe, and emit a 0-1 identity score. It returned
# 1.00 for every character on every shot, including a control where Jenny's
# turnaround was supplied as the reference for Nina. The notes were boilerplate
# with the name swapped. See docs/research/identity-validator-repair.md.
#
# The model no longer emits an identity score. It fills in two tables of
# ENUMERATED observations - what the keyframe shows, and what the turnaround
# shows - and the diff, the classification and the score are computed here, in
# Python, from those two tables. A grader that never emits a score cannot
# rubber-stamp one, and every score is now traceable to the two attribute rows
# it came from.
# ---------------------------------------------------------------------------

# Each attribute is an ordinal ladder of enumerated values. "distance" is how
# far apart two observations sit on that ladder; `defining_at` is the distance
# at which a difference stops being explicable by lighting, pose or framing and
# starts meaning the character was drawn differently.
#
#   defining_at = 1  ->  any difference at all is a design difference
#   defining_at = 2  ->  one step is drift/lighting, two steps is a design change
#   defining_at = None -> never defining on its own (pose- and light-sensitive)
IDENTITY_ATTRIBUTES: list[dict] = [
    {
        "key": "hair_colour",
        "values": ["blonde", "light_brown", "dark_brown", "black", "red_auburn", "grey_white"],
        # Colour is not a straight ladder: auburn sits beside the browns, not
        # beside blonde. Adjacency is spelled out instead of implied by order.
        "adjacency": [
            ("blonde", "light_brown"),
            ("light_brown", "dark_brown"),
            ("dark_brown", "black"),
            ("light_brown", "red_auburn"),
            ("red_auburn", "dark_brown"),
            ("grey_white", "blonde"),
        ],
        "defining_at": 2,
        "hint": ("Colour FAMILY, not exact shade. Warm interior lamplight reads a "
                 "shade darker than a white-background turnaround."),
    },
    {
        "key": "hair_length",
        "values": ["cropped", "short", "chin", "shoulder", "mid_back", "longer"],
        "defining_at": 2,
        "hint": "Length as worn down, ignoring whether it is currently tied up.",
    },
    {
        "key": "hair_texture",
        "values": ["straight", "wavy", "curly", "tightly_curled"],
        "defining_at": 2,
        "hint": "Straight vs wavy is a styling difference; straight vs curly is not.",
    },
    {
        "key": "build",
        "values": ["child", "slim", "average", "heavy_set", "stocky"],
        "defining_at": 2,
        "hint": "Body type as drawn, not as flattered by the costume.",
    },
    {
        "key": "eyewear",
        "values": ["none", "thin_wire_round", "thin_wire_rectangular",
                   "heavy_dark_round", "heavy_dark_rectangular", "other"],
        "defining_at": 1,
        "hint": ("Glasses are a character design element, not a lighting effect. "
                 "Report 'none' only if you can see the face and there are none."),
    },
    {
        "key": "facial_hair",
        "values": ["clean_shaven", "stubble", "moustache", "full_beard"],
        "defining_at": 1,
        "hint": "Only fill this in for adult male characters; use clean_shaven otherwise.",
    },
    {
        "key": "apparent_age",
        "values": ["toddler", "child", "teenager", "adult", "older_adult"],
        # Defining at one step. These bands are wide and read reliably, and the
        # cast depends on them: with age tolerant, Mia's locked row and Jenny's
        # scored 0.75 against each other - an 8-year-old and a 15-year-old the
        # validator could not tell apart. Caught by
        # test_locked_cast_is_pairwise_distinguishable.
        "defining_at": 1,
        "hint": ("Band, not exact years: a 5-year-old is 'child', not "
                 "'toddler'; a 15-year-old is 'teenager', not 'adult'."),
    },
    {
        "key": "skin_tone",
        "values": ["pale", "light", "tan", "medium_brown", "deep_brown"],
        "defining_at": 2,
        "hint": "One step is lighting. Two steps is a different character.",
    },
    {
        "key": "hair_styling",
        "values": ["worn_loose", "ponytail", "bun_or_updo", "braid", "tied_back", "not_visible"],
        "defining_at": None,
        "hint": "Hair goes up and down between shots; this can never fail a character on its own.",
    },
    {
        "key": "face_shape",
        "values": ["round", "oval", "long_and_narrow", "square", "heart"],
        "defining_at": None,
        "hint": "Reads differently at different angles; never failing on its own.",
    },
]

_ATTR_BY_KEY = {a["key"]: a for a in IDENTITY_ATTRIBUTES}

# Verdict ladder. The gate elsewhere in this file passes at >= 0.6, so exactly
# one defining mismatch is enough to fail a character - which is the point.
IDENTITY_VERDICT_SCORES = {
    "same_character": 1.0,
    "minor_drift": 0.75,
    "significant_drift": 0.4,
    "different_person": 0.1,
    "not_visible": 0.0,
}


def _attr_distance(attr: dict, a: str, b: str) -> Optional[int]:
    """Ordinal distance between two observations of one attribute.

    Returns None when either value is outside the enum (the model wrote
    something we did not offer), which callers treat as "cannot compare".
    """
    if a == b:
        return 0
    vals = attr["values"]
    if a not in vals or b not in vals:
        return None
    if "adjacency" in attr:
        # Breadth-first over the declared adjacency graph.
        edges: dict[str, set[str]] = {v: set() for v in vals}
        for x, y in attr["adjacency"]:
            edges[x].add(y)
            edges[y].add(x)
        seen = {a}
        frontier = [a]
        dist = 0
        while frontier:
            dist += 1
            nxt = []
            for node in frontier:
                for peer in edges[node]:
                    if peer in seen:
                        continue
                    if peer == b:
                        return dist
                    seen.add(peer)
                    nxt.append(peer)
            frontier = nxt
        return len(vals)  # unreachable in the graph == maximally far apart
    return abs(vals.index(a) - vals.index(b))


def score_identity(
    frame_obs: dict[str, dict],
    ref_obs: dict[str, dict],
    expected: list[str],
) -> dict[str, dict]:
    """Diff the two observation tables and score each character, in Python.

    ``frame_obs`` and ``ref_obs`` are name -> {attribute: enum value}. The
    returned dict keeps the shape the rest of this module and the pipeline
    orchestrator already consume (score / notes / no_reference) and adds the
    evidence the score was derived from.
    """
    out: dict[str, dict] = {}
    for name in expected:
        fr = frame_obs.get(name)
        rf = ref_obs.get(name)
        if not fr or not fr.get("_visible", True):
            out[name] = {
                "score": 0.0,
                "notes": "not visible in this keyframe - identity not compared "
                         "(absence is scored by character_presence)",
                "no_reference": True,
                "verdict": "not_visible",
                "defining_mismatches": [],
                "soft_mismatches": [],
                "frame_attributes": fr or {},
                "reference_attributes": rf or {},
            }
            continue
        if not rf or all(v is None for v in rf.values()):
            out[name] = {
                "score": 0.0,
                "notes": "no locked identity sheet for this character - "
                         "identity NOT VERIFIED (this is a gap in the bible, "
                         "not a pass)",
                "no_reference": True,
                "verdict": "not_visible",
                "defining_mismatches": [],
                "soft_mismatches": [],
                "frame_attributes": fr,
                "reference_attributes": {},
            }
            continue

        defining: list[str] = []
        soft: list[str] = []
        detail: list[str] = []
        for attr in IDENTITY_ATTRIBUTES:
            k = attr["key"]
            a, b = fr.get(k), rf.get(k)
            if a is None or b is None or a == b:
                continue
            d = _attr_distance(attr, a, b)
            detail.append(f"{k}: turnaround {b} / frame {a}")
            threshold = attr["defining_at"]
            if threshold is not None and d is not None and d >= threshold:
                defining.append(k)
            else:
                soft.append(k)

        if defining:
            verdict = "different_person" if len(defining) >= 2 else "significant_drift"
        elif soft:
            verdict = "minor_drift"
        else:
            verdict = "same_character"

        if defining:
            notes = f"off-model on {', '.join(defining)} - " + "; ".join(
                d for d in detail if d.split(":")[0] in defining
            )
        elif soft:
            notes = "on-model; differs only on pose/lighting-sensitive attributes: " + "; ".join(detail)
        else:
            notes = "every compared attribute matches the turnaround"

        out[name] = {
            "score": IDENTITY_VERDICT_SCORES[verdict],
            "notes": notes[:400],
            "no_reference": False,
            "verdict": verdict,
            "defining_mismatches": defining,
            "soft_mismatches": soft,
            "frame_attributes": {a["key"]: fr.get(a["key"]) for a in IDENTITY_ATTRIBUTES},
            "reference_attributes": {a["key"]: rf.get(a["key"]) for a in IDENTITY_ATTRIBUTES},
        }
    return out


def _identity_attr_schema(with_hints: bool) -> dict:
    props = {}
    for attr in IDENTITY_ATTRIBUTES:
        entry: dict = {"type": "string", "enum": list(attr["values"])}
        if with_hints and attr.get("hint"):
            entry["description"] = attr["hint"]
        props[attr["key"]] = entry
    return props


def _identity_prompt_block(char_hints: dict[str, str]) -> str:
    lines = [
        "IDENTITY - how it is graded (read this before you fill anything in):",
        "",
        "  You do NOT score identity, and you are NOT shown the character",
        "  turnarounds. You record ONE table - what each character actually",
        "  looks like in the KEYFRAME UNDER TEST - and the validator compares",
        "  that table against the locked turnaround sheet itself. There is no",
        "  score for you to agree with and no reference for you to agree with.",
        "  Recording the wrong observation is the only way to get this wrong.",
        "",
        "  frame_observations: one entry per manifest character. Fill in every",
        "  attribute from THIS IMAGE, for the figure that is meant to be that",
        "  character. Write down what is drawn, not what the character is",
        "  supposed to look like. If a manifest character is not in the frame,",
        "  set visible=false; the attributes are then ignored.",
        "",
        "  Who is who in this frame:",
    ]
    for name, hint in char_hints.items():
        lines.append(f"    - {name}: {hint}")
    lines += [
        "",
        "  Fixed vocabularies. Pick the closest listed value:",
    ]
    for attr in IDENTITY_ATTRIBUTES:
        lines.append(f"    {attr['key']}: {' | '.join(attr['values'])}")
        if attr.get("hint"):
            lines.append(f"      {attr['hint']}")
    lines += [
        "",
        "  CLOTHING IS NOT AN IDENTITY ATTRIBUTE and is not in this table. It",
        "  is scored separately against the manifest, above.",
        "",
        "  These are generated images and characters DO drift off-model - that",
        "  is the entire reason this check exists. An earlier version of this",
        "  validator was shown the turnarounds and asked for a score; it",
        "  returned a perfect identity score on every character of every shot,",
        "  including a control where the wrong person's turnaround was supplied",
        "  as the reference. You are not being asked to agree with anything.",
        "  Describe the frame.",
    ]
    return "\n".join(lines)


# The locked reference rows. Each is a character's turnaround expressed in the
# vocabulary above - a bible artifact in exactly the sense CLAUDE.md means, and
# reviewed by a human like any other locked reference. Build a first draft with
#
#     python scripts/validate/shot_validator.py build-sheets \
#         --characters-dir <dir of turnarounds> --out <path>
#
# then READ IT AGAINST THE TURNAROUNDS and correct it before committing. The
# validator can only be as right as this file.
DEFAULT_IDENTITY_SHEET = Path(__file__).resolve().parent / "identity-sheets.json"


def _repo_relative(p: Path) -> str:
    """Path relative to the repo root when possible, so reports are portable."""
    try:
        return str(Path(p).resolve().relative_to(Path(__file__).resolve().parents[2]))
    except ValueError:
        return str(p)


def load_identity_sheets(path: Optional[Path] = None) -> dict[str, dict]:
    """Load the locked per-character attribute rows.

    Returns name -> {attribute: value}. Missing file or missing character is
    not an error here; it surfaces downstream as no_reference, i.e. "identity
    was not verified", which is not the same thing as a pass.
    """
    p = path or DEFAULT_IDENTITY_SHEET
    if not p.exists():
        return {}
    blob = json.loads(p.read_text())
    sheets = blob.get("characters", blob)
    out: dict[str, dict] = {}
    for name, row in sheets.items():
        if not isinstance(row, dict):
            continue
        out[name] = {a["key"]: row.get(a["key"]) for a in IDENTITY_ATTRIBUTES}
    return out


def validate_identity_sheet(sheets: dict[str, dict]) -> list[str]:
    """Return a list of problems with a sheet file (unknown enum values, gaps)."""
    problems: list[str] = []
    for name, row in sheets.items():
        for attr in IDENTITY_ATTRIBUTES:
            v = row.get(attr["key"])
            if v is None:
                problems.append(f"{name}.{attr['key']} is missing")
            elif v not in attr["values"]:
                problems.append(
                    f"{name}.{attr['key']}={v!r} is not one of {attr['values']}")
    return problems


# Shared JSON schema for the validation output. Designed to be acceptable by
# both Anthropic tool-input schemas and Google Gemini response_schemas, which
# means: no additionalProperties, no patternProperties, and use arrays-of-
# records instead of dynamic-keyed objects.
VALIDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "character_presence": {
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "expected": {"type": "array", "items": {"type": "string"}},
                "observed": {"type": "array", "items": {"type": "string"}},
                "missing": {"type": "array", "items": {"type": "string"}},
                "unexpected": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["score", "expected", "observed", "missing", "unexpected"],
        },
        "character_wardrobe": {
            "type": "array",
            "description": (
                "One entry per manifest character that has a wardrobe entry. "
                "Compare ONLY the character's clothing in the keyframe against "
                "the manifest's per-shot wardrobe description for that "
                "character. The turnaround's clothing is irrelevant here - "
                "characters wear different clothes in different scenes. If the "
                "manifest says 'black tuxedo' and the shot shows a tuxedo, "
                "that is a PASS. If the character is not visible in the "
                "keyframe, set no_reference=true and score=0.0."
            ),
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "score": {"type": "number"},
                    "expected": {"type": "string"},
                    "notes": {"type": "string", "maxLength": 240},
                    "no_reference": {"type": "boolean"},
                },
                "required": ["name", "score", "expected", "notes", "no_reference"],
            },
        },
        "location_match": {
            "type": "object",
            "description": (
                "Compare the set against the LOCATION PLATE. If no location "
                "plate image was supplied, set no_reference=true - there is "
                "nothing to compare against and a score would be invented."
            ),
            "properties": {
                "score": {"type": "number"},
                "notes": {"type": "string"},
                "no_reference": {"type": "boolean"},
            },
            "required": ["score", "notes", "no_reference"],
        },
        "continuity": {
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "notes": {"type": "string"},
                "no_prior_shot": {"type": "boolean"},
                "same_location_as_prior": {"type": "boolean"},
            },
            "required": ["score", "notes", "no_prior_shot", "same_location_as_prior"],
        },
        "artifacts": {
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "notes": {"type": "string"},
                "detected": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["score", "notes", "detected"],
        },
        "reasons": {
            "type": "array",
            "maxItems": 6,
            "items": {"type": "string", "maxLength": 240},
            "description": (
                "Anything wrong with this keyframe that the numeric rubric "
                "above does not already capture. The pass/fail gate is "
                "computed by the validator from the scores, not from this "
                "list, so there is nothing to be gained by leaving it empty."
            ),
        },
    },
    "required": [
        "character_presence", "character_wardrobe",
        "location_match", "continuity", "artifacts", "reasons",
    ],
}

VALIDATION_TOOL = {
    "name": "report_validation",
    "description": (
        "Report the validation of a single keyframe against the shot manifest "
        "and locked reference images. All scores are 0.0-1.0 where 1.0 is "
        "perfect adherence to the references."
    ),
    "input_schema": VALIDATION_SCHEMA,
}


def _obs_table(raw: Any) -> dict[str, dict]:
    """Coerce an observation array-of-records into a name-keyed dict."""
    out: dict[str, dict] = {}
    if not isinstance(raw, list):
        return out
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not name:
            continue
        row = {a["key"]: entry.get(a["key"]) for a in IDENTITY_ATTRIBUTES}
        row["_visible"] = bool(entry.get("visible", True))
        row["_where"] = entry.get("where_in_frame", "")
        out[name] = row
    return out


# Gate thresholds. These are the ONLY place pass/fail is decided.
GATE = {
    "character_presence": 0.7,
    "character_identity": 0.6,
    "character_wardrobe": 0.6,
    "location_match": 0.6,
    "continuity": 0.6,
    "artifacts": 0.7,
}


def _gate_keyframe(data: dict, expected: list[str]) -> tuple[bool, list[str]]:
    """Decide pass/fail for one keyframe from its scores. Never the model's call.

    The previous version took the model's own ``overall_pass`` boolean, which
    meant a grader that scored everything 1.00 also declared itself passing.
    """
    # The model's own free-text notes are kept separately: they are commentary,
    # not gate findings, and merging them made passing observations show up
    # under "Failure reasons".
    data["model_notes"] = list(data.get("reasons") or [])
    reasons: list[str] = []
    ok = True

    cp = data.get("character_presence") or {}
    if float(cp.get("score", 0.0)) < GATE["character_presence"]:
        ok = False
        miss = ", ".join(cp.get("missing") or []) or "none"
        extra = ", ".join(cp.get("unexpected") or []) or "none"
        reasons.append(f"character_presence {float(cp.get('score', 0.0)):.2f} "
                       f"(missing: {miss}; unexpected: {extra})")

    for name, info in (data.get("character_identity") or {}).items():
        if info.get("no_reference"):
            continue
        if float(info.get("score", 0.0)) < GATE["character_identity"]:
            ok = False
            reasons.append(
                f"{name} identity {float(info['score']):.2f} "
                f"({info.get('verdict', '?')}): {info.get('notes', '')}")

    for name, info in (data.get("character_wardrobe") or {}).items():
        if info.get("no_reference"):
            continue
        if float(info.get("score", 0.0)) < GATE["character_wardrobe"]:
            ok = False
            reasons.append(
                f"{name} wardrobe {float(info['score']):.2f} vs manifest "
                f"'{info.get('expected', '')}': {info.get('notes', '')}")

    lm = data.get("location_match") or {}
    if lm.get("no_reference"):
        reasons.append("location not verified: no location plate was supplied "
                       "for this shot (this is a gap in the bible, not a pass)")
    elif float(lm.get("score", 0.0)) < GATE["location_match"]:
        ok = False
        reasons.append(f"location_match {float(lm.get('score', 0.0)):.2f}: {lm.get('notes', '')}")

    cn = data.get("continuity") or {}
    if not cn.get("no_prior_shot") and float(cn.get("score", 0.0)) < GATE["continuity"]:
        ok = False
        reasons.append(f"continuity {float(cn.get('score', 0.0)):.2f}: {cn.get('notes', '')}")

    ar = data.get("artifacts") or {}
    if float(ar.get("score", 0.0)) < GATE["artifacts"]:
        ok = False
        det = ", ".join(ar.get("detected") or []) or "unspecified"
        reasons.append(f"artifacts {float(ar.get('score', 0.0)):.2f} ({det})")

    # Dedupe, keep order.
    seen: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.append(r)
    return ok, seen[:8]


def _postprocess_keyframe(data: dict, expected: list[str],
                          sheets: dict[str, dict],
                          frame_obs: Optional[dict[str, dict]] = None) -> dict:
    """Turn one raw model response into the validator's keyframe record.

    This is where identity stops being something the model asserts and starts
    being something the validator computes: the model's frame observations are
    diffed against the locked attribute sheet in Python.
    """
    frame_obs = frame_obs if frame_obs is not None else _obs_table(
        data.pop("frame_observations", None))
    data["character_identity"] = score_identity(frame_obs, sheets, expected)
    data["character_wardrobe"] = _normalize_wardrobe(data.get("character_wardrobe"))
    data["_frame_observations"] = frame_obs
    data["_identity_sheet_rows"] = {n: sheets.get(n) for n in expected}
    if "no_reference" not in (data.get("location_match") or {}):
        data.setdefault("location_match", {})["no_reference"] = False
    data["overall_pass"], data["reasons"] = _gate_keyframe(data, expected)
    return data


def _normalize_wardrobe(raw: Any) -> dict[str, dict]:
    """Coerce the model's character_wardrobe into a name-keyed dict."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        out: dict[str, dict] = {}
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not name:
                continue
            out[name] = {
                "score": entry.get("score", 0.0),
                "expected": entry.get("expected", ""),
                "notes": entry.get("notes", ""),
                "no_reference": bool(entry.get("no_reference", False)),
            }
        return out
    return {}


def _build_prompt(
    shot: dict,
    char_refs: dict[str, Path],
    missing_refs: list[str],
    has_location_ref: bool,
    has_prior: bool,
    prior_shot: Optional[dict] = None,
    wardrobe_refs: Optional[dict[str, tuple[Path, str, str]]] = None,
) -> str:
    expected = ", ".join(shot["characters"]) if shot["characters"] else "(no characters - prop/insert shot)"
    wardrobe_lines = "\n".join(
        f"  - {name}: {desc}" for name, desc in shot.get("wardrobe", {}).items()
    ) or "  (none specified)"
    props = "\n".join(f"  - {p}" for p in shot.get("key_props", [])) or "  (none)"

    parts = [
        "You are validating a single keyframe from a generated animated shot "
        "against locked reference images. You MUST call the report_validation "
        "tool with your findings; do not respond in plain text.",
        "",
        f"SHOT ID: {shot['shot_id']}",
        f"LOCATION: {shot.get('location', 'unknown')}",
        f"CAMERA: {shot.get('camera', '')}",
        "",
        "EXPECTED CHARACTERS (per manifest):",
        f"  {expected}",
        "",
        "EXPECTED WARDROBE (per manifest - this is the source of truth for "
        "what each character should be WEARING in this specific shot; the "
        "turnaround clothing is NOT the wardrobe spec):",
        wardrobe_lines,
        "",
        "EXPECTED KEY PROPS:",
        props,
        "",
    ]
    if prior_shot is not None:
        prior_loc = prior_shot.get("location", "unknown")
        prior_chars = ", ".join(prior_shot.get("characters", [])) or "(none)"
        prior_wardrobe_lines = "\n".join(
            f"  - {name}: {desc}"
            for name, desc in prior_shot.get("wardrobe", {}).items()
        ) or "  (none specified)"
        parts.extend([
            f"PRIOR SHOT: {prior_shot.get('shot_id', '?')}",
            f"PRIOR SHOT LOCATION: {prior_loc}",
            f"PRIOR SHOT CHARACTERS: {prior_chars}",
            "PRIOR SHOT WARDROBE:",
            prior_wardrobe_lines,
            "",
        ])
    parts.append("REFERENCE IMAGES PROVIDED, IN ORDER:")

    if wardrobe_refs:
        for name, (_p, desc, src_shot) in wardrobe_refs.items():
            parts.append(
                f"  - WARDROBE CONSISTENCY REFERENCE for {name} - canonical "
                f"look of '{desc}' as established in shot {src_shot}; the "
                f"outfit in the current keyframe should match this image."
            )
    if missing_refs:
        parts.append(
            f"  - NOTE: no locked identity sheet for: {', '.join(missing_refs)}. "
            f"Still describe them in frame_observations; the validator will "
            f"report their identity as unverified rather than as a pass."
        )
    if has_location_ref:
        parts.append("  - LOCATION PLATE (locked set reference for this shot's location)")
    if has_prior:
        parts.append("  - PREVIOUS SHOT KEYFRAME (for continuity comparison)")
    parts.append("  - KEYFRAME UNDER TEST (the image being validated)")
    parts.append("")
    parts.append(
        "RUBRIC - score each on 0.0 to 1.0:\n"
        "  character_presence: Are EXACTLY the manifest characters present? "
        "    - List who you see, who is missing, who is unexpected.\n"
        "    - 1.0 = exactly right set; deduct for missing/extra; 0.0 = none right.\n"
        "    - For background/OTS/silhouette characters, count them as present if visible at all.\n"
        "    - ANY visible human figure that is NOT in the manifest is "
        "      'unexpected' - including blurry, partial, edge-of-frame, or "
        "      out-of-focus background figures. Be strict: if a person is "
        "      visible at all and not in the expected list, list them in "
        "      'unexpected'.\n"
        "  identity: NOT SCORED HERE - see the IDENTITY block below. You fill "
        "    in frame_observations and reference_observations; the validator "
        "    computes the identity score from them.\n"
        "  character_wardrobe: SOURCE OF TRUTH for this score is the "
        "    EXPECTED WARDROBE block above, which comes from the per-shot "
        "    manifest. The turnaround's clothing is IRRELEVANT and must "
        "    NEVER drive this score.\n"
        "    - Score the GARMENTS ONLY. Ignore pose, action, prop "
        "      interaction, body language, gaze, etc. - those are not "
        "      wardrobe. Example: if the manifest reads 'casual home wear, "
        "      legs tucked under on couch', only judge whether the "
        "      clothing is casual home wear; do not penalize the wardrobe "
        "      score because the character's legs are not tucked under.\n"
        "    - For each visible character with an EXPECTED WARDROBE entry, "
        "      compare the character's clothing in the keyframe to that "
        "      manifest description. If the manifest says 'black tuxedo' "
        "      and the shot shows a tuxedo, that is a PASS (1.0) - even if "
        "      the turnaround shows casual clothes. If the manifest says "
        "      'elegant black formal dress' and the shot shows a formal "
        "      black dress, that is a PASS.\n"
        "    - Set 'expected' to the manifest text you used.\n"
        "    - Score 1.0 = clothing matches the manifest description; 0.5 "
        "      = partial match (right category, wrong color/detail); 0.0 = "
        "      clearly the wrong type of garment.\n"
        "    - WARDROBE CONSISTENCY: if a WARDROBE CONSISTENCY REFERENCE "
        "      image is provided for this character, the outfit in the "
        "      keyframe should look like the SAME specific garment as in "
        "      that reference (same tuxedo, same dress, same pajamas). Only "
        "      mark inconsistency in 'notes' / lower the score if the same "
        "      character with the same manifest outfit looks visibly "
        "      different (different cut, color, accessories) between shots.\n"
        "    - If the character is not visible in the keyframe, set "
        "      no_reference=true, score=0.0.\n"
        "  location_match: Does the set match the location plate? "
        "    - If NO LOCATION PLATE image is listed in the reference images "
        "      above, set no_reference=true and score 0.0. Do not score a "
        "      comparison you were given nothing to compare against.\n"
        "    - Compare furniture, layout, color palette, windows, lighting style.\n"
        "    - For each distinctive landmark in the plate (e.g. a TV, a "
        "      specific couch, a window with a storm visible, an armchair, "
        "      a particular lamp), check whether the keyframe shows the "
        "      same landmarks in roughly the same positions.\n"
        "    - 1.0 = clearly the same room with most distinctive landmarks "
        "      visible and consistent; 0.5 = recognizably the same TYPE of "
        "      room (e.g. another living room) but key landmarks are "
        "      missing or rearranged - a hallway, foyer, dining room, or "
        "      bedroom is NOT a 1.0 even if the wall color matches; 0.0 = "
        "      a clearly different place.\n"
        "    - If the keyframe shows a different room entirely (e.g. a "
        "      hallway with no couch / no TV / no window when the plate "
        "      shows the living room), score 0.3-0.5 at most and "
        "      explicitly note which landmarks are missing.\n"
        "  continuity: Only meaningful when this shot is in the SAME LOCATION "
        "    as the prior shot. If you can see from the PRIOR SHOT context "
        "    above that the location differs from this shot's location, OR "
        "    if there is no prior shot, set no_prior_shot=true and score 1.0 "
        "    (this is a normal cut, not a continuity error). Same-location "
        "    rule: set same_location_as_prior=true and score ONLY genuinely "
        "    persistent elements - set/room dressing, time of day (day vs "
        "    night, storm vs calm), and the wardrobe of characters that "
        "    appear in BOTH this shot and the prior one. DO NOT penalize: "
        "    different characters appearing (a cut to another beat is fine), "
        "    wardrobe differing for characters that were not in the prior "
        "    shot, normal camera angle / framing changes, or different TV "
        "    content. DO penalize: a real room-layout change, missing "
        "    furniture/windows, or a day-to-night jump within the same "
        "    location.\n"
        "  artifacts: Visible generation artifacts and physics violations. "
        "    Examples to actively look for:\n"
        "    - extra limbs, melting/morphing, garbled hands, anatomy breaks, "
        "      duplicated features, text-in-frame, watermarks;\n"
        "    - environment effects that do not make physical sense, "
        "      especially LIGHTNING BOLTS SHOWN INSIDE A ROOM (lightning "
        "      should only be visible through a window from outdoors). If "
        "      you see a lightning bolt overlapping interior walls, "
        "      furniture, or lamps rather than the sky outside a window, "
        "      flag it explicitly in 'detected' and lower the score.\n"
        "    - unexpected background human figures that are not in the "
        "      manifest character list - this overlaps with presence, but "
        "      list it here too as 'unexpected background character' so it "
        "      cannot be missed.\n"
        "    - 1.0 = none visible; 0.7-0.9 = minor anomalies; 0.4-0.6 = a "
        "      clear artifact like indoor lightning or a phantom person; "
        "      0.0 = severely broken.\n"
    )
    parts.append("")
    parts.append(
        "THE PASS/FAIL GATE IS NOT YOURS TO SET. The validator computes it "
        "from your scores and observations:\n"
        "  - character_presence.score >= 0.7\n"
        "  - every visible character's computed identity score >= 0.6\n"
        "  - every visible character_wardrobe score >= 0.6\n"
        "  - location_match.score >= 0.6 (skipped if no_reference=true)\n"
        "  - continuity.score >= 0.6 (skipped if no_prior_shot=true)\n"
        "  - artifacts.score >= 0.7\n"
        "You cannot pass or fail this shot by asserting anything. Report what "
        "you see; the arithmetic happens elsewhere.\n"
        "\n"
        "Be HONEST. This is a real production validator; a false pass is worse "
        "than a false fail - a false pass puts off-model art in the finished "
        "film. Do NOT flag scene-appropriate clothing (different from the "
        "turnaround but matching the manifest) as a problem; per-shot wardrobe "
        "is the manifest's job, not the turnaround's.\n"
        "\n"
        "OUTPUT LENGTH RULES (critical, to avoid truncation):\n"
        "  - Every 'notes' field must be a SINGLE sentence, max 200 characters.\n"
        "  - The 'reasons' array must have at most 5 items, each a short sentence.\n"
        "  - 'observed', 'missing', 'unexpected', and 'detected' lists must "
        "contain at most 6 short items (a name or 2-3 word tag), never full "
        "paragraphs.\n"
        "  - Do not repeat the same reason verbatim."
    )
    parts.append("")
    parts.append(
        "IDENTITY is not part of this call at all. It is graded separately, "
        "from a description of the frame taken with no reference images "
        "present, diffed in code against the locked turnaround sheet. Do not "
        "comment on whether characters look like themselves.")
    return "\n".join(parts)


def _build_labeled_images(
    char_refs: dict[str, Path],
    location_ref: Optional[Path],
    prior_keyframe: Optional[Path],
    keyframe: Path,
    wardrobe_refs: Optional[dict[str, tuple[Path, str, str]]] = None,
) -> list[tuple[str, Path]]:
    """Ordered list of (caption, image_path) used by both backends.

    wardrobe_refs maps character name -> (canonical keyframe path,
    manifest wardrobe text, source shot id) for cross-shot wardrobe
    consistency checking. Only populated when an earlier shot in the
    scene established a canonical look for that character + outfit.
    """
    out: list[tuple[str, Path]] = []
    # Character turnarounds are DELIBERATELY NOT SENT. Attaching them measurably
    # contaminates the frame observation: with Gabe's turnaround in context the
    # model reported him wearing his turnaround's glasses and stubble in a clip
    # where he plainly has neither. Identity is graded against the locked
    # attribute sheet instead - see load_identity_sheets().
    if wardrobe_refs:
        for name, (path, desc, src_shot) in wardrobe_refs.items():
            out.append((
                f"WARDROBE CONSISTENCY REFERENCE - {name}'s outfit '{desc}' "
                f"as already established in shot {src_shot}. {name} appears "
                f"in the current shot with the same manifest wardrobe text, "
                f"so the outfit should look like the SAME garment as in this "
                f"reference image (same tuxedo, same dress, same pajamas - "
                f"not a different one).",
                path,
            ))
    if location_ref:
        out.append(("REFERENCE - location plate:", location_ref))
    if prior_keyframe:
        out.append(("REFERENCE - previous shot keyframe (for continuity):", prior_keyframe))
    out.append(("KEYFRAME UNDER TEST:", keyframe))
    return out


class _GeminiHardFailure(Exception):
    """Non-retryable structured-output failure (e.g. runaway generation)."""


def _call_with_retry(fn, *, max_attempts: int = 6, label: str = "call"):
    """Generic backoff wrapper around a callable that may raise rate-limit errors."""
    delay = 8.0
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except _GeminiHardFailure:
            raise
        except Exception as e:
            msg = str(e).lower()
            retryable = (
                "rate" in msg or "429" in msg or "overloaded" in msg or
                "503" in msg or "502" in msg or "504" in msg or
                "resource_exhausted" in msg or "deadline" in msg or
                "connection" in msg or "unavailable" in msg
            )
            if not retryable or attempt == max_attempts:
                raise
            sleep_for = delay + random.uniform(0, 2.0)
            print(f"  [retry] {label} attempt {attempt} hit retryable error "
                  f"({type(e).__name__}); sleeping {sleep_for:.1f}s", flush=True)
            time.sleep(sleep_for)
            delay = min(delay * 2.0, 90.0)
    raise RuntimeError("retry loop exited without result")


# --- Claude backend ---------------------------------------------------------

def _validate_keyframe_claude(
    client,
    model: str,
    keyframe: Path,
    shot: dict,
    char_refs: dict[str, Path],
    missing_refs: list[str],
    location_ref: Optional[Path],
    prior_keyframe: Optional[Path],
    prior_shot: Optional[dict] = None,
    wardrobe_refs: Optional[dict[str, tuple[Path, str, str]]] = None,
    sheets: Optional[dict[str, dict]] = None,
    frame_obs: Optional[dict[str, dict]] = None,
) -> tuple[dict, dict]:
    sheets = sheets or {}
    content: list[dict] = []
    for caption, path in _build_labeled_images(
        char_refs, location_ref, prior_keyframe, keyframe, wardrobe_refs=wardrobe_refs,
    ):
        content.append({"type": "text", "text": caption})
        content.append(_encode_image(path))

    prompt = _build_prompt(
        shot,
        char_refs=char_refs,
        missing_refs=missing_refs,
        has_location_ref=location_ref is not None,
        has_prior=prior_keyframe is not None,
        prior_shot=prior_shot,
        wardrobe_refs=wardrobe_refs,
    )
    content.append({"type": "text", "text": prompt})

    def _do_call():
        return client.messages.create(
            model=model,
            max_tokens=8192,
            tools=[VALIDATION_TOOL],
            tool_choice={"type": "tool", "name": "report_validation"},
            messages=[{"role": "user", "content": content}],
        )
    response = _call_with_retry(_do_call, label=f"claude:{shot['shot_id']}")

    tool_input = None
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "report_validation":
            tool_input = block.input
            break
    if tool_input is None:
        text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise RuntimeError(f"Claude did not emit tool call; text was: {text!r}")
        tool_input = json.loads(m.group())

    tool_input = _postprocess_keyframe(tool_input, shot.get("characters") or [], sheets, frame_obs)
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return tool_input, usage


# --- Gemini backend ---------------------------------------------------------

def _try_repair_json(text: str) -> Optional[dict]:
    """Best-effort recovery of a partial JSON object from a truncated stream.

    Strategy:
      1) Trim to the last balanced top-level close brace and try json.loads.
      2) If still broken, walk back close-brace by close-brace, repeatedly
         appending the missing closes ("}") until the structure parses.
      3) Pad missing required top-level keys with safe defaults.
    """
    start = text.find("{")
    if start < 0:
        return None
    s = text[start:]

    # Find the last balanced top-level close brace.
    depth = 0
    in_string = False
    escape = False
    last_balanced = -1
    for i, ch in enumerate(s):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                last_balanced = i

    candidates: list[str] = []
    if last_balanced > 0:
        candidates.append(s[: last_balanced + 1])
    # Also try aggressive recovery: walk back from the end, closing nesting.
    # We find the last comma at depth 1 (i.e., between top-level fields) and
    # cut there, then close the outer brace.
    depth = 0
    in_string = False
    escape = False
    last_top_comma = -1
    for i, ch in enumerate(s):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == "," and depth == 1:
            last_top_comma = i
    if last_top_comma > 0:
        candidates.append(s[:last_top_comma] + "}")

    parsed: Optional[dict] = None
    for cand in candidates:
        try:
            parsed = json.loads(cand)
            break
        except json.JSONDecodeError:
            continue
    if parsed is None:
        return None

    # Fill in any missing required top-level keys with safe defaults so the
    # downstream aggregator can still process this keyframe.
    defaults: dict = {
        "character_presence": {
            "score": 0.0, "expected": [], "observed": [],
            "missing": [], "unexpected": [],
        },
        "frame_observations": [],
        "reference_observations": [],
        "character_wardrobe": [],
        "location_match": {"score": 0.0, "notes": "(missing from truncated output)",
                            "no_reference": False},
        "continuity": {"score": 0.0, "notes": "(missing from truncated output)",
                        "no_prior_shot": False, "same_location_as_prior": False},
        "artifacts": {"score": 0.0, "notes": "(missing from truncated output)", "detected": []},
        "reasons": ["Model output was truncated; structured fields are incomplete."],
    }
    for k, v in defaults.items():
        parsed.setdefault(k, v)
    return parsed


def _strip_gemini_unsupported(schema: Any) -> Any:
    """Remove JSON-schema keys that the Gemini structured-output schema rejects."""
    if isinstance(schema, dict):
        cleaned = {}
        for k, v in schema.items():
            if k in {"additionalProperties", "$schema", "$id"}:
                continue
            cleaned[k] = _strip_gemini_unsupported(v)
        return cleaned
    if isinstance(schema, list):
        return [_strip_gemini_unsupported(v) for v in schema]
    return schema


def _validate_keyframe_gemini(
    client,
    model: str,
    keyframe: Path,
    shot: dict,
    char_refs: dict[str, Path],
    missing_refs: list[str],
    location_ref: Optional[Path],
    prior_keyframe: Optional[Path],
    prior_shot: Optional[dict] = None,
    wardrobe_refs: Optional[dict[str, tuple[Path, str, str]]] = None,
    sheets: Optional[dict[str, dict]] = None,
    frame_obs: Optional[dict[str, dict]] = None,
) -> tuple[dict, dict]:
    sheets = sheets or {}
    from google.genai import types

    parts: list = []
    for caption, path in _build_labeled_images(
        char_refs, location_ref, prior_keyframe, keyframe, wardrobe_refs=wardrobe_refs,
    ):
        parts.append(caption)
        # Re-use the resized/encoded image bytes from the shared helper.
        block = _encode_image(path)
        img_bytes = base64.b64decode(block["source"]["data"])
        parts.append(types.Part.from_bytes(data=img_bytes, mime_type=block["source"]["media_type"]))

    prompt = _build_prompt(
        shot,
        char_refs=char_refs,
        missing_refs=missing_refs,
        has_location_ref=location_ref is not None,
        has_prior=prior_keyframe is not None,
        prior_shot=prior_shot,
        wardrobe_refs=wardrobe_refs,
    )
    parts.append(prompt)

    schema = _strip_gemini_unsupported(VALIDATION_SCHEMA)
    config_kwargs = dict(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.0,
        max_output_tokens=32768,
    )
    # Thinking: the observation tables are a recall task, not a reasoning one,
    # and letting a 3.x model think freely cost up to 38k thought tokens on a
    # single keyframe without improving the answer. Cap it low; on 2.5 models,
    # which have no thinking_level, disable it outright.
    try:
        if model.startswith("gemini-3"):
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="low")
        else:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    except (AttributeError, TypeError):
        pass
    config = types.GenerateContentConfig(**config_kwargs)

    def _do_call():
        resp = client.models.generate_content(
            model=model,
            contents=parts,
            config=config,
        )
        # Surface truncation as a retryable error so _call_with_retry kicks in.
        finish = None
        try:
            finish = str(resp.candidates[0].finish_reason)
        except (AttributeError, IndexError):
            pass
        text = resp.text or ""
        truncated = bool(finish and "MAX_TOKENS" in finish.upper())
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = _try_repair_json(text)
        if data is None:
            # Unrecoverable: surface a clear message, NOT a retryable one
            # (retrying won't unbreak a runaway-generation pattern).
            preview = text[:400].replace("\n", " ")
            raise _GeminiHardFailure(
                f"Gemini failed to produce parseable JSON "
                f"(finish_reason={finish}, truncated={truncated}, "
                f"len={len(text)}). First 400 chars: {preview!r}"
            )
        if truncated:
            print(f"  [warn] Gemini hit MAX_TOKENS but JSON was repaired "
                  f"({len(text)} chars output).", flush=True)
        return resp, data
    pair = _call_with_retry(_do_call, label=f"gemini:{shot['shot_id']}")
    response, data = pair

    data = _postprocess_keyframe(data, shot.get("characters") or [], sheets, frame_obs)
    usage_meta = getattr(response, "usage_metadata", None)
    usage = {
        "input_tokens": getattr(usage_meta, "prompt_token_count", 0) or 0,
        # Thinking tokens are billed as output; count them or the cost estimate
        # understates by whatever the model spent reasoning.
        "output_tokens": (getattr(usage_meta, "candidates_token_count", 0) or 0)
                         + (getattr(usage_meta, "thoughts_token_count", 0) or 0),
    }
    return data, usage



# The identity observation is a SEPARATE call whose only image is the keyframe.
# It is kept separate because every reference image we have tried to put in
# front of the grader has anchored the answer: with Gabe's turnaround in
# context the model reported his glasses and stubble in a clip where he has
# neither, and with a prior shot's keyframe in context as a wardrobe reference
# it read Leo as blonde in a panel where he is brown-haired. The observation
# call sees the frame and nothing else, so there is nothing to agree with.
FRAME_OBSERVATION_SCHEMA = {
    "type": "object",
    "properties": {
        "frame_observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": dict(
                    {
                        "name": {"type": "string"},
                        "visible": {"type": "boolean"},
                        "where_in_frame": {"type": "string", "maxLength": 120},
                    },
                    **_identity_attr_schema(with_hints=True),
                ),
                "required": ["name", "visible", "where_in_frame"]
                + [a["key"] for a in IDENTITY_ATTRIBUTES],
            },
        },
    },
    "required": ["frame_observations"],
}


def _observe_frame_gemini(client, model: str, keyframe: Path, shot: dict) -> tuple[dict, dict]:
    from google.genai import types

    block = _encode_image(keyframe)
    img = types.Part.from_bytes(
        data=base64.b64decode(block["source"]["data"]),
        mime_type=block["source"]["media_type"])
    hints = {}
    for name in shot.get("characters") or []:
        wd = (shot.get("wardrobe") or {}).get(name)
        hints[name] = wd if wd else "(no manifest description; use position and context)"
    parts = ["KEYFRAME UNDER TEST:", img, _identity_prompt_block(hints)]

    config_kwargs = dict(
        response_mime_type="application/json",
        response_schema=_strip_gemini_unsupported(FRAME_OBSERVATION_SCHEMA),
        temperature=0.0,
        max_output_tokens=16384,
    )
    try:
        if model.startswith("gemini-3"):
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="low")
        else:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    except (AttributeError, TypeError):
        pass

    def _do_call():
        resp = client.models.generate_content(
            model=model, contents=parts,
            config=types.GenerateContentConfig(**config_kwargs))
        text = resp.text or ""
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = _try_repair_json(text) or {}
        return resp, data
    resp, data = _call_with_retry(_do_call, label=f"observe:{shot.get('shot_id')}")
    um = getattr(resp, "usage_metadata", None)
    usage = {
        "input_tokens": getattr(um, "prompt_token_count", 0) or 0,
        "output_tokens": ((getattr(um, "candidates_token_count", 0) or 0)
                          + (getattr(um, "thoughts_token_count", 0) or 0)),
    }
    return _obs_table(data.get("frame_observations")), usage


def _observe_frame_claude(client, model: str, keyframe: Path, shot: dict) -> tuple[dict, dict]:
    hints = {}
    for name in shot.get("characters") or []:
        wd = (shot.get("wardrobe") or {}).get(name)
        hints[name] = wd if wd else "(no manifest description; use position and context)"
    tool = {
        "name": "report_frame_observations",
        "description": "Record what each character actually looks like in this keyframe.",
        "input_schema": FRAME_OBSERVATION_SCHEMA,
    }
    content = [
        {"type": "text", "text": "KEYFRAME UNDER TEST:"},
        _encode_image(keyframe),
        {"type": "text", "text": _identity_prompt_block(hints)},
    ]

    def _do_call():
        return client.messages.create(
            model=model, max_tokens=4096, tools=[tool],
            tool_choice={"type": "tool", "name": "report_frame_observations"},
            messages=[{"role": "user", "content": content}])
    resp = _call_with_retry(_do_call, label=f"observe:{shot.get('shot_id')}")
    payload = {}
    for b in resp.content:
        if getattr(b, "type", None) == "tool_use":
            payload = b.input
            break
    return _obs_table(payload.get("frame_observations")), {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }


def observe_frame(backend: str, client, model: str, keyframe: Path, shot: dict):
    if backend == "claude":
        return _observe_frame_claude(client, model, keyframe, shot)
    if backend == "gemini":
        return _observe_frame_gemini(client, model, keyframe, shot)
    raise ValueError(f"Unknown backend: {backend}")


def _validate_keyframe(
    backend: str,
    client,
    model: str,
    **kwargs,
) -> tuple[dict, dict]:
    if backend == "claude":
        return _validate_keyframe_claude(client, model, **kwargs)
    if backend == "gemini":
        return _validate_keyframe_gemini(client, model, **kwargs)
    raise ValueError(f"Unknown backend: {backend}")


def _wardrobe_key(text: str) -> str:
    """Normalize a manifest wardrobe text so 'black tuxedo' and 'black "
    tuxedo (slightly rumpled)' map to the same key.

    Strategy: lowercase, strip parenthetical asides, collapse whitespace, drop
    trailing punctuation. Keeps the core garment phrase so that small
    parenthetical action notes (e.g. "(slightly rumpled)", "(background, "
    on phone)") do not cause the same outfit to be treated as a new one.
    """
    if not text:
        return ""
    t = re.sub(r"\([^)]*\)", " ", text)  # drop parenthetical notes
    t = re.sub(r"\s+", " ", t).strip().lower().rstrip(".,;")
    return t


# ---------------------------------------------------------------------------
# Shot-level aggregation
# ---------------------------------------------------------------------------

@dataclass
class ShotValidationResult:
    shot_id: str
    keyframes: list[dict] = field(default_factory=list)  # per-keyframe outputs
    overall_pass: bool = False
    aggregate_scores: dict = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    usage: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})
    media_paths: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "shot_id": self.shot_id,
            "overall_pass": self.overall_pass,
            "aggregate_scores": self.aggregate_scores,
            "reasons": self.reasons,
            "keyframes": self.keyframes,
            "usage": self.usage,
            "media_paths": self.media_paths,
        }


def _aggregate(per_keyframe: list[dict]) -> tuple[dict, bool, list[str]]:
    """Aggregate the rubric across keyframes.

    Every headline score is the WORST keyframe, not the mean. A shot in which
    a character is off-model for one of three keyframes is an off-model shot;
    averaging 0.10 with two 1.00s produced 0.70 and cleared the 0.60 gate,
    which is how a real per-keyframe failure used to vanish. Means are still
    reported alongside, under ``*_mean``, because the spread is informative -
    but the gate reads the minimum.
    """
    def avg(key_path: list[str]) -> float:
        vals = []
        for kf in per_keyframe:
            cur: Any = kf
            for k in key_path:
                cur = cur.get(k) if isinstance(cur, dict) else None
                if cur is None:
                    break
            if isinstance(cur, (int, float)):
                vals.append(float(cur))
        return sum(vals) / len(vals) if vals else 0.0

    def worst(key_path: list[str]) -> float:
        vals = []
        for kf in per_keyframe:
            cur: Any = kf
            for k in key_path:
                cur = cur.get(k) if isinstance(cur, dict) else None
                if cur is None:
                    break
            if isinstance(cur, (int, float)):
                vals.append(float(cur))
        return min(vals) if vals else 0.0

    aggregate = {
        "character_presence": round(worst(["character_presence", "score"]), 3),
        "location_match": round(worst(["location_match", "score"]), 3),
        "continuity": round(worst(["continuity", "score"]), 3),
        "artifacts": round(worst(["artifacts", "score"]), 3),
        "character_presence_mean": round(avg(["character_presence", "score"]), 3),
        "location_match_mean": round(avg(["location_match", "score"]), 3),
        "continuity_mean": round(avg(["continuity", "score"]), 3),
        "artifacts_mean": round(avg(["artifacts", "score"]), 3),
        "location_no_reference": all(
            (kf.get("location_match") or {}).get("no_reference") for kf in per_keyframe
        ) if per_keyframe else True,
    }

    # Per-character identity: average across keyframes that scored that character.
    id_acc: dict[str, list[float]] = {}
    id_no_ref: set[str] = set()
    for kf in per_keyframe:
        for ch, info in (kf.get("character_identity") or {}).items():
            if info.get("no_reference"):
                id_no_ref.add(ch)
                continue
            sc = info.get("score")
            if isinstance(sc, (int, float)):
                id_acc.setdefault(ch, []).append(float(sc))
    aggregate["character_identity"] = {ch: round(min(vs), 3) for ch, vs in id_acc.items()}
    aggregate["character_identity_mean"] = {
        ch: round(sum(vs) / len(vs), 3) for ch, vs in id_acc.items()
    }
    aggregate["character_identity_no_reference"] = sorted(id_no_ref)
    # The evidence behind the worst keyframe's verdict, so a report can quote it.
    worst_ev: dict[str, dict] = {}
    for kf in per_keyframe:
        for ch, info in (kf.get("character_identity") or {}).items():
            if info.get("no_reference"):
                continue
            sc = float(info.get("score", 0.0))
            if ch not in worst_ev or sc < worst_ev[ch]["score"]:
                worst_ev[ch] = {
                    "score": sc,
                    "verdict": info.get("verdict"),
                    "defining_mismatches": info.get("defining_mismatches", []),
                    "soft_mismatches": info.get("soft_mismatches", []),
                    "frame_attributes": info.get("frame_attributes", {}),
                    "reference_attributes": info.get("reference_attributes", {}),
                    "notes": info.get("notes", ""),
                }
    aggregate["character_identity_evidence"] = worst_ev

    # Per-character wardrobe: same pattern as identity.
    wd_acc: dict[str, list[float]] = {}
    wd_no_ref: set[str] = set()
    wd_expected: dict[str, str] = {}
    for kf in per_keyframe:
        for ch, info in (kf.get("character_wardrobe") or {}).items():
            if info.get("no_reference"):
                wd_no_ref.add(ch)
                continue
            sc = info.get("score")
            if isinstance(sc, (int, float)):
                wd_acc.setdefault(ch, []).append(float(sc))
            exp = info.get("expected")
            if exp and ch not in wd_expected:
                wd_expected[ch] = exp
    aggregate["character_wardrobe"] = {ch: round(min(vs), 3) for ch, vs in wd_acc.items()}
    aggregate["character_wardrobe_mean"] = {
        ch: round(sum(vs) / len(vs), 3) for ch, vs in wd_acc.items()
    }
    aggregate["character_wardrobe_no_reference"] = sorted(wd_no_ref)
    aggregate["character_wardrobe_expected"] = wd_expected

    # Pass = every keyframe passed.
    overall_pass = all(kf.get("overall_pass") for kf in per_keyframe) if per_keyframe else False

    # Reasons: dedupe across keyframes.
    seen: list[str] = []
    for kf in per_keyframe:
        for r in kf.get("reasons", []) or []:
            if r not in seen:
                seen.append(r)
    return aggregate, overall_pass, seen


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def _default_model_for_backend(backend: str) -> str:
    return DEFAULT_CLAUDE_MODEL if backend == "claude" else DEFAULT_GEMINI_MODEL


def _make_client(backend: str):
    if backend == "claude":
        return _get_anthropic_client()
    if backend == "gemini":
        return _get_gemini_client()
    raise ValueError(f"Unknown backend: {backend}")


_VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def validate_panel(
    shot: dict,
    panel_path: Path,
    characters_dir: Path,
    locations_dir: Path,
    keyframes_dir: Path,
    *,
    backend: str = DEFAULT_BACKEND,
    model: Optional[str] = None,
    client=None,
    identity_sheet: Optional[Path] = None,
    sheets: Optional[dict[str, dict]] = None,
) -> ShotValidationResult:
    """Validate a STILL PANEL image (storyboard panel) against the bible.

    This is the still-image entry point used by the orchestrator's panel gate.
    Identical rubric to ``validate_shot``, but the panel is treated as a
    single keyframe (no ffmpeg extraction). Continuity is reported as n/a
    because a still panel has no prior keyframe of itself.
    """
    p = Path(panel_path)
    if p.suffix.lower() not in _IMAGE_SUFFIXES:
        raise ValueError(
            f"validate_panel expects a still image (PNG/JPG/WEBP/GIF); "
            f"got {p.suffix!r}. For video, use validate_shot."
        )
    return validate_shot(
        shot=shot,
        media_path=p,
        characters_dir=characters_dir,
        locations_dir=locations_dir,
        keyframes_dir=keyframes_dir,
        prior_keyframe=None,
        prior_shot=None,
        wardrobe_refs=None,
        backend=backend,
        model=model,
        client=client,
        identity_sheet=identity_sheet,
        sheets=sheets,
    )


def validate_shot(
    shot: dict,
    media_path: Path,
    characters_dir: Path,
    locations_dir: Path,
    keyframes_dir: Path,
    prior_keyframe: Optional[Path] = None,
    prior_shot: Optional[dict] = None,
    wardrobe_refs: Optional[dict[str, tuple[Path, str, str]]] = None,
    backend: str = DEFAULT_BACKEND,
    model: Optional[str] = None,
    client=None,
    identity_sheet: Optional[Path] = None,
    sheets: Optional[dict[str, dict]] = None,
) -> ShotValidationResult:
    """Validate a single shot. media_path may be a video or a still image.

    Still images (PNG/JPG/WEBP/GIF) are validated as a single keyframe;
    videos have first/middle/last keyframes extracted via ffmpeg. The
    rubric and pass/fail gate are identical.
    """
    if model is None:
        model = _default_model_for_backend(backend)
    if client is None:
        client = _make_client(backend)

    if media_path.suffix.lower() in _VIDEO_SUFFIXES:
        keyframes = extract_keyframes(media_path, keyframes_dir)
    elif media_path.suffix.lower() in _IMAGE_SUFFIXES:
        keyframes = [media_path]
    else:
        # Unknown extension — best-effort treat as image; ffmpeg would have
        # failed anyway on a non-decodable file.
        keyframes = [media_path]

    char_refs, missing = resolve_character_refs(shot["characters"], characters_dir)
    location_ref = resolve_location_ref(shot, locations_dir)

    if sheets is None:
        sheets = load_identity_sheets(identity_sheet)
    problems = validate_identity_sheet(sheets)
    if problems:
        raise ValueError(
            "Identity sheet is malformed, refusing to validate against it:\n  "
            + "\n  ".join(problems))
    # A character with no sheet row cannot have their identity verified. Say so
    # rather than letting them quietly not appear in the identity scores.
    unsheeted = [c for c in shot["characters"] if c not in sheets]

    per_keyframe: list[dict] = []
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    for kf in keyframes:
        # Identity observation first, in its own call, with the keyframe as the
        # only image in context.
        frame_obs, obs_usage = observe_frame(backend, client, model, kf, shot)
        total_usage["input_tokens"] += obs_usage["input_tokens"]
        total_usage["output_tokens"] += obs_usage["output_tokens"]
        out, usage = _validate_keyframe(
            backend=backend,
            client=client,
            model=model,
            keyframe=kf,
            shot=shot,
            char_refs=char_refs,
            missing_refs=missing,
            location_ref=location_ref,
            prior_keyframe=prior_keyframe,
            prior_shot=prior_shot,
            wardrobe_refs=wardrobe_refs,
            sheets=sheets,
            frame_obs=frame_obs,
        )
        out["_keyframe_path"] = str(kf)
        per_keyframe.append(out)
        total_usage["input_tokens"] += usage["input_tokens"]
        total_usage["output_tokens"] += usage["output_tokens"]

    aggregate, overall_pass, reasons = _aggregate(per_keyframe)

    return ShotValidationResult(
        shot_id=shot["shot_id"],
        keyframes=per_keyframe,
        overall_pass=overall_pass,
        aggregate_scores=aggregate,
        reasons=reasons,
        usage=total_usage,
        media_paths={
            "media": str(media_path),
            "character_refs": {k: str(v) for k, v in char_refs.items()},
            "missing_refs": missing,
            "identity_sheet": _repo_relative(identity_sheet or DEFAULT_IDENTITY_SHEET),
            "characters_without_identity_sheet": unsheeted,
            "location_ref": str(location_ref) if location_ref else None,
            "prior_keyframe": str(prior_keyframe) if prior_keyframe else None,
            "prior_shot_id": prior_shot["shot_id"] if prior_shot else None,
            "wardrobe_refs": {
                name: {"path": str(p), "expected": desc, "source_shot": src}
                for name, (p, desc, src) in (wardrobe_refs or {}).items()
            },
            "keyframes": [str(p) for p in keyframes],
        },
    )


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    price = PRICING.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens / 1_000_000.0) * price["input"] + \
           (output_tokens / 1_000_000.0) * price["output"]


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

_NAME_PATTERN = re.compile(r"^([A-Z][a-z]+)(?:'s|\s+is)\b")
_MISSING_NAME = re.compile(r"\b([A-Z][a-z]+)\s+(?:is\s+)?missing\b")
_NAMED_MISSING_LIST = re.compile(r"missing\s+(?:character[s]?)?[: ]*([A-Z][a-zA-Z, ]+?)(?:\.|$| from| due)")


def _short_flag(reasons: list[str]) -> list[str]:
    """Best-effort condensation of failure reasons into 1-line tags."""
    tags: list[str] = []
    seen: set[str] = set()
    missing_names: set[str] = set()
    for r in reasons:
        for m in _MISSING_NAME.finditer(r):
            missing_names.add(m.group(1))
        ml = _NAMED_MISSING_LIST.search(r)
        if ml:
            for n in re.split(r",|\band\b", ml.group(1)):
                n = n.strip().rstrip(".")
                if n and n[:1].isupper():
                    missing_names.add(n)

    if missing_names:
        tags.append(f"missing characters: {', '.join(sorted(missing_names))}")
        seen.add("missing")

    for r in reasons:
        rl = r.lower()
        tag = None
        if "missing" in rl and "missing" not in seen and "character" in rl:
            tag = "missing character(s)"; seen.add("missing")
        elif "unexpected" in rl and ("character" in rl or "background" in rl):
            tag = "unexpected/extra character(s)"
        elif "lightning" in rl and ("inside" in rl or "indoor" in rl or "in the room" in rl):
            tag = "environment artifact (indoor lightning)"
        elif "wardrobe" in rl or "outfit" in rl or ("pajamas" in rl and "match" in rl) or ("dress" in rl and "match" in rl):
            tag = "wardrobe mismatch (vs manifest)"
        elif "hair" in rl and ("color" in rl or "style" in rl or "different" in rl or "off" in rl):
            tag = "hair drift"
        elif "continuity" in rl:
            tag = "continuity break"
        elif "window" in rl or "layout" in rl or ("location" in rl and "match" not in rl) or ("room" in rl and "drift" in rl):
            tag = "location/room drift"
        elif "artifact" in rl or "extra limb" in rl or "morph" in rl:
            tag = "visible artifacts"
        elif "identity" in rl:
            tag = "character identity drift"
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def render_markdown_report(
    scene_label: str,
    results: list[ShotValidationResult],
    total_cost_usd: float,
    backend: str,
    model: str,
) -> str:
    lines: list[str] = []
    lines.append(f"# {scene_label} - Reference-Aware Shot Validation Report")
    lines.append("")
    lines.append(f"Backend: `{backend}`  |  Model: `{model}`  |  Validator: `scripts/validate/shot_validator.py`")
    lines.append("")
    sheet_path = next((r.media_paths.get("identity_sheet") for r in results
                       if r.media_paths.get("identity_sheet")), str(DEFAULT_IDENTITY_SHEET))
    unsheeted = sorted({c for r in results
                        for c in r.media_paths.get("characters_without_identity_sheet", [])})
    lines.append(
        "Each keyframe was described by the vision model in a fixed attribute "
        "vocabulary - hair colour, length, texture, build, eyewear, facial "
        "hair, age, skin tone, styling, face shape - and that description was "
        "diffed **in code** against the locked identity sheet "
        f"(`{sheet_path}`). The model is not shown the turnarounds and never "
        "emits an identity score; the score and the pass/fail gate are both "
        "computed by the validator. Every identity number below is traceable "
        "to the two attribute rows it came from.\n\n"
        "Headline scores are the WORST keyframe, not the mean - a character "
        "off-model in one keyframe of three makes an off-model shot. Means are "
        "in the JSON under `*_mean`.\n\n"
        "`no_reference` means identity was NOT VERIFIED - the character was not "
        "visible, or has no row in the identity sheet. It is not a pass."
    )
    if unsheeted:
        lines.append("")
        lines.append(
            f"**Unverified characters** (no identity sheet row): "
            f"{', '.join(unsheeted)}. Their identity was not checked at all."
        )
    lines.append("")

    # Executive summary - validator's flagged issues per shot
    lines.append("## Validator findings (TL;DR)")
    lines.append("")
    for r in results:
        gate = "PASS" if r.overall_pass else "FAIL"
        flags = _short_flag(r.reasons) or (["(no issues flagged)"] if r.overall_pass else ["(generic failure)"])
        lines.append(f"- **{r.shot_id} - {gate}**: " + "; ".join(flags))
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Shot | Pass? | Presence | Location | Continuity | Artifacts | Identity (avg) | Wardrobe (avg) | # Reasons |")
    lines.append("|------|-------|----------|----------|------------|-----------|----------------|----------------|-----------|")
    for r in results:
        agg = r.aggregate_scores
        ids = agg.get("character_identity", {})
        id_avg = (sum(ids.values()) / len(ids)) if ids else None
        id_str = f"{id_avg:.2f}" if id_avg is not None else "n/a"
        wds = agg.get("character_wardrobe", {})
        wd_avg = (sum(wds.values()) / len(wds)) if wds else None
        wd_str = f"{wd_avg:.2f}" if wd_avg is not None else "n/a"
        gate = "PASS" if r.overall_pass else "FAIL"
        lines.append(
            f"| {r.shot_id} | **{gate}** | {agg.get('character_presence',0):.2f} | "
            f"{agg.get('location_match',0):.2f} | {agg.get('continuity',0):.2f} | "
            f"{agg.get('artifacts',0):.2f} | {id_str} | {wd_str} | {len(r.reasons)} |"
        )
    lines.append("")
    in_tot = sum(r.usage["input_tokens"] for r in results)
    out_tot = sum(r.usage["output_tokens"] for r in results)
    lines.append(
        f"**Total API usage:** {in_tot:,} input tokens + {out_tot:,} output tokens. "
        f"**Estimated cost:** ${total_cost_usd:.4f}."
    )
    lines.append("")

    # Per-shot detail
    lines.append("## Per-Shot Breakdown")
    lines.append("")
    for r in results:
        agg = r.aggregate_scores
        gate = "PASS" if r.overall_pass else "FAIL"
        lines.append(f"### Shot {r.shot_id} - {gate}")
        lines.append("")
        lines.append("**Aggregate scores:**")
        lines.append(f"- character_presence: {agg.get('character_presence',0):.2f}")
        if agg.get("character_identity"):
            id_strs = ", ".join(f"{k}: {v:.2f}" for k, v in agg["character_identity"].items())
            lines.append(f"- character_identity: {id_strs}")
        if agg.get("character_identity_no_reference"):
            lines.append(
                f"- character_identity (no reference, not scored): "
                f"{', '.join(agg['character_identity_no_reference'])}"
            )
        if agg.get("character_wardrobe"):
            wd_strs = ", ".join(f"{k}: {v:.2f}" for k, v in agg["character_wardrobe"].items())
            lines.append(f"- character_wardrobe: {wd_strs}")
        if agg.get("character_wardrobe_no_reference"):
            lines.append(
                f"- character_wardrobe (not visible, not scored): "
                f"{', '.join(agg['character_wardrobe_no_reference'])}"
            )
        lines.append(f"- location_match: {agg.get('location_match',0):.2f}")
        lines.append(f"- continuity: {agg.get('continuity',0):.2f}")
        lines.append(f"- artifacts: {agg.get('artifacts',0):.2f}")
        lines.append("")
        if r.reasons:
            lines.append("**Failure reasons:**")
            for reason in r.reasons:
                lines.append(f"- {reason}")
            lines.append("")
        # Per-keyframe drill-down
        lines.append("<details><summary>Per-keyframe detail</summary>")
        lines.append("")
        for i, kf in enumerate(r.keyframes):
            label = ["first", "mid", "last"][i] if i < 3 else f"k{i}"
            lines.append(f"**Keyframe {label}** ({Path(kf.get('_keyframe_path','')).name})")
            cp = kf.get("character_presence", {})
            lines.append(
                f"- presence: {cp.get('score',0):.2f} "
                f"(observed: {', '.join(cp.get('observed',[])) or 'none'} | "
                f"missing: {', '.join(cp.get('missing',[])) or 'none'} | "
                f"unexpected: {', '.join(cp.get('unexpected',[])) or 'none'})"
            )
            ci = kf.get("character_identity", {})
            for ch, info in ci.items():
                if info.get("no_reference"):
                    lines.append(f"- identity[{ch}]: NOT VERIFIED - {info.get('notes','')}")
                    continue
                lines.append(
                    f"- identity[{ch}]: {info.get('score',0):.2f} "
                    f"({info.get('verdict','?')}) - {info.get('notes','')}")
                fa = info.get("frame_attributes") or {}
                ra = info.get("reference_attributes") or {}
                diffs = [k for k in ra if fa.get(k) != ra.get(k)]
                if diffs:
                    lines.append("  | attribute | turnaround sheet | this frame |")
                    lines.append("  |---|---|---|")
                    for k in diffs:
                        flag = " **(defining)**" if k in (info.get("defining_mismatches") or []) else ""
                        lines.append(f"  | {k}{flag} | {ra.get(k)} | {fa.get(k)} |")
            cw = kf.get("character_wardrobe", {})
            for ch, info in cw.items():
                if info.get("no_reference"):
                    lines.append(f"- wardrobe[{ch}]: not visible - {info.get('notes','')}")
                else:
                    exp = info.get("expected", "")
                    exp_str = f" (expected: {exp})" if exp else ""
                    lines.append(
                        f"- wardrobe[{ch}]: {info.get('score',0):.2f}{exp_str} - "
                        f"{info.get('notes','')}"
                    )
            lm = kf.get("location_match", {})
            lines.append(f"- location: {lm.get('score',0):.2f} - {lm.get('notes','')}")
            cn = kf.get("continuity", {})
            if cn.get("no_prior_shot"):
                lines.append(f"- continuity: n/a (no prior shot or different location)")
            else:
                same_loc = " [same location]" if cn.get("same_location_as_prior") else ""
                lines.append(f"- continuity: {cn.get('score',0):.2f}{same_loc} - {cn.get('notes','')}")
            art = kf.get("artifacts", {})
            det = ", ".join(art.get("detected", [])) or "none"
            lines.append(f"- artifacts: {art.get('score',0):.2f} - detected: {det} - {art.get('notes','')}")
            if kf.get("model_notes"):
                lines.append("- model commentary: " + " | ".join(kf["model_notes"]))
            lines.append(f"- keyframe overall_pass: {kf.get('overall_pass')}")
            if kf.get("reasons"):
                for reason in kf["reasons"]:
                    lines.append(f"  - {reason}")
            lines.append("")
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_manifest(path: Path) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def _match_footage(shot_id: str, footage_dir: Path) -> Optional[Path]:
    if not footage_dir.exists():
        return None
    for p in sorted(footage_dir.iterdir()):
        if not p.is_file():
            continue
        if shot_id.lower() in p.stem.lower():
            return p
    return None


def cmd_validate_shot(args: argparse.Namespace) -> int:
    manifest = _load_manifest(Path(args.manifest))
    shot = next((s for s in manifest if s["shot_id"] == args.shot_id), None)
    if shot is None:
        print(f"Shot {args.shot_id} not found in {args.manifest}", file=sys.stderr)
        return 2
    media = Path(args.footage)
    if not media.exists():
        print(f"Footage not found: {media}", file=sys.stderr)
        return 2
    keyframes_dir = Path(args.keyframes_dir) if args.keyframes_dir else Path("./footage/keyframes")
    prior = Path(args.prior_keyframe) if args.prior_keyframe else None
    backend = args.backend
    model = args.model or _default_model_for_backend(backend)

    result = validate_shot(
        shot=shot,
        media_path=media,
        characters_dir=Path(args.characters_dir),
        locations_dir=Path(args.locations_dir),
        keyframes_dir=keyframes_dir,
        prior_keyframe=prior,
        backend=backend,
        model=model,
        identity_sheet=Path(args.identity_sheet) if args.identity_sheet else None,
    )

    out_dict = result.to_dict()
    out_dict["backend"] = backend
    out_dict["model"] = model
    out_dict["estimated_cost_usd"] = round(
        estimate_cost(model, result.usage["input_tokens"], result.usage["output_tokens"]), 4
    )

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(out_dict, f, indent=2)
        print(f"Wrote {args.out}")
    else:
        print(json.dumps(out_dict, indent=2))
    return 0 if result.overall_pass else 1


def cmd_validate_panel(args: argparse.Namespace) -> int:
    """Validate a single still-panel image (storyboard PNG) against the bible."""
    manifest = _load_manifest(Path(args.manifest))
    shot = next((s for s in manifest if s["shot_id"] == args.shot_id), None)
    if shot is None:
        print(f"Shot {args.shot_id} not found in {args.manifest}", file=sys.stderr)
        return 2
    panel = Path(args.panel)
    if not panel.exists():
        print(f"Panel not found: {panel}", file=sys.stderr)
        return 2
    keyframes_dir = (
        Path(args.keyframes_dir) if args.keyframes_dir else Path("./footage/keyframes")
    )
    backend = args.backend
    model = args.model or _default_model_for_backend(backend)
    result = validate_panel(
        shot=shot,
        panel_path=panel,
        characters_dir=Path(args.characters_dir),
        locations_dir=Path(args.locations_dir),
        keyframes_dir=keyframes_dir,
        backend=backend,
        model=model,
        identity_sheet=Path(args.identity_sheet) if args.identity_sheet else None,
    )
    out_dict = result.to_dict()
    out_dict["backend"] = backend
    out_dict["model"] = model
    out_dict["estimated_cost_usd"] = round(
        estimate_cost(model, result.usage["input_tokens"], result.usage["output_tokens"]), 4
    )
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(out_dict, f, indent=2)
        print(f"Wrote {args.out}")
    else:
        print(json.dumps(out_dict, indent=2))
    return 0 if result.overall_pass else 1


def cmd_validate_scene(args: argparse.Namespace) -> int:
    manifest = _load_manifest(Path(args.manifest))
    footage_dir = Path(args.footage_dir)
    characters_dir = Path(args.characters_dir)
    locations_dir = Path(args.locations_dir)
    keyframes_dir = Path(args.keyframes_dir) if args.keyframes_dir else Path("./footage/keyframes")
    report_path = Path(args.report)
    json_path = report_path.with_suffix(".json")
    backend = args.backend
    model = args.model or _default_model_for_backend(backend)

    client = _make_client(backend)
    sheets = load_identity_sheets(
        Path(args.identity_sheet) if args.identity_sheet else None)
    problems = validate_identity_sheet(sheets)
    if problems:
        for pr in problems:
            print(f"  [problem] {pr}", file=sys.stderr)
        print("Refusing to run against a malformed identity sheet.", file=sys.stderr)
        return 2
    if not sheets:
        print("WARNING: no identity sheet found - identity will be reported as "
              "UNVERIFIED for every character. Run `build-sheets` first.",
              file=sys.stderr)
    results: list[ShotValidationResult] = []
    last_keyframe: Optional[Path] = None
    last_shot: Optional[dict] = None
    # (character_name, normalized_wardrobe_text) -> (canonical_keyframe, raw_text, source_shot_id)
    wardrobe_canonical: dict[tuple[str, str], tuple[Path, str, str]] = {}

    for shot in manifest:
        media = _match_footage(shot["shot_id"], footage_dir)
        if media is None:
            print(f"[skip] No footage for {shot['shot_id']} in {footage_dir}")
            continue
        print(f"[validate] {shot['shot_id']} -> {media.name}", flush=True)

        # Build per-shot wardrobe consistency refs: for each character in this
        # shot whose manifest wardrobe text matches one we have already seen
        # earlier in the scene, pass that prior keyframe as a consistency
        # reference. Skip the character if this is the first time we are seeing
        # that outfit (this shot becomes the canonical after validation).
        wardrobe_refs: dict[str, tuple[Path, str, str]] = {}
        for ch, desc in (shot.get("wardrobe") or {}).items():
            key = (ch, _wardrobe_key(desc))
            if key[1] and key in wardrobe_canonical:
                wardrobe_refs[ch] = wardrobe_canonical[key]

        result = validate_shot(
            shot=shot,
            media_path=media,
            characters_dir=characters_dir,
            locations_dir=locations_dir,
            keyframes_dir=keyframes_dir,
            prior_keyframe=last_keyframe,
            prior_shot=last_shot,
            wardrobe_refs=wardrobe_refs or None,
            backend=backend,
            model=model,
            client=client,
            sheets=sheets,
        )
        results.append(result)
        kf_paths = result.media_paths.get("keyframes", [])
        if kf_paths:
            last_keyframe = Path(kf_paths[-1])
        last_shot = shot

        # Record the canonical look for any (character, outfit) pair we have
        # not yet seen, using the middle keyframe as the canonical reference
        # (typically the most stable / least edge-of-shot frame).
        canonical_kf = Path(kf_paths[len(kf_paths) // 2]) if kf_paths else None
        if canonical_kf is not None:
            for ch, desc in (shot.get("wardrobe") or {}).items():
                key = (ch, _wardrobe_key(desc))
                if not key[1] or key in wardrobe_canonical:
                    continue
                wardrobe_canonical[key] = (canonical_kf, desc, shot["shot_id"])

        gate = "PASS" if result.overall_pass else "FAIL"
        print(f"  -> {gate}  reasons={len(result.reasons)}  "
              f"tokens(in/out)={result.usage['input_tokens']}/{result.usage['output_tokens']}")

    total_in = sum(r.usage["input_tokens"] for r in results)
    total_out = sum(r.usage["output_tokens"] for r in results)
    total_cost = estimate_cost(model, total_in, total_out)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump({
            "scene": args.scene_label,
            "backend": backend,
            "model": model,
            "shots": [r.to_dict() for r in results],
            "total_usage": {"input_tokens": total_in, "output_tokens": total_out},
            "estimated_cost_usd": round(total_cost, 4),
        }, f, indent=2)
    print(f"Wrote {json_path}")

    report = render_markdown_report(args.scene_label, results, total_cost, backend, model)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Wrote {report_path}")
    print(f"Total cost: ${total_cost:.4f}")
    return 0


def cmd_render_report(args: argparse.Namespace) -> int:
    """Re-render the markdown report from a previously saved JSON blob."""
    blob = json.loads(Path(args.json).read_text())
    results: list[ShotValidationResult] = []
    for shot_dict in blob["shots"]:
        results.append(ShotValidationResult(
            shot_id=shot_dict["shot_id"],
            keyframes=shot_dict.get("keyframes", []),
            overall_pass=shot_dict.get("overall_pass", False),
            aggregate_scores=shot_dict.get("aggregate_scores", {}),
            reasons=shot_dict.get("reasons", []),
            usage=shot_dict.get("usage", {"input_tokens": 0, "output_tokens": 0}),
            media_paths=shot_dict.get("media_paths", {}),
        ))
    cost = blob.get("estimated_cost_usd", 0.0)
    report = render_markdown_report(
        blob.get("scene", "Scene"),
        results,
        cost,
        blob.get("backend", "unknown"),
        blob.get("model", "unknown"),
    )
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(report)
    print(f"Wrote {args.report}")
    return 0



def build_identity_sheet(
    characters_dir: Path,
    *,
    backend: str = DEFAULT_BACKEND,
    model: Optional[str] = None,
    client=None,
) -> tuple[dict, dict]:
    """Derive a first-draft identity sheet from the locked turnarounds.

    One call per character, with that character's turnaround as the ONLY image
    in context - nothing to anchor to and nothing to agree with. The output is
    a DRAFT: read it against the turnarounds and correct it before committing.
    """
    if model is None:
        model = _default_model_for_backend(backend)
    if client is None:
        client = _make_client(backend)
    if backend != "gemini":
        raise NotImplementedError("build-sheets currently supports the gemini backend")

    from google.genai import types

    row_schema = {
        "type": "object",
        "properties": _identity_attr_schema(with_hints=True),
        "required": [a["key"] for a in IDENTITY_ATTRIBUTES],
    }
    prompt_lines = [
        "This is a locked character turnaround sheet from an animated film's "
        "asset bible. Describe the character as drawn, filling in every "
        "attribute from the fixed vocabularies below.",
        "",
        "Judge build from the body as drawn, not from what the clothes flatter. "
        "Judge hair length as worn down. Ignore the sheet's background, labels "
        "and height ruler.",
        "",
    ]
    for attr in IDENTITY_ATTRIBUTES:
        prompt_lines.append(f"  {attr['key']}: {' | '.join(attr['values'])}")
        if attr.get("hint"):
            prompt_lines.append(f"    {attr['hint']}")
    prompt = "\n".join(prompt_lines)

    sheets: dict[str, dict] = {}
    usage = {"input_tokens": 0, "output_tokens": 0}
    for f in sorted(characters_dir.iterdir()):
        if not f.is_file() or f.suffix.lower() not in _IMAGE_SUFFIXES:
            continue
        name = f.stem.split("_")[0].split("-")[0].title()
        block = _encode_image(f)
        img = types.Part.from_bytes(
            data=base64.b64decode(block["source"]["data"]),
            mime_type=block["source"]["media_type"])

        def _do_call():
            return client.models.generate_content(
                model=model,
                contents=[f"Character turnaround sheet - {name}:", img, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=row_schema,
                    temperature=0.0,
                    max_output_tokens=4096,
                ),
            )
        resp = _call_with_retry(_do_call, label=f"sheet:{name}")
        sheets[name] = json.loads(resp.text)
        um = getattr(resp, "usage_metadata", None)
        usage["input_tokens"] += getattr(um, "prompt_token_count", 0) or 0
        usage["output_tokens"] += ((getattr(um, "candidates_token_count", 0) or 0)
                                   + (getattr(um, "thoughts_token_count", 0) or 0))
        print(f"[sheet] {name}: " + ", ".join(
            f"{k}={sheets[name].get(k)}" for k in
            ("hair_colour", "hair_length", "hair_texture", "build", "eyewear", "facial_hair")),
            flush=True)
    return sheets, usage


def cmd_build_sheets(args: argparse.Namespace) -> int:
    sheets, usage = build_identity_sheet(
        Path(args.characters_dir), backend=args.backend, model=args.model)
    model = args.model or _default_model_for_backend(args.backend)
    out = Path(args.out)
    existing = {}
    if out.exists() and not args.overwrite:
        existing = json.loads(out.read_text()).get("characters", {})
        print(f"{out} exists; merging only characters not already in it "
              f"(pass --overwrite to replace). Existing: {sorted(existing)}")
    merged = dict(sheets)
    merged.update(existing)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "_comment": (
            "Locked identity attribute sheet: each character's turnaround "
            "expressed in the validator's fixed vocabularies. DRAFTED by "
            "`shot_validator.py build-sheets` and then CORRECTED BY A HUMAN "
            "against the turnarounds. Treat it as a bible artifact - changing "
            "a row changes what the validator considers on-model."),
        "_vocabularies": {a["key"]: a["values"] for a in IDENTITY_ATTRIBUTES},
        "characters": merged,
    }, indent=2) + "\n")
    problems = validate_identity_sheet(
        {k: v for k, v in merged.items() if isinstance(v, dict)})
    for p in problems:
        print(f"  [problem] {p}")
    cost = estimate_cost(model, usage["input_tokens"], usage["output_tokens"])
    print(f"Wrote {out} ({len(merged)} characters). Cost ${cost:.4f}.")
    print("NOW READ IT AGAINST THE TURNAROUNDS AND CORRECT IT before trusting "
          "any validation run.")
    return 1 if problems else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("validate-shot", help="Validate a single shot.")
    a.add_argument("--manifest", required=True)
    a.add_argument("--shot-id", required=True)
    a.add_argument("--footage", required=True)
    a.add_argument("--characters-dir", default="asset-bible/characters")
    a.add_argument("--locations-dir", default="asset-bible/locations")
    a.add_argument("--keyframes-dir", default=None)
    a.add_argument("--prior-keyframe", default=None)
    a.add_argument("--out", default=None)
    a.add_argument("--identity-sheet", default=None,
                   help="Locked identity attribute sheet (default: scripts/validate/identity-sheets.json).")
    a.add_argument("--backend", default=DEFAULT_BACKEND, choices=["claude", "gemini"])
    a.add_argument("--model", default=None,
                   help="Override the per-backend default model.")
    a.set_defaults(func=cmd_validate_shot)

    pa = sub.add_parser("validate-panel", help="Validate a single still-panel image (storyboard PNG).")
    pa.add_argument("--manifest", required=True)
    pa.add_argument("--shot-id", required=True)
    pa.add_argument("--panel", required=True,
                    help="Path to the still panel image (PNG/JPG/WEBP/GIF).")
    pa.add_argument("--characters-dir", default="asset-bible/characters")
    pa.add_argument("--locations-dir", default="asset-bible/locations")
    pa.add_argument("--keyframes-dir", default=None)
    pa.add_argument("--out", default=None)
    pa.add_argument("--identity-sheet", default=None,
                   help="Locked identity attribute sheet (default: scripts/validate/identity-sheets.json).")
    pa.add_argument("--backend", default=DEFAULT_BACKEND, choices=["claude", "gemini"])
    pa.add_argument("--model", default=None,
                    help="Override the per-backend default model.")
    pa.set_defaults(func=cmd_validate_panel)

    b = sub.add_parser("validate-scene", help="Validate every shot in a manifest, emit markdown report.")
    b.add_argument("--manifest", required=True)
    b.add_argument("--footage-dir", required=True)
    b.add_argument("--characters-dir", default="asset-bible/characters")
    b.add_argument("--locations-dir", default="asset-bible/locations")
    b.add_argument("--keyframes-dir", default=None)
    b.add_argument("--report", required=True)
    b.add_argument("--scene-label", default="Scene")
    b.add_argument("--identity-sheet", default=None,
                   help="Locked identity attribute sheet (default: scripts/validate/identity-sheets.json).")
    b.add_argument("--backend", default=DEFAULT_BACKEND, choices=["claude", "gemini"])
    b.add_argument("--model", default=None,
                   help="Override the per-backend default model.")
    b.set_defaults(func=cmd_validate_scene)

    s = sub.add_parser("build-sheets",
                       help="Draft the locked identity attribute sheet from the turnarounds.")
    s.add_argument("--characters-dir", default="asset-bible/characters")
    s.add_argument("--out", default=str(DEFAULT_IDENTITY_SHEET))
    s.add_argument("--overwrite", action="store_true",
                   help="Replace rows that already exist in --out.")
    s.add_argument("--backend", default=DEFAULT_BACKEND, choices=["claude", "gemini"])
    s.add_argument("--model", default=None)
    s.set_defaults(func=cmd_build_sheets)

    c = sub.add_parser("render-report",
                       help="Re-render the markdown report from a saved JSON blob (no API calls).")
    c.add_argument("--json", required=True)
    c.add_argument("--report", required=True)
    c.set_defaults(func=cmd_render_report)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
