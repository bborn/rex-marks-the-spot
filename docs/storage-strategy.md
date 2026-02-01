# Asset Storage Strategy for Fairy Dinosaur Date Night

*Research completed: February 2026*

## Executive Summary

**Recommended approach: Hybrid Storage with Tiered Architecture**

| Tier | Storage | Use Case | Cost |
|------|---------|----------|------|
| **Hot** | Hetzner local SSD | Active working files | ~€5/TB/mo |
| **Warm** | Backblaze B2 | Recent renders, shared assets | $6/TB/mo |
| **Archive** | Backblaze B2 (lifecycle) | Final renders, old versions | $6/TB/mo |
| **Source** | Git (GitHub) | Code, scripts, docs | Free |
| **Public CDN** | Cloudflare R2 | Website assets, public downloads | $15/TB/mo |

**Estimated monthly cost for this project: $15-40/month** (depending on project phase)

---

## Project Asset Analysis

### Current State

Based on analysis of the codebase:

- **6 main characters** with comprehensive design documentation
- **37 scenes** across 3 acts
- **75 concept art images** planned (tracked in IMAGE-MANIFEST.md)
- **56+ storyboard panels** in Act 1 alone
- **Rendering pipeline** already built (scripts/render/, scripts/validate/)
- **No binary assets** currently in Git (properly ignored via .gitignore)

### Projected Storage Requirements

| Asset Type | Estimated Size | Frequency | Retention |
|------------|----------------|-----------|-----------|
| Concept art (AI-generated) | ~50MB each × 75 = ~4GB | One-time generation | Permanent |
| Character turnarounds | ~20MB each × 6 = ~120MB | Occasional updates | Permanent |
| 3D models (.blend) | ~50-200MB each | Per character/scene | Permanent |
| Textures & materials | ~500MB-2GB total | As needed | Permanent |
| Test renders (1080p) | ~5-20MB each | Frequent | Delete after 7 days |
| Production renders (4K) | ~50-100MB each | Per shot | Permanent |
| Animation caches | ~1-10GB per scene | Per render | Temporary |
| Final video outputs | ~1-5GB per minute | Per version | Versioned |

**Conservative estimate: 50-100GB active, 500GB-1TB archive over project lifetime**

---

## Option Analysis

### 1. Hetzner Local Storage

**Best for:** Active working files requiring fast access

**Pricing (as of 2026):**
- Storage Box: ~€3/TB/month (BX11: 1TB for €3.81/mo)
- Object Storage (S3-compatible): €4.99/mo includes 1TB storage + 1TB egress
- Additional storage: €0.0067/TB-hour (~€5/TB/month)
- **Unlimited ingress**, egress included in quota

**Pros:**
- Cheapest storage option available
- GDPR-compliant (EU data residency)
- 100% green electricity
- Multiple protocols: WebDAV, FTP, SFTP, rsync, S3
- Low latency if running Hetzner servers

**Cons:**
- Limited geographic redundancy
- No built-in CDN
- Egress beyond quota costs extra

**Use case:** Working files, active renders, Blender project files

---

### 2. Backblaze B2

**Best for:** Cost-effective cloud backup and sharing

**Pricing (as of 2026):**
- Storage: **$6/TB/month** (cheapest major cloud provider)
- Egress: Free up to 3× monthly storage (e.g., 10TB storage = 30TB free egress)
- Free egress to CDN partners: Cloudflare, Fastly, bunny.net
- First 10GB free

**Pros:**
- S3-compatible API
- Free CDN partner egress (Cloudflare integration)
- 11 nines durability
- Simple, predictable pricing
- Native rclone support

**Cons:**
- Class B/C API calls have costs (minimal for our use)
- Not as fast as local storage

**Use case:** Backup, archive, shared assets, final renders

---

### 3. Cloudflare R2

**Best for:** Public-facing assets and CDN delivery

**Pricing (as of 2026):**
- Storage: **$15/TB/month** ($0.015/GB)
- Egress: **$0** (zero egress fees - major differentiator)
- Class A operations: $4.50/million
- Class B operations: $0.36/million
- Free tier available

**Pros:**
- Zero egress fees (critical for public assets)
- Global CDN built-in
- S3-compatible API
- Excellent for high-traffic public content

**Cons:**
- More expensive storage than B2
- Better suited for delivery than archival

