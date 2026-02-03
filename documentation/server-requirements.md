# Server Requirements

To run the "Fairy Dinosaur Date Night" production pipeline and board server, the following software must be installed on the host machine (e.g., Hetzner instance).

## Core Requirements

### Git & Git LFS
Required for pulling the repository and binary assets (blender files, images).

```bash
sudo apt update
sudo apt install git git-lfs
git lfs install
```

### Node.js (for Board Server)
Required for the TaskYou board real-time API.

- Node.js LTS (v20+)
- npm

(See `scripts/board-server/setup.sh` for automated installation)

### Blender (for Rendering/MCP)
Required for 3D operations.

- Blender 4.0+
- Xvfb (for headless operation)

(See `scripts/start_blender_mcp.sh` and `documentation/blender-mcp-setup.md` for details)

## Setup Checklist

1. [ ] Install system dependencies (`git`, `git-lfs`, `xvfb`)
2. [ ] Clone repository
3. [ ] Run `git lfs pull` to fetch assets
4. [ ] Run `scripts/board-server/setup.sh` to start the API server
5. [ ] Configure `.env` or environment variables
