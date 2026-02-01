# Storage Scripts

Scripts for managing asset storage for the Fairy Dinosaur Date Night project.

## Overview

These scripts implement the hybrid storage strategy documented in [docs/storage-strategy.md](../../docs/storage-strategy.md).

## Quick Start

1. **Install rclone:**
   ```bash
   curl https://rclone.org/install.sh | sudo bash
   ```

2. **Configure storage remotes:**
   ```bash
   cp rclone_config_template.conf ~/.config/rclone/rclone.conf
   # Edit the file and add your credentials
   ```

3. **Test configuration:**
   ```bash
   rclone lsd b2:   # Should list B2 buckets
   rclone lsd r2:   # Should list R2 buckets
   ```

## Scripts

### sync_to_b2.sh

Syncs local renders to Backblaze B2 for backup/archive.

```bash
# Dry run (show what would be synced)
./sync_to_b2.sh --dry-run

# Actual sync
./sync_to_b2.sh

# Custom source directory
LOCAL_RENDERS=./renders/act1 ./sync_to_b2.sh
```

### cleanup_temp_renders.sh

Removes temporary render files older than 7 days.

```bash
# Dry run
./cleanup_temp_renders.sh --dry-run

# Clean files older than 14 days
./cleanup_temp_renders.sh --days 14

# Custom directory
./cleanup_temp_renders.sh --dir ./renders/test
```

### upload_to_cdn.py

Uploads approved public assets to Cloudflare R2 CDN.

```bash
# Dry run
python upload_to_cdn.py --dry-run

# Actual upload
python upload_to_cdn.py

# Verbose output
python upload_to_cdn.py --verbose
```

## Cron Jobs

Recommended cron entries for automated maintenance:

```cron
# Daily: Clean up temp renders at 2 AM
0 2 * * * /path/to/scripts/storage/cleanup_temp_renders.sh

# Weekly: Sync all renders to B2 on Sunday at 3 AM
0 3 * * 0 /path/to/scripts/storage/sync_to_b2.sh
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `B2_BUCKET` | Backblaze B2 bucket name | `fairy-dino-assets` |
| `R2_BUCKET` | Cloudflare R2 bucket name | `fairy-dino-public` |
| `LOCAL_RENDERS` | Local renders directory | `./renders` |
| `RENDERS_DIR` | Renders directory for cleanup | `./renders` |
| `DAYS_OLD` | Days before temp files are cleaned | `7` |

## Storage Layout

See [docs/storage-strategy.md](../../docs/storage-strategy.md) for the full storage architecture.

### Backblaze B2 (fairy-dino-assets)

```
fairy-dino-assets/
├── characters/       # Character assets (models, textures)
├── environments/     # Environment assets
├── renders/          # Production renders by date
│   └── 2026-02/
└── video/            # Video cuts and finals
```

### Cloudflare R2 (fairy-dino-public)

```
fairy-dino-public/
├── website/          # Public website assets
├── social/           # Social media exports
└── press-kit/        # Press materials
```
