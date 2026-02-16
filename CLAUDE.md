# Project Instructions for Claude

## CRITICAL: Real Work, Not Documentation

**This project exists to CREATE AN ANIMATED MOVIE, not to generate documentation.**

### What "Done" Actually Means

A task is NOT complete when you have:
- Written a markdown file describing what should be done
- Created placeholder files or templates
- Generated prompts for future use
- Documented a strategy or plan

A task IS complete when you have:
- Created actual deliverables (real images, real 3D models, real video)
- Set up actual accounts/infrastructure that works
- Generated actual content that can be used in the movie
- Built actual integrations that produce output

### When to Ask for Human Help

Some things require human intervention. **ASK CLEARLY** when you need:
- Account creation (social media, API keys, service signups)
- Payment/billing decisions
- Creative direction decisions
- Access to credentials or services you cannot reach

Format: "**HUMAN ACTION NEEDED:** [specific thing you need them to do]"

### Image Generation

For storyboards, concept art, and visual assets:
1. Use the Gemini image generation skill (nano banana) when available
2. Or integrate with available image APIs (DALL-E, Stability AI, etc.)
3. **Generate actual images, not just prompts**

### The Goal

We are making "Fairy Dinosaur Date Night" - an AI-generated animated movie.

Every task should move us closer to having:
- Actual rendered scenes
- Actual character models
- Actual storyboard images
- Actual audio/music
- Actual video output

**If your output is just markdown, you have not completed the task.**

---

## BlenderMCP Integration

This project has BlenderMCP configured for interactive 3D scene control.

### Before Using Blender Tools

Before using any Blender MCP tools, ensure the Blender server is running:

1. **On a machine with display**: Open Blender, go to View3D > Sidebar > BlenderMCP, click "Connect to MCP server"

2. **On headless server**: Run `./scripts/start_blender_mcp.sh` (requires Xvfb installed)

### Available MCP Tools

When the BlenderMCP server is running, you can use tools like:
- `get_blender_scene_info` - Get information about the current scene
- `create_object` - Create new 3D objects
- `modify_object` - Modify existing objects
- `set_material` - Set materials on objects
- `execute_blender_code` - Execute arbitrary Blender Python code
- `get_polyhaven_assets` - Browse Poly Haven assets
- `download_polyhaven_asset` - Download assets from Poly Haven

## Project Context

This is the "Fairy Dinosaur Date Night" animated movie production project.

### Key Characters
- **Gabe & Nina** (parents)
- **Mia & Leo** (kid protagonists)
- **Ruben** (fairy godfather)
- **Jetplane** (color-farting dinosaur)

### Key Locations
- Family home (cozy, warm lighting)
- The magic minivan
- Jurassic swamp/jungle
- Cave hideout

## 3D Character Pipeline (PROVEN - Feb 2025)

**DO NOT** manually rig characters. DO NOT use Auto-Rig Pro, Rigify, or Mixamo for rigging.
Use Meshy's auto-rig — it produces clean deformation that survives FBX export to Blender.

### The Pipeline

1. **Generate 2D turnaround** — concept art showing character from front/side/back
2. **Meshy image-to-3D** — upload turnaround to https://www.meshy.ai, generate 3D model
3. **Meshy auto-rig** — apply Meshy's built-in rigging (biped). This produces good vertex weights.
4. **Apply animation in Meshy** — pick from 500+ preset animations or use custom
5. **Export FBX from Meshy** — download with "Skin" option (bakes animation + mesh)
6. **Import FBX into Blender**:
   ```python
   bpy.ops.import_scene.fbx(
       filepath="path/to/file.fbx",
       use_anim=True,
       ignore_leaf_bones=False,
       automatic_bone_orientation=True,
   )
   ```
7. **Re-apply textures in Blender** — FBX from Meshy comes with 0 materials; download PBR textures separately from Meshy and apply them in Blender

### What We Tried That DIDN'T Work

- **Auto-Rig Pro from scratch**: Destroyed mesh detail, head detached, limbs disappeared
- **Auto-Rig Pro hybrid** (Meshy rig + ARP cleanup): Shirt stretching, cylinder limbs
- **Rigify**: Poor weight painting on stylized characters
- **Mixamo**: Limited bone count, bad deformation on non-humanoid proportions

The core issue: re-rigging AI-generated meshes produces terrible vertex weights.
Meshy's auto-rig does a much better job because it understands the mesh it generated.

### Approved Character Turnarounds

- **Mia (original)**: `r2:rex-assets/characters/mia/mia_turnaround_APPROVED.png` — curly hair, most faithful to character design
- **Mia (animation-friendly)**: `r2:rex-assets/characters/mia/mia_turnaround_APPROVED_ALT.png` — simple wavy ponytail, no front wisps, best for 3D/animation

Use the ALT version for 3D model generation in Meshy. The original curly hair creates mesh artifacts (stray skin-colored geometry near the ears).

### Meshy Best Practices for Input Images

- Resolution: at least 1040x1040
- Plain white background, well-lit, no dramatic shadows
- A-pose (arms at 30-45 degrees from body)
- Avoid individual hair strands, wisps, or fine curly details — they create mesh artifacts
- Hair should be solid sculpted volumes, not individual strands

### Textures

FBX exports from Meshy include PBR texture PNGs (diffuse, normal, roughness, metallic) when downloaded WITHOUT rigging. Rigged FBX downloads may not include textures — download the static model separately to get the texture files, then apply them in Blender.