**Use case:** Website assets, public downloads, trailer hosting, production stills

---

### 4. Git LFS

**Best for:** Version-controlled binary assets (limited)

**Pricing (GitHub, as of 2026):**
- Free tier: 10GB storage + 10GB bandwidth/month
- Data packs: $5/50GB additional storage+bandwidth

**Pros:**
- Integrates with existing Git workflow
- True version control for binaries
- Good for small, frequently-updated assets

**Cons:**
- Bandwidth limits make it expensive at scale
- 2GB max file size (Free), 4GB (Team)
- Each version stored separately (quick bloat)
- Not suitable for rendered outputs

**Use case:** Character reference sheets, style guides, small textures (<50MB)

---

### 5. What Real Studios Do

| Studio Type | Primary Storage | Backup | Archive |
|-------------|-----------------|--------|---------|
| **Pixar/Disney** | Petabyte on-prem + tape | Multi-site replication | LTO tape libraries |
| **Mid-size studios** | NAS (Synology/QNAP) | Cloud (B2/Wasabi) | Cold cloud tier |
| **Indie studios** | Cloud object storage | Same provider, different bucket | Lifecycle policies |
| **Solo/small teams** | Local SSD + cloud sync | B2/R2 | Same as backup |

---

## Recommended Architecture

### Tier Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                      ASSET STORAGE TIERS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   LOCAL     │    │  BACKBLAZE  │    │  CLOUDFLARE │         │
│  │   (Hot)     │───▶│  B2 (Warm)  │───▶│  R2 (CDN)   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│       │                   │                   │                 │
│  • Active .blend    • Final renders     • Public assets        │
│  • Working renders  • Approved assets   • Trailer/previews     │
│  • Temp caches      • Version archive   • Website content      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                        GIT (GitHub)                         ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │  • Source code (scripts/, blender/)                         ││
│  │  • Documentation (docs/, documentation/)                    ││
│  │  • Screenplay, storyboards (text only)                     ││
│  │  • Configuration files                                      ││
│  │  • Small reference images via Git LFS (optional)           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### File Organization

```
# Backblaze B2 Bucket Structure
fairy-dino-assets/
├── characters/
│   ├── mia/
│   │   ├── concept-art/
│   │   ├── 3d-models/
│   │   └── textures/
│   ├── leo/
│   ├── jetplane/
│   └── ...
├── environments/
│   ├── living-room/
│   ├── backyard/
│   └── ...
├── renders/
│   ├── act1/
│   │   ├── scene01/
│   │   │   ├── shot001_v001.exr
│   │   │   ├── shot001_v002.exr
│   │   │   └── shot001_final.exr
│   │   └── scene02/
│   ├── act2/
│   └── act3/
├── video/
│   ├── dailies/
│   ├── cuts/
│   │   ├── rough-cut_v001.mp4
│   │   └── rough-cut_v002.mp4
│   └── final/
└── archive/
    └── 2026-01/
        └── deprecated-assets/

# Cloudflare R2 (Public CDN)
fairy-dino-public/
├── website/
│   ├── images/
│   ├── videos/
│   └── downloads/
├── social/
│   ├── instagram/
│   └── youtube/
└── press-kit/
```

### Naming Conventions

```
# Characters
{character}_{asset-type}_{variant}_v{version}.{ext}
mia_turnaround_neutral_v003.png
jetplane_model_rigged_v001.blend

# Renders
{scene}_{shot}_{frame-range}_v{version}.{ext}
scene01_shot003_f0001-0120_v002.exr

# Video
{project}_{cut-type}_v{version}_{date}.{ext}
fddn_rough-cut_v003_2026-02-01.mp4
```

---

## Cost Estimation

### Phase 1: Pre-Production (Current - 3 months)

| Item | Storage | Monthly Cost |
|------|---------|--------------|
| Concept art generation | ~5GB | $0.30 |
| Character design iterations | ~2GB | $0.12 |
| Storyboard images | ~1GB | $0.06 |
| **Total B2** | ~8GB | **~$0.50/mo** |

### Phase 2: Production (6-12 months)

| Item | Storage | Monthly Cost |
|------|---------|--------------|
| 3D models & rigs | ~20GB | $1.20 |
| Textures & materials | ~10GB | $0.60 |
| Test renders (rolling) | ~50GB | $3.00 |
| Production renders | ~100GB | $6.00 |
| Animation caches | ~50GB (temp) | $0 (local only) |
| **Total B2** | ~180GB | **~$11/mo** |

