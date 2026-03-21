CREATE TABLE IF NOT EXISTS scenes (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  hero_shot_url TEXT,
  character_refs TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS panels (
  id TEXT PRIMARY KEY,
  scene_id TEXT NOT NULL,
  panel_number TEXT NOT NULL,
  name TEXT NOT NULL,
  start_url TEXT NOT NULL,
  end_url TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  video_url TEXT,
  scene_description TEXT,
  motion_prompt TEXT,
  FOREIGN KEY (scene_id) REFERENCES scenes(id)
);

CREATE TABLE IF NOT EXISTS annotations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  panel_id TEXT NOT NULL,
  type TEXT NOT NULL,
  frame TEXT NOT NULL,
  x REAL NOT NULL,
  y REAL NOT NULL,
  w REAL,
  h REAL,
  text TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (panel_id) REFERENCES panels(id)
);
