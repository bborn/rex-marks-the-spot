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

## Rendering Pipeline

- **Interactive development**: Use BlenderMCP for scene building
- **Production rendering**: Use headless Blender with Python scripts in `scripts/`
- **Validation**: Rendered images can be analyzed for scene validation