### Phase 3: Post-Production (3-6 months)

| Item | Storage | Monthly Cost |
|------|---------|--------------|
| All production assets | ~200GB | $12.00 |
| Video edits & cuts | ~100GB | $6.00 |
| Final renders (4K) | ~200GB | $12.00 |
| Public CDN (R2) | ~20GB | $0.30 |
| **Total** | ~520GB | **~$30/mo** |

### Total Project Cost (18 months)

| Phase | Duration | Monthly Avg | Subtotal |
|-------|----------|-------------|----------|
| Pre-production | 3 months | $5 | $15 |
| Production | 9 months | $15 | $135 |
| Post-production | 6 months | $35 | $210 |
| **Total** | 18 months | - | **~$360** |

*Note: This is conservative. Actual costs depend on render resolution, iteration count, and retention policies.*

---

## Implementation Plan

### Phase 1: Setup (Week 1)

1. **Create Backblaze B2 account**
   - Create bucket: `fairy-dino-assets`
   - Enable versioning
   - Set lifecycle rule: move to "cold" after 90 days of no access
   - Generate application key for rclone

2. **Create Cloudflare R2 bucket** (when needed for public assets)
   - Create bucket: `fairy-dino-public`
   - Connect to Cloudflare CDN
   - Set up custom domain (optional)

3. **Install and configure rclone**
   - Set up B2 remote
   - Set up R2 remote
   - Test sync operations

### Phase 2: Workflow Integration (Week 2)

1. **Create sync scripts** (see below)
2. **Update pipeline.py** to auto-upload approved renders
3. **Document workflow** for team members
4. **Set up .gitignore** patterns (already done)

---

## Setup Scripts

### scripts/storage/sync_to_b2.sh

```bash
#!/bin/bash
# Sync local renders to Backblaze B2
# Usage: ./sync_to_b2.sh [--dry-run]

set -euo pipefail

B2_BUCKET="fairy-dino-assets"
LOCAL_RENDERS="./renders"
REMOTE_PATH="renders/$(date +%Y-%m)"

DRY_RUN=""
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN="--dry-run"
    echo "DRY RUN MODE - no files will be transferred"
fi

echo "Syncing renders to B2..."
rclone sync $DRY_RUN \
    --progress \
    --transfers 8 \
    --checkers 16 \
    --exclude "*.tmp" \
    --exclude "**/cache/**" \
    --min-size 1k \
    "$LOCAL_RENDERS" \
    "b2:$B2_BUCKET/$REMOTE_PATH"

echo "Sync complete!"
rclone size "b2:$B2_BUCKET"
```

### scripts/storage/rclone_config_template.conf

```ini
# Rclone configuration template
# Copy to ~/.config/rclone/rclone.conf and fill in credentials

[b2]
type = b2
account = YOUR_B2_ACCOUNT_ID
key = YOUR_B2_APPLICATION_KEY
hard_delete = true

[r2]
type = s3
provider = Cloudflare
access_key_id = YOUR_R2_ACCESS_KEY
secret_access_key = YOUR_R2_SECRET_KEY
endpoint = https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
acl = private
```

### scripts/storage/cleanup_temp_renders.sh

```bash
#!/bin/bash
# Remove temporary renders older than 7 days
# Run via cron: 0 2 * * * /path/to/cleanup_temp_renders.sh

set -euo pipefail

RENDERS_DIR="./renders"
DAYS_OLD=7

echo "Cleaning up temporary renders older than $DAYS_OLD days..."

find "$RENDERS_DIR" \
    -type f \
    \( -name "*.tmp" -o -name "*_test_*" -o -name "*_preview_*" \) \
    -mtime +$DAYS_OLD \
    -print \
    -delete

echo "Cleanup complete!"
```

### scripts/storage/upload_to_cdn.py

