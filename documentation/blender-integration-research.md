# Blender + LLM Integration Research

## Executive Summary

Claude can effectively control Blender through multiple pathways, with the **BlenderMCP** server being the most mature solution. Headless rendering is fully supported via command line. A vision feedback loop is achievable using Claude's multimodal capabilities.

**Recommendation**: Use BlenderMCP for interactive control during development, with custom Python scripts for production rendering pipelines.

---

## 1. Blender Python API

### Capabilities

The Blender Python API (`bpy`) provides comprehensive access to nearly all Blender functionality:

| Category | What You Can Automate |
|----------|----------------------|
| **Objects** | Create, modify, delete, transform, parent/child relationships |
| **Modeling** | Mesh operations, modifiers, procedural geometry |
| **Materials** | Shaders, textures, node-based materials |
| **Animation** | Keyframes, constraints, drivers, NLA strips |
| **Rendering** | Camera setup, lighting, render settings, output |
| **Scene** | Collections, world settings, physics, particles |
| **Import/Export** | FBX, OBJ, glTF, USD, and custom formats |

### Script Execution Methods

1. **Embedded Text Editor** - Write/run scripts inside Blender
2. **Python Console** - Interactive REPL within Blender
3. **Command Line** - Execute scripts without GUI: `blender -b file.blend -P script.py`
4. **Blender as Python Module** - Import `bpy` in external Python apps

### Can Claude Write Blender Scripts?

**Yes.** Claude can generate complete `.py` scripts that Blender executes. The API is well-documented and Claude has strong knowledge of it.

