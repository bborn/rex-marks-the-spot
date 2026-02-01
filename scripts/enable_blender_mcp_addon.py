#!/usr/bin/env python3
"""
Enable BlenderMCP addon in Blender.

Usage:
    blender -b -P scripts/enable_blender_mcp_addon.py
"""

import bpy

def enable_addon():
    """Enable the BlenderMCP addon and save preferences."""
    addon_name = "blender_mcp_addon"

    # Refresh addon list
    bpy.ops.preferences.addon_refresh()

    # Check if addon is available
    addons = bpy.context.preferences.addons

    # Enable the addon
    try:
        bpy.ops.preferences.addon_enable(module=addon_name)
        print(f"Successfully enabled addon: {addon_name}")
    except Exception as e:
        print(f"Error enabling addon: {e}")
        return False

    # Save preferences so it persists
    bpy.ops.wm.save_userpref()
    print("User preferences saved.")

    return True

if __name__ == "__main__":
    success = enable_addon()
    if success:
        print("\nBlenderMCP addon is now installed and enabled!")
        print("To start the MCP server:")
        print("  1. Open Blender with GUI")
        print("  2. Go to View3D > Sidebar > BlenderMCP")
        print("  3. Click 'Start Server'")
    else:
        print("\nFailed to enable addon.")
