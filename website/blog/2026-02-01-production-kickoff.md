# Production Kickoff: Building an Animated Film with AI

**February 1, 2026**

We're making an animated movie, and we're doing it differently.

"Fairy Dinosaur Date Night" is the story of two kids, Mia (8) and Leo (5), who must rescue their parents after they accidentally drive through a time warp and get stranded in the Jurassic era. They're aided by Ruben, a depressed fairy godfather whose magic is rusty, and Jetplane, a lovable dinosaur who farts colors. It's weird, it's heartfelt, and it's entirely produced using AI-orchestrated workflows.

This is the first progress report for **Rex Marks the Spot**, our experiment in AI-assisted filmmaking.

---

## What We've Accomplished

### The Story Foundation

The screenplay is complete. 37 scenes across three acts, running approximately 85-95 minutes. We've broken it down into a comprehensive production bible:

- **Scene Breakdown**: Every scene documented with emotional beats, location details, and production notes
- **Shot List**: 513+ camera shots planned with VFX complexity ratings
- **Director's Analysis**: Character arcs, pacing analysis, and potential cuts/expansions

The structure follows a classic family adventure arc:

| Act | Scenes | Runtime | Focus |
|-----|--------|---------|-------|
| Act 1 | 10 | ~12 min | The Departure & The Jurassic |
| Act 2 | 15 | ~20 min | Investigation, Connection, The Fairy Godfather |
| Act 3 | 12 | ~15 min | The Rescue & The Return |

### Storyboards: 498 Panels Complete

We've completed detailed storyboards for all three acts:

- **Act 1**: 56 panels across 10 scenes
- **Act 2**: 83 panels across 15 scenes
- **Act 3**: 359 panels across 12 scenes (the climax is detailed)

Each panel includes composition notes, camera movements, character positions, and VFX requirements. We've also created animatic timing guides for key sequences.

### Character Design Concepts

Full design documentation for all six main characters:

- **Mia**: 8-year-old protagonist, turquoise scrunchie, purple star shirt, determined eyes
- **Leo**: 5-year-old brother, messy hair, freckles, gap-tooth grin, dinosaur obsession
- **Gabe & Nina**: The parents, starting in formal anniversary attire that deteriorates throughout
- **Ruben**: Fairy godfather with emotion-reactive droopy wings and worn fairy clothes
- **Jetplane**: Teal-scaled dinosaur with big amber eyes, ear-frills, and rainbow fart particles

Each character has turnaround sheets, expression guides, color palettes (with hex codes), and AI generation prompts for consistent visual development.

### The Blender Pipeline

This is where things get technical. We've built a pipeline for Claude to control Blender:

**BlenderMCP Integration**: We're using BlenderMCP (14,500+ stars on GitHub) to give Claude direct control over Blender. Claude can create objects, modify materials, set up lighting, and position cameras in real-time.

**Headless Rendering**: Our proof-of-concept scripts demonstrate full Cycles rendering without a GUI. This enables batch rendering on servers and cloud infrastructure.

**Vision Validation Loop**: Claude can render a scene, analyze the output image, and iterate. The feedback loop looks like this:

```
Claude generates Blender Python script
    ↓
Blender executes in headless mode
    ↓
Image rendered to file
    ↓
Claude Vision analyzes the render
    ↓
Claude refines and iterates
```

We've tested this with a scene that creates ground planes, character placeholders, three-point lighting, camera tracking, and procedural sky shaders.

---

## Our AI-First Approach

This project is orchestrated by [TaskYou](https://taskyou.dev), which manages Claude agents working in parallel across different production tasks.

Here's what that means in practice:

1. **Tasks are defined as GitHub issues**: "Create Act 1 storyboards," "Research Blender integration," "Design Mia's expressions"
2. **Each task runs in its own git worktree**: Isolated branches for parallel work without conflicts
3. **Claude agents execute the tasks**: Reading context, exploring the codebase, generating assets, writing documentation
4. **Everything is version controlled**: Every decision, every asset, every iteration is tracked

This isn't about replacing human creativity. The screenplay was written by a human. The creative vision is human. But the production pipeline—the tedious, repetitive, technically complex work of turning a screenplay into an animated film—that's where AI shines.

We're transparent about this: every commit message, every document, every piece of this project identifies where AI was involved.

---

## Technical Highlights

### Git Worktrees for Parallel Production

Traditional production has bottlenecks. You can't do character design until the screenplay is locked. You can't storyboard until characters are designed. We're breaking those dependencies.

With git worktrees, multiple Claude agents work simultaneously on different branches. Act 1 storyboards were being refined while Act 3 was being created. Character design happened in parallel with pipeline development.

### MCP (Model Context Protocol) Integration

MCP lets Claude interact with external tools through a standardized interface. For this project:

- **BlenderMCP**: Direct control of Blender scenes, materials, and rendering
- **File operations**: Reading/writing production documents
- **Git operations**: Version control and branch management

### Headless Infrastructure

Everything is designed to run without a GUI. This means:

- Rendering on cloud servers with GPUs
- Batch processing of animation frames
- CI/CD pipelines for automated asset generation

---

## What's Next

We're in early production. Here's the roadmap:

### Near Term
- **3D Modeling**: Converting character designs into rigged Blender models
- **Environment Assets**: Building the key locations (minivan, Jurassic forest, meadow)
- **Animation Tests**: First motion tests with placeholder geometry

### Medium Term
- **Voice Pipeline**: Text-to-speech prototyping for dialogue
- **Music & Sound**: AI-assisted soundtrack development
- **Lighting Setups**: Per-scene lighting rigs

### Long Term
- **Full Animation**: Scene-by-scene production
- **Rendering**: Final quality output
- **Post-Production**: Color grading, effects, titles

---

## Following Along

This is a public experiment. We'll share progress, failures, and lessons learned. The goal isn't just to make a film—it's to document a new way of making films.

Everything we learn will be published here. Technical deep-dives, production diaries, and honest assessments of what works and what doesn't.

The tools are available. The techniques are evolving. And we're finding out what's possible.

---

*This is Rex Marks the Spot. Let's see where it goes.*
