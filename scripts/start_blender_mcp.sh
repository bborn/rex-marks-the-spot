#!/bin/bash
# Start Blender with MCP server enabled for headless operation
#
# This script starts Blender with the MCP addon server running.
# On headless servers, it uses Xvfb to provide a virtual display.
#
# Usage:
#   ./scripts/start_blender_mcp.sh [port]
#
# Arguments:
#   port - MCP server port (default: 9876)
#
# Environment:
#   DISPLAY - If set, uses existing display
#   BLENDER_PATH - Path to Blender executable (default: blender)
#
# Requirements for headless operation:
#   sudo apt install xvfb libxrender1 libxxf86vm1 libxfixes3 libxi6 libsm6 libgl1 libxkbcommon0 libegl1 mesa-utils

set -e

PORT="${1:-9876}"
BLENDER="${BLENDER_PATH:-blender}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if display is available
USE_XVFB=false
if [ -z "$DISPLAY" ]; then
    echo "No display detected - checking for Xvfb..."

    if command -v Xvfb &> /dev/null; then
        USE_XVFB=true
        echo "Xvfb found - will start virtual display"

        # Find an available display number
        DISPLAY_NUM=99
        while [ -e "/tmp/.X${DISPLAY_NUM}-lock" ]; do
            DISPLAY_NUM=$((DISPLAY_NUM + 1))
        done

        # Start Xvfb
        Xvfb :${DISPLAY_NUM} -screen 0 1920x1080x24 &
        XVFB_PID=$!
        export DISPLAY=:${DISPLAY_NUM}

        # Wait for Xvfb to start
        sleep 1

        echo "Xvfb started on display :${DISPLAY_NUM} (PID: $XVFB_PID)"

        # Cleanup on exit
        cleanup() {
            echo ""
            echo "Shutting down..."
            kill $XVFB_PID 2>/dev/null || true
            echo "Xvfb stopped"
        }
        trap cleanup EXIT
    else
        echo "ERROR: No display available and Xvfb not installed."
        echo ""
        echo "BlenderMCP requires a display for the socket server to work."
        echo ""
        echo "Install Xvfb with:"
        echo "  sudo apt install xvfb libxrender1 libxxf86vm1 libxfixes3 libxi6 libsm6 libgl1 libxkbcommon0 libegl1 mesa-utils"
        echo ""
        exit 1
    fi
fi

echo ""
echo "========================================"
echo "Starting Blender with MCP Server"
echo "========================================"
echo "Display:  ${DISPLAY}"
echo "Port:     ${PORT}"
echo "Blender:  ${BLENDER}"
echo "========================================"
echo ""

# Create a temporary Python script to start the server
PYTHON_SCRIPT=$(mktemp /tmp/blender_mcp_start.XXXXXX.py)
cat > "$PYTHON_SCRIPT" << 'PYTHON'
"""
Start BlenderMCP server and keep Blender running.
"""
import bpy
import sys
import time
import signal

def get_port():
    """Get port from command line args."""
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        if args:
            return int(args[0])
    return 9876

def start_server():
    """Start the BlenderMCP server."""
    # Import the server class from the addon
    import importlib
    addon_module = importlib.import_module("blender_mcp_addon")
    BlenderMCPServer = addon_module.BlenderMCPServer

    port = get_port()

    # Create and store server instance
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        print("Server already running, stopping first...")
        bpy.types.blendermcp_server.stop()

    bpy.types.blendermcp_server = BlenderMCPServer(port=port)
    bpy.types.blendermcp_server.start()

    # Mark as running
    bpy.context.scene.blendermcp_server_running = True

    print("")
    print("=" * 50)
    print(f"BlenderMCP server is running on localhost:{port}")
    print("=" * 50)
    print("")
    print("The server is ready to accept connections from Claude.")
    print("Keep this process running while using Claude with Blender.")
    print("")
    print("Press Ctrl+C to stop the server.")
    print("")

    return True

# Start the server
start_server()

# Keep Blender running (for headless mode)
# The server runs in a background thread, but Blender needs to stay alive
def keep_alive():
    """Timer function to keep Blender alive."""
    return 1.0  # Call again in 1 second

bpy.app.timers.register(keep_alive)
PYTHON

# Cleanup temp file on exit
cleanup_script() {
    rm -f "$PYTHON_SCRIPT"
}
trap cleanup_script EXIT

# Start Blender with the script
# Note: We don't use -b (background) because MCP needs some GUI components
"${BLENDER}" --python "$PYTHON_SCRIPT" -- "${PORT}"
