# QA Issues Log

This document tracks recurring quality issues for process improvement.

---

## Active Issues

### Style Drift to Photorealism

**First Observed:** 2025-02-02
**Frequency:** Common
**Severity:** High

**Symptoms:**
- Police car chase scenes look like movie stills
- Environments losing animated quality
- Characters appearing too realistic

**Root Cause:**
- Default AI model behavior trends toward photorealism
- Style prefixes being omitted from prompts
- Using models not optimized for animation style

**Solution:**
1. ALWAYS include style prefix in prompts:
   ```
   Pixar-style 3D animated film, DreamWorks quality animation
   ```
2. ALWAYS include style negative:
   ```
   --no realistic, photorealistic, photograph
   ```
3. Consider using animation-specific models or fine-tunes

**Status:** Ongoing - requires vigilance

---

### Character Inconsistency Across Panels

**First Observed:** 2025-02-02
**Frequency:** Common
**Severity:** High

**Symptoms:**
- Same character looks different in adjacent panels
- Key identifying features missing (scrunchie, glasses, etc.)
- Proportions vary significantly

**Root Cause:**
- Not using reference images in prompts
- Prompts too vague about character features
- Different generation tools used without calibration

**Solution:**
1. Include character reference images when available
2. Be extremely specific about identifying features
3. Standardize on one generation tool per character batch
4. Generate batches rather than one-offs

**Status:** Ongoing - need to establish reference image pipeline

---

### Lighting Style Variance

**First Observed:** 2025-02-02
**Frequency:** Moderate
**Severity:** Medium

**Symptoms:**
- Some scenes have harsh, dramatic lighting
- Other scenes have flat, diffuse lighting
- Inconsistent shadow softness

**Root Cause:**
- Not specifying lighting in prompts
- Different scenes generated with different tools
- Mood-appropriate lighting conflicting with overall style

**Solution:**
1. Include lighting keywords: "soft lighting, warm bounced light"
2. Match lighting to reference films (Coco, Luca)
3. Even "scary" scenes maintain family-friendly lighting

**Status:** Active

---

## Resolved Issues

*No resolved issues yet - log here when issues are successfully addressed.*

---

## Issue Template

Copy this template when logging new issues:

```markdown
### [Issue Title]

**First Observed:** [Date]
**Frequency:** [Rare / Occasional / Common]
**Severity:** [Low / Medium / High / Critical]

**Symptoms:**
- [What you see]
- [What you see]

**Root Cause:**
- [Why it happens]

**Solution:**
1. [Step to prevent]
2. [Step to prevent]

**Status:** [Active / Resolved / Monitoring]
```

---

## Issue Statistics

| Issue Type | Count | Most Common |
|------------|-------|-------------|
| Style drift | 1 | Photorealism |
| Character inconsistency | 1 | Missing features |
| Lighting variance | 1 | Harsh shadows |
| **Total Active** | **3** | |

---

## Review Frequency

- **Weekly:** Review new issues added this week
- **Monthly:** Analyze patterns, update QA-SYSTEM.md if needed
- **Per-release:** Clear resolved issues, archive to history
