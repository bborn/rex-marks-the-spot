"""
Rigging Review App - Human-in-the-loop review for character rigging quality.

Agents upload stress-test pose renders. Humans review, approve/reject, and leave feedback.
Tracks iterations per character so the rig-fix-review loop is organized.

Run: uvicorn app:app --host 0.0.0.0 --port 3090
"""

import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "reviews.db"
UPLOAD_DIR = APP_DIR / "uploads"
STATIC_DIR = APP_DIR / "static"

UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Rigging Review", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS iterations (
            id TEXT PRIMARY KEY,
            character_id TEXT NOT NULL REFERENCES characters(id),
            version INTEGER NOT NULL,
            rigging_tool TEXT,
            notes TEXT,
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS poses (
            id TEXT PRIMARY KEY,
            iteration_id TEXT NOT NULL REFERENCES iterations(id),
            pose_name TEXT NOT NULL,
            image_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',  -- pending, approved, rejected
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            pose_id TEXT NOT NULL REFERENCES poses(id),
            comment TEXT NOT NULL,
            created_at REAL NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_iterations_char ON iterations(character_id);
        CREATE INDEX IF NOT EXISTS idx_poses_iter ON poses(iteration_id);
        CREATE INDEX IF NOT EXISTS idx_feedback_pose ON feedback(pose_id);
    """)
    conn.commit()
    conn.close()


init_db()


# ---------------------------------------------------------------------------
# HTML UI
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text()


# ---------------------------------------------------------------------------
# API: Characters
# ---------------------------------------------------------------------------

@app.get("/api/characters")
async def list_characters():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM characters ORDER BY created_at"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/characters")
async def create_character(name: str = Form(...)):
    cid = str(uuid.uuid4())[:8]
    conn = get_db()
    conn.execute(
        "INSERT INTO characters (id, name, created_at) VALUES (?, ?, ?)",
        (cid, name, time.time()),
    )
    conn.commit()
    conn.close()
    return {"id": cid, "name": name}


# ---------------------------------------------------------------------------
# API: Iterations
# ---------------------------------------------------------------------------

@app.get("/api/characters/{character_id}/iterations")
async def list_iterations(character_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM iterations WHERE character_id = ? ORDER BY version",
        (character_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/characters/{character_id}/iterations")
async def create_iteration(
    character_id: str,
    rigging_tool: str = Form(""),
    notes: str = Form(""),
):
    conn = get_db()
    # Check character exists
    char = conn.execute(
        "SELECT id FROM characters WHERE id = ?", (character_id,)
    ).fetchone()
    if not char:
        conn.close()
        raise HTTPException(404, "Character not found")

    # Auto-increment version
    last = conn.execute(
        "SELECT MAX(version) as v FROM iterations WHERE character_id = ?",
        (character_id,),
    ).fetchone()
    version = (last["v"] or 0) + 1

    iid = str(uuid.uuid4())[:8]
    conn.execute(
        "INSERT INTO iterations (id, character_id, version, rigging_tool, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (iid, character_id, version, rigging_tool, notes, time.time()),
    )
    conn.commit()
    conn.close()
    return {"id": iid, "version": version}


# ---------------------------------------------------------------------------
# API: Poses (upload + review)
# ---------------------------------------------------------------------------

@app.get("/api/iterations/{iteration_id}/poses")
async def list_poses(iteration_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM poses WHERE iteration_id = ? ORDER BY pose_name",
        (iteration_id,),
    ).fetchall()
    result = []
    for r in rows:
        pose = dict(r)
        # Include feedback
        fb = conn.execute(
            "SELECT * FROM feedback WHERE pose_id = ? ORDER BY created_at",
            (r["id"],),
        ).fetchall()
        pose["feedback"] = [dict(f) for f in fb]
        result.append(pose)
    conn.close()
    return result


@app.post("/api/iterations/{iteration_id}/poses")
async def upload_pose(
    iteration_id: str,
    pose_name: str = Form(...),
    image: UploadFile = File(...),
):
    conn = get_db()
    # Check iteration exists
    it = conn.execute(
        "SELECT id FROM iterations WHERE id = ?", (iteration_id,)
    ).fetchone()
    if not it:
        conn.close()
        raise HTTPException(404, "Iteration not found")

    # Save image
    ext = Path(image.filename or "image.png").suffix or ".png"
    pid = str(uuid.uuid4())[:8]
    filename = f"{iteration_id}_{pose_name}_{pid}{ext}"
    filepath = UPLOAD_DIR / filename
    content = await image.read()
    filepath.write_bytes(content)

    conn.execute(
        "INSERT INTO poses (id, iteration_id, pose_name, image_path, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
        (pid, iteration_id, pose_name, filename, time.time()),
    )
    conn.commit()
    conn.close()
    return {"id": pid, "pose_name": pose_name, "image_path": filename}


@app.put("/api/poses/{pose_id}/status")
async def update_pose_status(pose_id: str, status: str = Form(...)):
    if status not in ("pending", "approved", "rejected"):
        raise HTTPException(400, "Status must be pending, approved, or rejected")
    conn = get_db()
    conn.execute("UPDATE poses SET status = ? WHERE id = ?", (status, pose_id))
    conn.commit()
    conn.close()
    return {"id": pose_id, "status": status}


@app.post("/api/poses/{pose_id}/feedback")
async def add_feedback(pose_id: str, comment: str = Form(...)):
    conn = get_db()
    pose = conn.execute("SELECT id FROM poses WHERE id = ?", (pose_id,)).fetchone()
    if not pose:
        conn.close()
        raise HTTPException(404, "Pose not found")

    fid = str(uuid.uuid4())[:8]
    conn.execute(
        "INSERT INTO feedback (id, pose_id, comment, created_at) VALUES (?, ?, ?, ?)",
        (fid, pose_id, comment, time.time()),
    )
    conn.commit()
    conn.close()
    return {"id": fid, "comment": comment}


# ---------------------------------------------------------------------------
# API: Summary / Dashboard
# ---------------------------------------------------------------------------

@app.get("/api/summary")
async def summary():
    """Overall review status across all characters."""
    conn = get_db()
    chars = conn.execute("SELECT * FROM characters ORDER BY created_at").fetchall()
    result = []
    for c in chars:
        iters = conn.execute(
            "SELECT * FROM iterations WHERE character_id = ? ORDER BY version DESC LIMIT 1",
            (c["id"],),
        ).fetchone()
        if iters:
            poses = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM poses WHERE iteration_id = ? GROUP BY status",
                (iters["id"],),
            ).fetchall()
            status_counts = {r["status"]: r["cnt"] for r in poses}
        else:
            status_counts = {}
        result.append({
            "character": dict(c),
            "latest_version": iters["version"] if iters else 0,
            "latest_iteration_id": iters["id"] if iters else None,
            "pose_status": status_counts,
        })
    conn.close()
    return result


# ---------------------------------------------------------------------------
# API: Bulk upload (convenience for agents)
# ---------------------------------------------------------------------------

@app.post("/api/bulk-upload")
async def bulk_upload(
    character_name: str = Form(...),
    rigging_tool: str = Form(""),
    notes: str = Form(""),
    pose_names: str = Form(...),  # comma-separated
    images: list[UploadFile] = File(...),
):
    """
    Upload all stress test renders for a character in one request.
    Creates character (if new), iteration, and all poses.
    """
    names = [n.strip() for n in pose_names.split(",")]
    if len(names) != len(images):
        raise HTTPException(400, f"Got {len(names)} pose names but {len(images)} images")

    conn = get_db()

    # Get or create character
    char = conn.execute(
        "SELECT id FROM characters WHERE name = ?", (character_name,)
    ).fetchone()
    if char:
        cid = char["id"]
    else:
        cid = str(uuid.uuid4())[:8]
        conn.execute(
            "INSERT INTO characters (id, name, created_at) VALUES (?, ?, ?)",
            (cid, character_name, time.time()),
        )

    # Create iteration
    last = conn.execute(
        "SELECT MAX(version) as v FROM iterations WHERE character_id = ?", (cid,)
    ).fetchone()
    version = (last["v"] or 0) + 1
    iid = str(uuid.uuid4())[:8]
    conn.execute(
        "INSERT INTO iterations (id, character_id, version, rigging_tool, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (iid, cid, version, rigging_tool, notes, time.time()),
    )

    # Save poses
    results = []
    for name, image in zip(names, images):
        ext = Path(image.filename or "image.png").suffix or ".png"
        pid = str(uuid.uuid4())[:8]
        filename = f"{iid}_{name}_{pid}{ext}"
        filepath = UPLOAD_DIR / filename
        content = await image.read()
        filepath.write_bytes(content)
        conn.execute(
            "INSERT INTO poses (id, iteration_id, pose_name, image_path, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
            (pid, iid, name, filename, time.time()),
        )
        results.append({"id": pid, "pose_name": name, "image_path": filename})

    conn.commit()
    conn.close()
    return {
        "character_id": cid,
        "iteration_id": iid,
        "version": version,
        "poses": results,
    }


# ---------------------------------------------------------------------------
# Serve uploaded images
# ---------------------------------------------------------------------------

@app.get("/uploads/{filename}")
async def serve_upload(filename: str):
    filepath = UPLOAD_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "Image not found")
    return FileResponse(str(filepath))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
