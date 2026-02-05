# Rex Marks the Spot - Production Workflow

## Three Parallel Workstreams

### 1. Production (Making the Movie)
The actual creative work of producing the animated film.

**Tracks that run in parallel:**
- **Character Design** → Turnaround sheets for all 6 characters
- **Sketchy Storyboards** → Scene-by-scene composition/shots

**Merge point:** Clean/final storyboards once both tracks are solid.

### 2. Built in Public (Sharing the Journey)
Documenting and sharing the AI-assisted filmmaking process.

- Website updates showing progress
- Blog posts about the process
- Social media posts (Twitter)
- Behind-the-scenes content
- Making "how we made this" as interesting as the movie itself

### 3. Community (Audience Feedback Loop)
Building an audience and incorporating their input.

- Sharing character designs for feedback
- Polls on creative direction
- Responding to comments/suggestions
- Building audience before the movie is done

---

## Task Types

Use these prefixes in task titles to indicate workflow type:

| Prefix | Purpose | Human Review Required |
|--------|---------|----------------------|
| `[design]` | Establish look, style, or creative direction | **Yes** - approve before proceeding |
| `[generate]` | Create content following approved design | Light review |
| `[iterate]` | Refine existing work based on feedback | **Yes** |
| `[fix]` | Address specific feedback on existing work | **Yes** when done |
| `[qa]` | Validate quality and consistency | Report issues only |
| `[assemble]` | Combine pieces into sequences | **Yes** |
| `[publish]` | Share work publicly (website, social, blog) | **Yes** - decides what to share |
| `[research]` | Investigate tools, techniques, options | Report findings |

**Examples:**
```
[design] Create Mia character turnaround sheet
[generate] Scene 1 sketchy storyboards (panels 1-4)
[fix] Address feedback on Gabe family poses
[publish] Update website with Act 1 storyboards
[qa] Review character consistency across Act 1
```

---

## Key Process Rules

### Smaller Batches
- Generate 1-2 images at a time, not 8
- Human review before proceeding to next batch
- "Style lock-in" before mass generation

### Fixes Stay on Same PR
Don't create new PRs for fixes - push to the existing branch.

### Small Goals First
Get one thing perfect → Document what worked → Use as template for rest.

**Current focus:** Scene 1 + all character turnarounds

---

## Who Does What

### Human Director (Bruno)
- Final creative authority
- Reviews and approves design work
- Decides what to publish/share
- Community engagement decisions
- Quality gate for all creative output

### Assistant Director (Claude on Bruno's machine)
- Coordinates agents and monitors progress
- Escalates decisions to Bruno
- Can approve routine/mechanical tasks
- Keeps things moving

### Remote Agents (TaskYou workers)
- Execute individual tasks
- Report back via PRs and status updates
- Flag blockers and questions
- Follow approved designs/templates

---

## Production Pipeline (In Order)

1. **Script** ✓ (complete)
2. **Pre-production** (current phase)
   - Character designs / turnarounds
   - Sketchy storyboards
   - Style guide lock-in
3. **Production**
   - Clean storyboards
   - 3D models from approved designs
   - Animation
   - Rendering
4. **Post-production**
   - Compositing
   - Sound/music
   - Final edit

---

## Asset Storage

| Content | Where | Why |
|---------|-------|-----|
| Images, video, audio, 3D models | Cloudflare R2 | Large files, fast CDN |
| Code, scripts, config, docs | Git | Version control, collaboration |
| Website/preview | GitHub Pages | Easy deploys from git |

**R2 Public URL:** `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev`

Upload command (from remote server):
```bash
rclone copy <local-path> r2:rex-assets/<r2-path>
```
