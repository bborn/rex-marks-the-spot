# Rigging Review App

Human-in-the-loop review app for character rigging quality validation.

## Quick Start

```bash
# Install dependencies (one time)
pip3 install --break-system-packages fastapi uvicorn python-multipart aiofiles

# Start the app
./start.sh
# Access at http://rex:3090
```

## API Reference

### Characters
- `GET /api/characters` - List all characters
- `POST /api/characters` (form: name) - Create character

### Iterations
- `GET /api/characters/{id}/iterations` - List iterations
- `POST /api/characters/{id}/iterations` (form: rigging_tool, notes) - Create iteration

### Poses
- `GET /api/iterations/{id}/poses` - List poses with feedback
- `POST /api/iterations/{id}/poses` (form: pose_name, image file) - Upload pose render

### Review
- `PUT /api/poses/{id}/status` (form: status=pending|approved|rejected) - Set status
- `POST /api/poses/{id}/feedback` (form: comment) - Add feedback comment

### Bulk Upload (for agents)
- `POST /api/bulk-upload` (form: character_name, rigging_tool, notes, pose_names, images[]) - Upload all at once

### Dashboard
- `GET /api/summary` - Overall status across all characters
- `GET /health` - Health check

## Stress Test Script

Run in Blender to auto-pose and render:

```bash
blender model.blend --background --python stress_test_poses.py -- \
    --output ./renders/ \
    --character "Mia" \
    --tool "Auto-Rig Pro" \
    --notes "v1 initial rig" \
    --upload http://rex:3090
```
