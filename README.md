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

## Production Pipeline

This project uses [TaskYou](https://taskyou.dev) for AI-orchestrated task management and automation.

## Characters

- **Gabe & Nina** - The parents
- **Mia & Leo** - The kid protagonists  
- **Ruben** - Fairy godfather
- **Jetplane** - Color-farting dinosaur companion

## License

All rights reserved. Screenplay by Bruno Bornsztein.