```python
#!/usr/bin/env python3
"""Upload approved assets to Cloudflare R2 for public CDN delivery."""

import subprocess
import sys
from pathlib import Path

R2_BUCKET = "fairy-dino-public"
PUBLIC_ASSETS = [
    ("./assets/characters/*/concept-art/*.png", "website/characters/"),
    ("./renders/final/*.mp4", "website/videos/"),
    ("./docs/press-kit/*", "press-kit/"),
]

def sync_to_r2(local_pattern: str, remote_path: str, dry_run: bool = False):
    """Sync files matching pattern to R2."""
    cmd = [
        "rclone", "copy",
        "--include", Path(local_pattern).name,
        str(Path(local_pattern).parent),
        f"r2:{R2_BUCKET}/{remote_path}",
        "--progress",
    ]
    if dry_run:
        cmd.append("--dry-run")

    subprocess.run(cmd, check=True)

def main():
    dry_run = "--dry-run" in sys.argv

    for local_pattern, remote_path in PUBLIC_ASSETS:
        print(f"Syncing {local_pattern} -> {remote_path}")
        sync_to_r2(local_pattern, remote_path, dry_run)

    print("CDN sync complete!")

if __name__ == "__main__":
    main()
```

---

## Video Output Versioning Strategy

For final video outputs, use semantic versioning with clear milestones:

```
# Version format: {major}.{minor}.{patch}
# major = significant story changes
# minor = scene/shot changes
# patch = technical fixes (color, audio sync)

fairy-dino-date-night_v0.1.0_rough-cut.mp4      # First assembly
fairy-dino-date-night_v0.2.0_rough-cut.mp4      # Scene reordering
fairy-dino-date-night_v1.0.0_picture-lock.mp4   # Picture lock
fairy-dino-date-night_v1.0.1_color-grade.mp4    # Color correction
fairy-dino-date-night_v1.1.0_final.mp4          # Final with audio

# Keep changelog in video/CHANGELOG.md
```

---

## Backup Strategy

### 3-2-1 Rule

- **3 copies** of important data
- **2 different storage types** (local SSD + cloud)
- **1 offsite** (Backblaze B2)

### What to Back Up

| Priority | Assets | Backup Frequency |
|----------|--------|------------------|
| Critical | Source files (.blend, scripts) | Git + daily B2 sync |
| High | Final renders, approved assets | After each approval |
| Medium | Work-in-progress renders | Weekly |
| Low | Test renders, caches | Don't backup (regenerate) |

### Recovery Time Objectives

| Asset Type | Max Recovery Time | Strategy |
|------------|-------------------|----------|
| Source code | < 1 hour | Git clone |
| 3D models | < 4 hours | B2 download |
| Final renders | < 8 hours | B2 download |
| Full project | < 24 hours | Full B2 restore |

---

## Security Considerations

1. **Access control**: Use separate B2 application keys per use case
2. **Encryption**: B2 encrypts at rest; enable for sensitive assets
3. **Versioning**: Enable B2 versioning to protect against accidental deletion
4. **Lifecycle policies**: Auto-delete old versions after 90 days
5. **Audit logs**: Enable B2 event notifications for compliance

---

## Recommendations Summary

| Requirement | Recommendation | Rationale |
|-------------|----------------|-----------|
| Working files | Local SSD | Speed for Blender operations |
| Backup & archive | Backblaze B2 | Cheapest at $6/TB, free CDN egress |
| Public delivery | Cloudflare R2 | Zero egress, global CDN |
| Source control | Git (GitHub) | Already in use, works well |
| Large binary versioning | B2 with naming convention | Git LFS too expensive at scale |
| Video versioning | Semantic versioning + changelog | Clear milestone tracking |

**Total estimated project cost: ~$360 over 18 months** (or ~$20/month average)

---

## Next Steps

1. [ ] Create Backblaze B2 account and bucket
2. [ ] Install rclone and configure remotes
3. [ ] Create `scripts/storage/` directory with sync scripts
4. [ ] Update pipeline to auto-sync approved renders
5. [ ] Document workflow in team onboarding docs
6. [ ] Set up lifecycle policies for cost optimization

---

## References

- [Backblaze B2 Pricing](https://www.backblaze.com/cloud-storage/pricing)
- [Cloudflare R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [Hetzner Storage Box](https://www.hetzner.com/storage/storage-box/)
- [Git LFS Billing](https://docs.github.com/billing/managing-billing-for-git-large-file-storage/about-billing-for-git-large-file-storage)
- [CG Wire: Animation Asset Storage](https://blog.cg-wire.com/animation-asset-storage/)
- [Rclone Documentation](https://rclone.org/docs/)
