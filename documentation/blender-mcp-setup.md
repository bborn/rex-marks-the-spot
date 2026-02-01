# BlenderMCP Setup Guide

This guide documents how to set up and use BlenderMCP for interactive Blender control via Claude.

## Overview

BlenderMCP enables Claude to directly control Blender through the Model Context Protocol (MCP). This allows for:
- Creating and modifying 3D objects through natural language
- Getting scene information and screenshots
- Importing assets from Poly Haven
- Executing custom Blender Python code
- Interactive scene iteration with real-time feedback

## Architecture

```
┌──────────────┐     MCP Protocol    ┌──────────────┐     TCP Socket    ┌──────────────┐
│  Claude Code │ ◀───────────────▶ │  blender-mcp  │ ◀──────────────▶  │   Blender    │
│    (CLI)     │                     │   (Server)   │      :9876         │   (Addon)    │
└──────────────┘                     └──────────────┘                    └──────────────┘
```

1. **Claude Code** connects to the **blender-mcp** MCP server
2. **blender-mcp** translates MCP tool calls to socket commands
3. **Blender Addon** receives commands and executes them in Blender
4. Results flow back through the same chain

## Requirements

### System Requirements
- Linux (tested on Ubuntu 22.04)
- Blender 3.0 or newer (tested with 4.0.2)
- Python 3.10 or newer

### For Headless Servers
```bash
sudo apt install xvfb libxrender1 libxxf86vm1 libxfixes3 libxi6 \
    libsm6 libgl1 libxkbcommon0 libegl1 mesa-utils
```

## Installation

### 1. Install uv Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Add to your PATH (add to `~/.bashrc` or `~/.zshrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

Verify installation:
```bash
uv --version
uvx --version
```

### 2. Install Blender Addon

The addon is already included in this repository at `scripts/blender-addons/blender_mcp_addon.py`.

**Option A: Automatic Installation**
```bash
# Copy addon to Blender's addons directory
mkdir -p ~/.config/blender/4.0/scripts/addons
cp scripts/blender-addons/blender_mcp_addon.py ~/.config/blender/4.0/scripts/addons/

# Enable the addon
blender -b -P scripts/enable_blender_mcp_addon.py
```

**Option B: Manual Installation (GUI)**
1. Open Blender
2. Edit > Preferences > Add-ons
3. Click "Install..."
4. Select `scripts/blender-addons/blender_mcp_addon.py`
5. Enable "Interface: Blender MCP"
6. Save Preferences

### 3. Configure MCP for Claude Code

The project includes `.mcp.json` which configures the blender-mcp server:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"],
      "env": {
        "PATH": "/home/rex/.local/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

## Usage

### Starting the Blender Server

#### On Desktop (with display)
1. Open Blender
2. Press `N` to open the sidebar (if not visible)
3. Go to the "BlenderMCP" tab
4. Click "Connect to MCP server"
5. Server starts on `localhost:9876` by default

#### On Headless Server
```bash
./scripts/start_blender_mcp.sh [port]

# Examples:
./scripts/start_blender_mcp.sh        # Default port 9876
./scripts/start_blender_mcp.sh 9877   # Custom port
```

The script will:
1. Start Xvfb virtual display (if no DISPLAY)
2. Launch Blender with the MCP addon
3. Start the socket server
4. Keep running until Ctrl+C

### Using with Claude Code

Once the Blender server is running, Claude can use MCP tools:

```
Claude, create a red cube at position (0, 0, 1)
```

Claude will use the `create_object` tool to create the cube in Blender.

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `get_blender_scene_info` | Get scene objects, materials, and settings |
| `create_object` | Create primitive objects (cube, sphere, cylinder, etc.) |
| `modify_object` | Transform, scale, rotate objects |
| `delete_object` | Remove objects from scene |
| `set_material` | Apply materials to objects |
| `get_object_info` | Get details about a specific object |
| `execute_blender_code` | Execute arbitrary Python code in Blender |
| `get_polyhaven_assets` | Browse Poly Haven asset library |
| `download_polyhaven_asset` | Download and import Poly Haven assets |
| `get_hyper3d_models` | Access Hyper3D model generation |
| `get_sketchfab_models` | Search Sketchfab 3D models |

## Troubleshooting

### Server won't start
1. Check if port 9876 is already in use: `lsof -i :9876`
2. Verify addon is enabled: Check Blender preferences
3. Check Blender console for error messages

### Connection refused
1. Ensure Blender server is running first
2. Check firewall settings
3. Verify correct port number

### Xvfb errors on headless server
```bash
# Install required packages
sudo apt install xvfb

# Check if Xvfb can start
Xvfb :99 -screen 0 1920x1080x24 &
echo $?  # Should be 0
```

### MCP tools not available
1. Verify `.mcp.json` exists in project root
2. Restart Claude Code after configuration changes
3. Check `uvx blender-mcp` works from command line

### First command fails
This is a known issue. Simply retry the command.

## Integration with Production Pipeline

BlenderMCP is designed for **interactive development**. For production rendering:

1. Use BlenderMCP to iterate on scenes interactively
2. Export final scripts to `scripts/` directory
3. Run headless renders with:
   ```bash
   blender -b scene.blend -P render_script.py
   ```

This allows:
- Fast iteration during development (MCP)
- Reproducible production renders (Python scripts)
- Both pipelines working together

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BLENDER_PATH` | Path to Blender executable | `blender` |
| `DISPLAY` | X11 display (auto-set by Xvfb) | - |

### Blender Addon Settings

Access in Blender via View3D > Sidebar > BlenderMCP:
- **Port**: Socket server port (default: 9876)
- **Auto-connect**: Start server when Blender opens

### MCP Server Configuration

In `.mcp.json`:
```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"],
      "env": {
        "PATH": "..."
      }
    }
  }
}
```

## Resources

- [BlenderMCP GitHub](https://github.com/ahujasid/blender-mcp)
- [BlenderMCP Website](https://blender-mcp.com/)
- [Blender Python API](https://docs.blender.org/api/current/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Poly Haven](https://polyhaven.com/)
