# AI-Assisted Creative Direction: Process Documentation

## Overview

This document captures the working relationship between a human creative director, an AI assistant director, and autonomous AI agents during the production of an animated film. The goal is to inform product development for tools that support this workflow.

## The Three-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│                   HUMAN DIRECTOR                        │
│  - Sets creative vision                                 │
│  - Makes final approval decisions                       │
│  - Provides course corrections                          │
│  - Reviews work product                                 │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                AI ASSISTANT DIRECTOR                    │
│  - Manages agent workforce                              │
│  - Reviews agent output for quality                     │
│  - Maintains consistency with source material           │
│  - Creates/prioritizes tasks                            │
│  - Provides critical feedback (not rubber stamps)       │
│  - Bridges human intent to agent execution              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   EXECUTION AGENTS                      │
│  - Generate assets (images, code, content)              │
│  - Work autonomously on defined tasks                   │
│  - Create PRs/deliverables for review                   │
│  - Address feedback and iterate                         │
└─────────────────────────────────────────────────────────┘
```

## Key Principles Discovered

### 1. Real Work vs Pretend Work

**The Problem:** Agents naturally gravitate toward "safe" outputs like documentation, schedules, and plans rather than actual deliverables.

**The Solution:** Task definitions must explicitly demand tangible outputs:
- ❌ "Create a production schedule" (produces markdown)
- ✅ "Generate 10 character pose images as PNG files" (produces assets)

**Guardrail:** If the output is just markdown describing what *should* be done, the task is not complete.

### 2. Critical Review, Not Rubber Stamping

**The Problem:** Initial AI reviews were too positive—approving everything with generic praise like "looks great, ready to merge."

**The Correction:** The assistant director must:
- Compare outputs against source material (screenplay, design docs)
- Flag specific inconsistencies (wrong eye color, missing costume elements)
- Reject work that doesn't meet spec, not just suggest improvements
- Ask "does this match the script?" not "does this look nice?"

**Example of weak review:**
> "Character design looks great. Good emotional range. Ready to merge."

**Example of strong review:**
> "Eye color is amber but script specifies yellow. Wings missing in 4 of 10 poses but script says 'small wings visible.' Outfit is vest+pants but should be coveralls. Action needed before merge."

### 3. Consistency Over Quantity

**The Problem:** Agents generate lots of assets, but they drift from established designs and each other.

**The Solution:**
- Run QA audits before generating more content
- Cross-reference against screenplay/source docs
- Flag when the same character looks different across assets
- Lock down designs before scaling up production

**Workflow:**
1. Generate initial concepts
2. QA audit for consistency
3. Fix inconsistencies
4. THEN scale up production

### 4. Stay On Script (Literally)

**The Problem:** Agents generate "nice to have" assets that aren't actually needed for the story.

**The Solution:**
- Every asset should trace back to a screenplay scene or storyboard panel
- Ask "what scene does this appear in?" for every generated asset
- If it's not in the script, it's probably not needed yet

**Example:** Generating 20 prop variations when only 3 props actually appear in the screenplay.

## The Workflow

### Task Creation
```
Human: "We need character poses for Jetplane"

Assistant Director:
1. Reads screenplay for character description
2. Creates specific task with requirements from script
3. Specifies output format (PNG files, not documentation)
4. Queues task for agent execution
```

### Agent Execution
```
Agent:
1. Receives task with specific requirements
2. Generates assets
3. Creates PR with outputs
4. Provides summary of what was created
```

### Review Cycle
```
Assistant Director:
1. Reviews PR against requirements
2. Compares to source material (screenplay, storyboards)
3. Checks consistency with existing assets
4. Leaves specific, actionable feedback
5. Creates fix tasks if needed

Human Director:
1. Reviews assistant director's assessment
2. Spot-checks actual assets
3. Approves, requests changes, or rejects
```

### Iteration
```
If fixes needed:
1. Assistant director creates specific fix task
2. Agent addresses feedback
3. New PR or updated PR created
4. Review cycle repeats
```

## Infrastructure Requirements

### For Visual Review
- PR previews must render actual images (not just file diffs)
- LFS files need special handling (GitHub doesn't render them)
- Solution: Deploy PR branches to preview URLs (e.g., Cloudflare Pages)
- Simple gallery showing only changed files, not full site deploy

### For Task Management
- Queue system for agent tasks
- Status visibility (queued, running, done, failed)
- Output capture for debugging
- Ability to retry/restart failed tasks

### For Consistency
- Source of truth documents (screenplay, design docs)
- Asset inventory tracking
- Cross-reference reports (what scenes need what assets)
- Style guide enforcement

## Human Director Interventions

The human director intervened to course-correct in these situations:

1. **"This documentation isn't useful"** → Refocus on actual deliverables
2. **"You're approving everything"** → Implement critical review standards
3. **"Stay on script"** → Add QA audits before generating more
4. **"Why can't I see the images?"** → Build preview infrastructure
5. **"Capture this process"** → Meta-documentation for product development

## Metrics That Matter

### Quality Indicators
- Consistency score across character renders
- Script-to-asset coverage percentage
- Rejection rate on first review (too low = rubber stamping)
- Time to address feedback

### Production Indicators
- Assets generated per day
- PRs merged vs rejected
- Task completion rate
- Rework rate (tasks that needed fix PRs)

## Anti-Patterns Identified

1. **The Approval Machine**: Reviewing 10 PRs and approving all 10 without specific feedback
2. **The Doc Generator**: Creating markdown files about work instead of doing work
3. **The Scope Creeper**: Suggesting "nice to have" additions instead of fixing actual issues
4. **The Style Drifter**: Each asset batch looks slightly different from the last
5. **The Quantity Play**: 359 images that no one verified against the screenplay

## Product Implications

A tool supporting this workflow needs:

1. **Source-of-truth integration**: Connect to screenplay/script as the canonical reference
2. **Visual diff for creative assets**: Can't review images as text diffs
3. **Consistency checking**: Automated comparison of new assets vs established designs
4. **Task specificity enforcement**: Require concrete output definitions
5. **Critical review prompts**: Guide reviewers to check specific criteria, not just "looks good"
6. **Coverage tracking**: Map assets to scenes/story requirements
7. **Preview infrastructure**: One-click deploy of PR content for visual review
8. **Feedback-to-task pipeline**: Convert review comments into actionable fix tasks

## Summary

The AI assistant director role is not about being helpful and positive. It's about:
- **Maintaining quality** against defined standards
- **Ensuring consistency** with source material
- **Catching drift** before it compounds
- **Translating** human creative intent into specific agent tasks
- **Filtering** agent output before it reaches human review

The human director sets vision and makes final calls. The assistant director is the quality gate that prevents the human from drowning in mediocre output.
