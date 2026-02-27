# Rex Marks the Spot

AI-orchestrated animated movie production for **"Fairy Dinosaur Date Night"**

## Synopsis

Two kids, Mia and Leo, must rescue their parents after they accidentally drive through a time warp and get stranded in the Jurassic era. With help from a depressed fairy godfather named Ruben and a lovable dinosaur named Jetplane (who farts colors), they embark on an adventure through prehistoric time.

## Project Structure

```
rex-marks-the-spot/
├── screenplay/          # Source screenplay
├── assets/
│   ├── characters/      # Character models & rigs
│   ├── environments/    # Scene backgrounds & sets
│   ├── props/           # Object models
│   └── audio/           # Sound effects & music
├── animation/
│   ├── scenes/          # Blender scene files
│   └── renders/         # Rendered output
├── scripts/             # Automation & pipeline scripts
│   ├── blender/         # Blender Python modules (scene, objects, etc.)
│   ├── render/          # Headless render pipeline
│   ├── validate/        # Vision validation with Claude
│   └── pipeline.py      # Main orchestration script
├── renders/             # Rendered output files
└── docs/                # Production documentation
    └── pipeline-guide.md # Pipeline usage guide
```

## How We Work

This isn't a typical animation project — there's no render farm full of humans. The entire production is orchestrated by AI agents managed through [TaskYou OS](https://github.com/taskyou/taskyou-os).

A human director (Bruno) sets creative direction and makes final calls. A GM agent (Claude Code) breaks that vision into concrete tasks — storyboard panels, 3D models, video clips, code. Worker agents running on a Linux server pick up those tasks and execute them autonomously, producing real assets. TaskYou handles the queuing, agent sessions, and orchestration that keeps the whole thing moving.

The result: a production pipeline where dozens of tasks can run in parallel, each agent working in its own isolated git worktree, pushing PRs when done.

## Tools & Pipeline

| Tool | Role |
|------|------|
| [TaskYou OS](https://github.com/taskyou/taskyou-os) | Task orchestration — queuing, agent sessions, worktrees |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | GM agent that coordinates work + worker agents that execute tasks |
| Gemini | Image generation (storyboards, concept art, visual assets) |
| [Meshy](https://www.meshy.ai) | 3D model generation and auto-rigging from 2D concept art |
| Wan / Veo | Video generation (drafts via Wan on Replicate, finals via Veo) |
| [Blender 4.x](https://www.blender.org) | 3D scene assembly, rendering, and animation |
| [Cloudflare R2](https://www.cloudflare.com/developer-platform/r2/) | Asset storage (images, video, 3D models — kept out of git) |

## Characters

- **Gabe & Nina** - The parents
- **Mia & Leo** - The kid protagonists  
- **Ruben** - Fairy godfather
- **Jetplane** - Color-farting dinosaur companion

## License

All rights reserved. Screenplay by Bruno Bornsztein.
