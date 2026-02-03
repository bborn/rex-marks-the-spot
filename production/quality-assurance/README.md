# Quality Assurance System

This directory contains the quality assurance framework for "Fairy Dinosaur Date Night" visual assets.

---

## Overview

The QA system ensures consistency and quality across all AI-generated images in the production. It defines:

1. **Standards** for each asset type
2. **A reviewer persona** for PR review
3. **A visual style guide** for reference
4. **Processes** for review and iteration

---

## Documents

| Document | Purpose |
|----------|---------|
| [QA-SYSTEM.md](./QA-SYSTEM.md) | Complete QA standards and processes |
| [QA-REVIEWER-PERSONA.md](./QA-REVIEWER-PERSONA.md) | Reviewer role definition for task queue |
| [VISUAL-STYLE-GUIDE.md](./VISUAL-STYLE-GUIDE.md) | Canonical visual style reference |
| [issues-log.md](./issues-log.md) | Tracking recurring quality issues |

---

## Quick Start

### For Image Creators

1. Before generating, review [VISUAL-STYLE-GUIDE.md](./VISUAL-STYLE-GUIDE.md)
2. Follow prompts in `assets/characters/AI-IMAGE-GENERATION-GUIDE.md`
3. Self-check against standards in [QA-SYSTEM.md](./QA-SYSTEM.md)
4. Submit PR with `needs-qa-review` label

### For QA Reviewers

1. Review against [QA-REVIEWER-PERSONA.md](./QA-REVIEWER-PERSONA.md)
2. Use the review template in that document
3. Provide specific, actionable feedback
4. Log recurring issues in [issues-log.md](./issues-log.md)

### For Directors (Human)

1. Final authority on creative disputes
2. Review escalations from QA Reviewer
3. Update style guide as needed

---

## Integration with TaskYou

The QA Reviewer persona can be used on the remote task queue:

```yaml
# Example task assignment
task: Review PR #123
persona: qa-reviewer
reference: production/quality-assurance/QA-REVIEWER-PERSONA.md
```

---

## Key Standards Summary

### Style
- Pixar/DreamWorks 3D animated aesthetic
- NOT photorealistic, NOT 2D, NOT anime

### Characters
- Must match reference designs
- Identifying features always visible
- Expressions readable at small sizes

### Technical
- Minimum 1024px width
- Correct aspect ratio for asset type
- No obvious artifacts

### Continuity
- Consistent with established canon
- Matches adjacent scenes
- No contradictions

---

## Approval Flow

```
Creator → Self-check → PR (needs-qa-review) → QA Reviewer
                                                   ↓
                            [APPROVED] ←── Pass? ──→ [CHANGES REQUESTED]
                                 ↓                           ↓
                              Merge                    Iterate
```

---

## Style Score Guide

| Score | Meaning | Action |
|-------|---------|--------|
| 5 | Perfect Pixar/DreamWorks match | Approve |
| 4 | Minor deviations | Approve with notes |
| 3 | Noticeable drift | Request changes |
| 2 | Wrong aesthetic | Reject, regenerate |
| 1 | Completely off-brand | Reject immediately |

**Minimum passing score: 4**

---

## Getting Help

- **Style questions:** Review [VISUAL-STYLE-GUIDE.md](./VISUAL-STYLE-GUIDE.md)
- **Process questions:** Review [QA-SYSTEM.md](./QA-SYSTEM.md)
- **Disputes:** Escalate to Director (human)