**Sources:**
- [Blender Python API Documentation](https://docs.blender.org/api/current/index.html)
- [API Quickstart Guide](https://docs.blender.org/api/current/info_quickstart.html)
- [Scripting Introduction](https://docs.blender.org/manual/en/latest/advanced/scripting/introduction.html)

---

## 2. Headless Rendering

### How It Works

Blender supports headless (background) rendering via the `-b` flag:

```bash
# Basic render
blender -b scene.blend -o //output/frame_ -f 1

# Animation render with Cycles
blender -b scene.blend -E CYCLES -s 1 -e 100 -a

# Execute Python script in background
blender -b scene.blend -P render_script.py
```

### Requirements for Linux Servers

Install these packages for headless operation:

```bash
# Debian/Ubuntu
sudo apt install libxrender1 libxxf86vm1 libxfixes3 libxi6 libsm6 libgl1 libxkbcommon0 libegl1 mesa-utils

# RHEL/Fedora
sudo dnf install libXrender libXxf86vm libXfixes libXi libSM libGL libxkbcommon libEGL mesa-dri-drivers
```

### Render Engine Compatibility

| Engine | Headless Support | Notes |
|--------|------------------|-------|
| **Cycles** | Full support | CPU and GPU (CUDA/OptiX/HIP) |
| **Eevee** | No | Requires display; use Xvfb workaround |
| **Workbench** | Full support | Good for previews |

### Eevee Workaround (if needed)

```bash
# Use virtual framebuffer for Eevee
Xvfb :1 -screen 0 1920x1080x24 &
DISPLAY=:1 blender -b scene.blend -E BLENDER_EEVEE -f 1
```

**Sources:**
- [Rendering From Command Line](https://docs.blender.org/manual/en/latest/advanced/command_line/render.html)
- [HeadlessBlenderRenderer](https://github.com/Jackzmc/HeadlessBlenderRenderer)
- [Blender CLI Guide](https://renderday.com/blog/mastering-the-blender-cli)

---

## 3. Vision Feedback Loop

### Claude's Image Analysis Capabilities

Claude can analyze rendered images to validate:
- Scene composition and framing
- Object placement and relationships
- Material/color accuracy
- Lighting quality
- Animation frame correctness

### Technical Specifications

| Spec | Value |
|------|-------|
| Max resolution | 8000x8000 px |
| Formats | JPEG, PNG, GIF, WebP |
| Images per request | Up to 100 (API) |
| Multi-image comparison | Supported |

### Feedback Loop Architecture

```
┌─────────────┐    Script     ┌─────────────┐    Render    ┌─────────────┐
│   Claude    │ ──────────▶   │   Blender   │ ──────────▶  │   Image     │
│   (LLM)     │               │   (Python)  │              │   Output    │
└─────────────┘               └─────────────┘              └──────┬──────┘
       ▲                                                          │
       │                    Analysis                              │
       └──────────────────────────────────────────────────────────┘
```

### Implementation Pattern

```python
# Pseudocode for feedback loop
def render_and_validate():
    # 1. Generate/modify Blender script
    script = claude.generate_script(scene_description)

    # 2. Execute in Blender
    subprocess.run(['blender', '-b', 'scene.blend', '-P', script, '-o', 'render.png', '-f', '1'])

    # 3. Send render to Claude for validation
    with open('render.png', 'rb') as f:
        image_data = base64.b64encode(f.read())

    validation = claude.analyze_image(image_data, "Does this match the scene description?")

    # 4. Iterate if needed
    if validation.needs_changes:
        return render_and_validate(validation.suggestions)
```

### Limitations

- Claude cannot provide precise pixel coordinates
- Spatial measurements are approximate
- Best for qualitative validation, not pixel-perfect QA

**Sources:**
- [Claude Vision Documentation](https://docs.anthropic.com/en/docs/build-with-claude/vision)
- [Vision Best Practices](https://docs.claude.com/en/docs/build-with-claude/vision)

---

## 4. Existing Tools

### BlenderMCP (Recommended)

The most mature solution for Claude + Blender integration.

| Metric | Value |
|--------|-------|
| GitHub Stars | 14,500+ |
| License | MIT |
| Blender Version | 3.0+ |
| Python Version | 3.10+ |

**Features:**
- Direct Claude-to-Blender communication via MCP protocol
- Object creation, modification, deletion
- Material and texture control
- Scene inspection and querying
- **Viewport screenshots** for visual feedback
- Poly Haven asset integration
- Hyper3D Rodin model generation
- Sketchfab model downloads

**Installation:**

1. Install the Blender addon (`addon.py`)
2. Configure Claude Desktop:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"]
    }
  }
}
```

**Limitations:**
- Requires Blender GUI running (socket server)
- Complex operations may need multiple steps
- First command sometimes fails

**Sources:**
- [BlenderMCP GitHub](https://github.com/ahujasid/blender-mcp)
- [BlenderMCP Website](https://blender-mcp.com/)
- [Setup Tutorial](https://vagon.io/blog/how-to-use-blender-mcp-with-anthropic-claude-ai)

### Other Tools

| Tool | Purpose |
|------|---------|
| [HeadlessBlenderRenderer](https://github.com/Jackzmc/HeadlessBlenderRenderer) | Web UI + REST API for remote rendering |
| [Crowdrender](https://www.crowd-render.com/) | Distributed rendering across nodes |

---

## 5. Procedural Generation

### Python Libraries for Geometry Nodes

| Library | Description | Best For |
|---------|-------------|----------|
| [Geometry Script](https://superhivemarket.com/products/geometry-script) | Python API for Geometry Nodes | Production workflows |
| [pynodes](https://github.com/iplai/pynodes) | Full node system scripting | Shaders + geometry |
| [geonodes](https://github.com/al1brn/geonodes) | Clean Python interface | Maintainable code |

### What Can Be Generated Procedurally?

- **Terrain** - Fractal landscapes, heightmaps
- **Vegetation** - L-systems for trees/plants
- **Architecture** - Parametric buildings, procedural interiors
- **Props** - Modular assets, variations
- **Effects** - Particles, simulations
- **Characters** - Rigging automation, blend shapes

### Example: Procedural Scene Generation

```python
import bpy

def create_procedural_forest(num_trees=50, area_size=20):
    import random

    for i in range(num_trees):
        x = random.uniform(-area_size, area_size)
        y = random.uniform(-area_size, area_size)
        scale = random.uniform(0.5, 2.0)

        bpy.ops.mesh.primitive_cone_add(
            vertices=8,
            radius1=scale,
            depth=scale * 3,
            location=(x, y, scale * 1.5)
        )
        tree = bpy.context.active_object
        tree.name = f"Tree_{i}"
```

**Sources:**
- [Scripting Geometry Nodes](https://blog.cg-wire.com/blender-scripting-geometry-nodes-2/)
- [Procedural Content Generation Book](https://link.springer.com/book/10.1007/979-8-8688-1787-8)

---

## 6. Recommended Architecture

### For This Project (Fairy Dinosaur Date Night)

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐     ┌──────────────┐     ┌───────────────┐   │
│  │  Claude  │────▶│  Script Gen  │────▶│  Blender CLI  │   │
│  │  (Opus)  │     │  (.py files) │     │  (headless)   │   │
│  └──────────┘     └──────────────┘     └───────┬───────┘   │
│       ▲                                        │           │
│       │           ┌──────────────┐             │           │
│       └───────────│  Rendered    │◀────────────┘           │
│      Validation   │  Images/Video│                         │
│                   └──────────────┘                         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                   Development/Iteration                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐     ┌──────────────┐     ┌───────────────┐   │
│  │  Claude  │◀───▶│  BlenderMCP  │◀───▶│  Blender GUI  │   │
│  │  Desktop │     │  (socket)    │     │  (interactive)│   │
│  └──────────┘     └──────────────┘     └───────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Workflow

1. **Development Phase**: Use BlenderMCP for interactive scene building
2. **Production Phase**: Export scripts, run headless for batch rendering
3. **Validation Phase**: Send renders to Claude Vision for QA

---

## 7. Next Steps

### Immediate (This Task)
- [x] Research complete
- [x] Create proof-of-concept script
- [x] Test headless rendering locally

### Short-term (Completed in Pipeline Build)
- [x] Build automated rendering pipeline (`scripts/render/`)
- [x] Implement vision feedback loop for scene validation (`scripts/validate/`)
- [x] Create modular Blender automation library (`scripts/blender/`)
- [x] Document pipeline usage (`docs/pipeline-guide.md`)
- [ ] Install BlenderMCP and test Claude Desktop integration
- [ ] Create base scene template for the movie
- [ ] Define character asset requirements

### Medium-term
- [ ] Create procedural environment generators
- [ ] Add character rigging automation
- [ ] Build asset library management

---

## Appendix: Quick Reference Commands

```bash
# Render single frame
blender -b scene.blend -f 1

# Render animation
blender -b scene.blend -a

# Execute script
blender -b scene.blend -P script.py

# Render with specific engine
blender -b scene.blend -E CYCLES -f 1

# Output to specific path
blender -b scene.blend -o //renders/frame_ -f 1

# Set resolution
blender -b scene.blend --python-expr "import bpy; bpy.context.scene.render.resolution_x = 1920"

# List available render devices
blender -b --python-expr "import bpy; print(bpy.context.preferences.addons['cycles'].preferences.get_devices())"
```
