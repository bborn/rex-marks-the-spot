# Project Instructions for Claude

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

### Project Context

This is the "Fairy Dinosaur Date Night" animated movie production project. Key characters:
- Gabe & Nina (parents)
- Mia & Leo (kid protagonists)
- Ruben (fairy godfather)
- Jetplane (color-farting dinosaur)

### Rendering Pipeline

- **Interactive development**: Use BlenderMCP for scene building
- **Production rendering**: Use headless Blender with Python scripts in `scripts/`
- **Validation**: Rendered images can be analyzed for scene validation