### Known Issues / TODOs

- **Custom animations**: For poses not in Meshy's library, need to figure out workflow
- **Multiple characters in scene**: Need to test importing multiple rigged FBX files

### Meshy FBX Import Details (for reference)

- Model comes in as 1 mesh + 1 armature (24 bones, 22 vertex groups)
- Walk cycle: ~30 frames, ~249 animation channels
- Bone names: Hips, Spine, Spine01, Spine02, LeftArm, RightArm, etc. (standard biped)

---

## Rendering Pipeline

- **Interactive development**: Use BlenderMCP for scene building
- **Production rendering**: Use headless Blender with Python scripts in `scripts/`
- **Validation**: Rendered images can be analyzed for scene validation

---

## Project Workflow & Reporting Structure

**See `docs/WORKFLOW.md` for the full production workflow guide**, including:
- Three parallel workstreams (Production, Built in Public, Community)
- Task type prefixes (`[design]`, `[generate]`, `[fix]`, etc.)
- Review gates and batch sizes
- Production pipeline phases

This project uses a hierarchical workflow with AI agents coordinated through TaskYou.

### The Team

- **Bruno (Director)** - Final creative authority. Makes decisions on direction, approves major work, provides feedback on quality and tone.
- **Assistant Director (Claude on Bruno's machine)** - Coordinates agents, monitors task progress, escalates decisions to Bruno, keeps things moving.
- **Remote Agents (Claude instances on task server)** - Execute individual tasks. Report back via PRs, commits, and task status updates.

### How It Works

1. **Tasks are created** on the remote TaskYou instance (ssh rex)
2. **Remote agents execute tasks** in isolated git worktrees
3. **Agents create PRs** when work is complete
4. **Assistant Director monitors** progress, approves routine work, unblocks stuck agents
5. **Director reviews** creative output, provides feedback, makes final calls

### Assistant Director Operating Guide

**Using TaskYou CLI on remote server:**
```bash
ssh rex "su - rex -c 'cd /home/rex/rex-marks-the-spot && ty <command>'"
```

Key commands:
- `ty list` - See all tasks
- `ty sessions` - See running agent sessions
- `ty output <id>` - See task output (what Claude sees)
- `ty input <id> <text>` - Send text input to a task
- `ty input <id> --enter` - Send Enter key
- `ty input <id> <number>` - Select menu option (but may need --enter after)
- `ty execute <id>` - Start a task
- `ty close <id>` - Close a task
- `ty retry <id>` - Retry a failed/stuck task
- `ty create` - Create new task

**Important operational notes:**
- `ty input` sends text but often needs `--enter` separately to submit
- When a task shows a numbered menu, send the number then `--enter`
- Don't assume sessions are "stale" just because `ty output` is empty - check with Bruno
- Don't auto-approve Bash commands - make informed decisions
- `workflow_get_project_context` MCP tool is safe to approve (read-only)
- Rate limits: Gemini image gen needs ~8 sec delays between requests
- Model for image gen: **`gemini-2.5-flash-image`** (minimum) or `gemini-3-pro-image-preview` (preferred)

### Communication

- Remote agents should **create clear PR descriptions** explaining what they did
- If an agent is stuck or needs a decision, it should **update the task with questions**
- The Assistant Director checks in regularly and **escalates to Bruno** when needed
- Bruno's feedback (on storyboards, blog posts, etc.) should inform future work

### Quality Control

- Run QA validation on generated assets before committing
- Check existing feedback before regenerating content
- Don't merge work that doesn't meet quality standards
- When QA flags issues, create follow-up tasks to fix them

### PR Workflow

**IMPORTANT: Fixes go on the SAME PR, not new ones.**

When there's feedback on a PR:
1. Make fixes on the SAME branch
2. Push to update the existing PR
3. Do NOT create a new PR for fixes

This keeps the PR history clean and avoids duplicate/conflicting PRs.

---

## Asset Storage (Cloudflare R2)

**DO NOT commit large files (images, video, audio) to git.**

Assets are stored in Cloudflare R2, not in the git repo. This avoids LFS budget issues.

### R2 Configuration

- **Bucket:** `rex-assets`
- **Public URL:** `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev`
- **Upload tool:** `rclone` (configured as `r2:` remote)

### Uploading Assets

```bash
# Upload a single file
rclone copy output.png r2:rex-assets/characters/family/

# Upload a directory
rclone copy ./generated-images/ r2:rex-assets/characters/family/action-poses/

# Or use the helper script
python scripts/r2_upload.py ./output/ characters/family/
```

### In Generation Scripts

```python
from r2_upload import upload_file, upload_directory

# After generating an image
url = upload_file("output.png", "characters/family/gabe.png")

# After generating multiple images
urls = upload_directory("./output/", "characters/family/action-poses/")
```

### What Goes Where

| Type | Storage | Why |
|------|---------|-----|
| Code, scripts | Git | Version controlled, small |
| Config, docs | Git | Version controlled, small |
| Generated images | R2 | Large, regeneratable |
| Video/audio | R2 | Very large |
| Storyboards | R2 | Many large images |
| 3D models | R2 | Large binary files |

### Referencing Assets

In HTML/docs, use the R2 public URL:
```html
<img src="https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/family/gabe.png">
```
