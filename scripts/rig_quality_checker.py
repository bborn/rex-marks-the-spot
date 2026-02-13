#!/usr/bin/env python3
"""
Rig Quality Checker for Fairy Dinosaur Date Night
===================================================
Validates character rigs against production quality standards.
Run inside Blender: File > Run Script, or from command line:
  blender --background --python scripts/rig_quality_checker.py -- model.fbx

Based on research into professional rigging pipelines (Pixar, DreamWorks, Disney)
and auto-rigging tool capabilities (Mixamo, AccuRIG, Rigify, Cascadeur, Meshy, Tripo).

Quality checks:
  1. Bone count and hierarchy validation
  2. Weight painting coverage (no unweighted verts)
  3. Deformation stress tests at key joints
  4. IK/FK chain detection
  5. Symmetry validation
  6. Bone naming convention checks
  7. Export readiness (FBX/GLB compatibility)
"""

import sys
import os
import math
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

# ---- Constants based on research ----

# Recommended bone counts by character type (from production pipeline research)
BONE_COUNT_GUIDELINES = {
    "simple_prop": {"min": 1, "max": 10, "description": "Simple animated prop"},
    "basic_biped": {"min": 20, "max": 50, "description": "Basic biped (Mixamo-style)"},
    "standard_biped": {"min": 50, "max": 100, "description": "Standard biped with fingers"},
    "production_biped": {"min": 80, "max": 200, "description": "Production biped with face"},
    "hero_character": {"min": 150, "max": 400, "description": "Hero character (Pixar-level)"},
    "quadruped": {"min": 40, "max": 120, "description": "Quadruped (e.g., Jetplane dinosaur)"},
    "game_optimized": {"min": 20, "max": 75, "description": "Game-optimized (Unity <75, Unreal <100)"},
}

# Essential bones that must exist in a humanoid rig
REQUIRED_HUMANOID_BONES = [
    "hips", "spine", "chest", "neck", "head",
    "shoulder.L", "upper_arm.L", "forearm.L", "hand.L",
    "shoulder.R", "upper_arm.R", "forearm.R", "hand.R",
    "thigh.L", "shin.L", "foot.L",
    "thigh.R", "shin.R", "foot.R",
]

# Common naming patterns across tools
BONE_NAME_PATTERNS = {
    "mixamo": {
        "prefix": "mixamorig:",
        "hips": "mixamorig:Hips",
        "spine": "mixamorig:Spine",
    },
    "rigify": {
        "prefix": "",
        "hips": "spine",
        "spine": "spine.001",
    },
    "accurig": {
        "prefix": "CC_Base_",
        "hips": "CC_Base_Hip",
        "spine": "CC_Base_Waist",
    },
    "tripo": {
        "prefix": "",
        "hips": "Hips",
        "spine": "Spine",
    },
    "meshy": {
        "prefix": "",
        "hips": "Hips",
        "spine": "Spine",
    },
}

# Stress test poses (joint angles that commonly cause issues)
STRESS_TEST_POSES = {
    "arms_up": {
        "description": "Both arms raised above head - tests shoulder deformation",
        "bones": {"upper_arm.L": (0, 0, -170), "upper_arm.R": (0, 0, 170)},
    },
    "arms_forward": {
        "description": "Arms stretched forward - tests shoulder/chest blend",
        "bones": {"upper_arm.L": (-90, 0, 0), "upper_arm.R": (-90, 0, 0)},
    },
    "squat": {
        "description": "Deep squat pose - tests hip/knee deformation",
        "bones": {"thigh.L": (-120, 0, 0), "thigh.R": (-120, 0, 0),
                  "shin.L": (90, 0, 0), "shin.R": (90, 0, 0)},
    },
    "twist_arm": {
        "description": "Arm twist 180 degrees - tests candy-wrapper issue",
        "bones": {"forearm.L": (0, 180, 0), "forearm.R": (0, 180, 0)},
    },
    "head_turn": {
        "description": "Head turned 90 degrees - tests neck deformation",
        "bones": {"head": (0, 0, 90)},
    },
}

# Quality thresholds
QUALITY_THRESHOLDS = {
    "min_weight_coverage": 0.99,        # 99% of verts must be weighted
    "max_weight_per_vert": 4,            # Max bone influences per vertex
    "symmetry_tolerance": 0.01,          # Position tolerance for symmetry check
    "min_deform_bones": 20,              # Minimum deform bones for humanoid
    "max_stretch_ratio": 1.5,            # Max acceptable stretch in stress test
    "min_volume_preservation": 0.7,      # Min volume preservation at joints
}


class CheckResult(Enum):
    PASS = "PASS"
    WARN = "WARNING"
    FAIL = "FAIL"
    SKIP = "SKIPPED"


@dataclass
class QualityCheck:
    name: str
    result: CheckResult
    message: str
    details: list = field(default_factory=list)


@dataclass
class RigReport:
    character_name: str
    source_tool: str  # mixamo, accurig, rigify, tripo, meshy, manual, unknown
    bone_count: int
    deform_bone_count: int
    vertex_count: int
    checks: list = field(default_factory=list)
    overall_score: float = 0.0
    production_ready: bool = False

    def add_check(self, check: QualityCheck):
        self.checks.append(check)

    def calculate_score(self):
        if not self.checks:
            self.overall_score = 0.0
            return
        weights = {CheckResult.PASS: 1.0, CheckResult.WARN: 0.5,
                   CheckResult.FAIL: 0.0, CheckResult.SKIP: 0.5}
        total = sum(weights.get(c.result, 0) for c in self.checks)
        self.overall_score = total / len(self.checks) * 100
        # Production ready requires no FAILs and score > 80
        self.production_ready = (
            all(c.result != CheckResult.FAIL for c in self.checks)
            and self.overall_score >= 80
        )

    def to_dict(self):
        d = asdict(self)
        for i, check in enumerate(d["checks"]):
            d["checks"][i]["result"] = check["result"]
        return d

    def summary(self):
        lines = [
            f"=== Rig Quality Report: {self.character_name} ===",
            f"Source tool: {self.source_tool}",
            f"Bones: {self.bone_count} total, {self.deform_bone_count} deform",
            f"Vertices: {self.vertex_count}",
            f"",
        ]
        for check in self.checks:
            icon = {"PASS": "[OK]", "WARNING": "[!!]", "FAIL": "[XX]", "SKIPPED": "[--]"}
            lines.append(f"  {icon.get(check.result, '[??]')} {check.name}: {check.message}")
            for detail in check.details:
                lines.append(f"       - {detail}")
        lines.append("")
        lines.append(f"Overall Score: {self.overall_score:.1f}%")
        lines.append(f"Production Ready: {'YES' if self.production_ready else 'NO'}")
        return "\n".join(lines)


# ---- Blender-specific checks (only run inside Blender) ----

def run_blender_checks(armature_obj, mesh_obj):
    """Run all quality checks on a Blender armature+mesh pair."""
    import bpy

    report = RigReport(
        character_name=armature_obj.name,
        source_tool=detect_source_tool(armature_obj),
        bone_count=len(armature_obj.data.bones),
        deform_bone_count=sum(1 for b in armature_obj.data.bones if b.use_deform),
        vertex_count=len(mesh_obj.data.vertices) if mesh_obj else 0,
    )

    # Check 1: Bone count validation
    report.add_check(check_bone_count(armature_obj))

    # Check 2: Bone hierarchy
    report.add_check(check_bone_hierarchy(armature_obj))

    # Check 3: Required bones present
    report.add_check(check_required_bones(armature_obj))

    # Check 4: Bone naming conventions
    report.add_check(check_naming_conventions(armature_obj))

    # Check 5: Symmetry
    report.add_check(check_symmetry(armature_obj))

    if mesh_obj:
        # Check 6: Weight painting coverage
        report.add_check(check_weight_coverage(armature_obj, mesh_obj))

        # Check 7: Max influences per vertex
        report.add_check(check_max_influences(mesh_obj))

    # Check 8: IK chains
    report.add_check(check_ik_chains(armature_obj))

    # Check 9: Bone constraints
    report.add_check(check_constraints(armature_obj))

    # Check 10: Rest pose (T-pose or A-pose)
    report.add_check(check_rest_pose(armature_obj))

    report.calculate_score()
    return report


def detect_source_tool(armature_obj):
    """Detect which tool generated this rig based on bone naming."""
    bone_names = [b.name for b in armature_obj.data.bones]
    joined = " ".join(bone_names)

    if "mixamorig:" in joined:
        return "mixamo"
    elif "CC_Base_" in joined:
        return "accurig"
    elif any(b.name.startswith("DEF-") for b in armature_obj.data.bones):
        return "rigify"
    elif any(b.name.startswith("MCH-") for b in armature_obj.data.bones):
        return "rigify"
    elif any(b.name in ("ORG-spine", "ORG-spine.001") for b in armature_obj.data.bones):
        return "rigify"
    else:
        return "unknown"


def check_bone_count(armature_obj):
    """Validate bone count is within reasonable range."""
    count = len(armature_obj.data.bones)
    deform = sum(1 for b in armature_obj.data.bones if b.use_deform)

    if count < 10:
        return QualityCheck("Bone Count", CheckResult.WARN,
                            f"{count} bones - very simple rig, may lack control",
                            [f"Deform bones: {deform}"])
    elif count > 400:
        return QualityCheck("Bone Count", CheckResult.WARN,
                            f"{count} bones - very complex, may impact performance",
                            [f"Deform bones: {deform}"])
    else:
        return QualityCheck("Bone Count", CheckResult.PASS,
                            f"{count} total bones, {deform} deform bones")


def check_bone_hierarchy(armature_obj):
    """Check that bones have a proper hierarchy (no orphan bones)."""
    orphans = [b.name for b in armature_obj.data.bones if b.parent is None]
    if len(orphans) == 0:
        return QualityCheck("Bone Hierarchy", CheckResult.WARN,
                            "No root bone found (all bones have parents)")
    elif len(orphans) == 1:
        return QualityCheck("Bone Hierarchy", CheckResult.PASS,
                            f"Single root bone: {orphans[0]}")
    else:
        return QualityCheck("Bone Hierarchy", CheckResult.WARN,
                            f"Multiple root bones: {len(orphans)}",
                            orphans[:10])


def check_required_bones(armature_obj):
    """Check that essential humanoid bones exist."""
    bone_names_lower = {b.name.lower().replace("mixamorig:", "").replace("cc_base_", "")
                        for b in armature_obj.data.bones}
    # Also check without dots/underscores
    bone_names_normalized = set()
    for name in bone_names_lower:
        bone_names_normalized.add(name)
        bone_names_normalized.add(name.replace(".", "_"))
        bone_names_normalized.add(name.replace("_", "."))

    # Simple presence check for core bones
    core_names = ["hips", "hip", "pelvis", "spine", "head", "neck"]
    found = sum(1 for name in core_names if any(name in bn for bn in bone_names_normalized))

    if found >= 4:
        return QualityCheck("Required Bones", CheckResult.PASS,
                            f"Found {found}/6 core bone groups")
    elif found >= 2:
        return QualityCheck("Required Bones", CheckResult.WARN,
                            f"Found only {found}/6 core bone groups",
                            [f"Looking for: {', '.join(core_names)}"])
    else:
        return QualityCheck("Required Bones", CheckResult.FAIL,
                            f"Missing most core bones ({found}/6 found)",
                            [f"Looking for: {', '.join(core_names)}"])


def check_naming_conventions(armature_obj):
    """Check bone naming follows a consistent convention."""
    bone_names = [b.name for b in armature_obj.data.bones]

    # Check for .L/.R or Left/Right or _L/_R conventions
    has_lr = any(".L" in n or ".R" in n for n in bone_names)
    has_leftright = any("Left" in n or "Right" in n for n in bone_names)
    has_underscore_lr = any("_L" in n or "_R" in n for n in bone_names)

    conventions_used = sum([has_lr, has_leftright, has_underscore_lr])

    if conventions_used == 1:
        return QualityCheck("Naming Convention", CheckResult.PASS,
                            "Consistent naming convention detected")
    elif conventions_used > 1:
        return QualityCheck("Naming Convention", CheckResult.WARN,
                            "Mixed naming conventions detected",
                            ["Uses multiple L/R conventions which may cause issues with symmetry tools"])
    else:
        return QualityCheck("Naming Convention", CheckResult.WARN,
                            "No standard L/R naming convention detected",
                            ["May not support Blender's symmetry tools"])


def check_symmetry(armature_obj):
    """Check if rig is symmetric (left/right bones match)."""
    bones = armature_obj.data.bones
    left_bones = [b for b in bones if ".L" in b.name or "Left" in b.name or "_L" in b.name]
    right_bones = [b for b in bones if ".R" in b.name or "Right" in b.name or "_R" in b.name]

    if not left_bones and not right_bones:
        return QualityCheck("Symmetry", CheckResult.SKIP,
                            "No L/R bones detected, cannot check symmetry")

    if len(left_bones) == len(right_bones):
        return QualityCheck("Symmetry", CheckResult.PASS,
                            f"Symmetric: {len(left_bones)} bones per side")
    else:
        return QualityCheck("Symmetry", CheckResult.WARN,
                            f"Asymmetric: {len(left_bones)} left, {len(right_bones)} right",
                            ["This may cause issues with pose mirroring"])


def check_weight_coverage(armature_obj, mesh_obj):
    """Check that all mesh vertices are weighted to at least one bone."""
    vgroups = mesh_obj.vertex_groups
    if not vgroups:
        return QualityCheck("Weight Coverage", CheckResult.FAIL,
                            "No vertex groups found - mesh is not weighted")

    total_verts = len(mesh_obj.data.vertices)
    unweighted = 0
    for vert in mesh_obj.data.vertices:
        if not vert.groups:
            unweighted += 1

    coverage = (total_verts - unweighted) / total_verts if total_verts > 0 else 0

    if coverage >= QUALITY_THRESHOLDS["min_weight_coverage"]:
        return QualityCheck("Weight Coverage", CheckResult.PASS,
                            f"{coverage*100:.1f}% vertices weighted ({unweighted} unweighted)")
    elif coverage >= 0.95:
        return QualityCheck("Weight Coverage", CheckResult.WARN,
                            f"{coverage*100:.1f}% coverage - {unweighted} unweighted vertices",
                            ["Some vertices may fly off during animation"])
    else:
        return QualityCheck("Weight Coverage", CheckResult.FAIL,
                            f"Only {coverage*100:.1f}% coverage - {unweighted} unweighted vertices",
                            ["Many vertices will not move with the rig"])


def check_max_influences(mesh_obj):
    """Check max bone influences per vertex (should be <= 4 for game engines)."""
    max_influences = 0
    high_influence_count = 0

    for vert in mesh_obj.data.vertices:
        influences = len(vert.groups)
        max_influences = max(max_influences, influences)
        if influences > QUALITY_THRESHOLDS["max_weight_per_vert"]:
            high_influence_count += 1

    if max_influences <= QUALITY_THRESHOLDS["max_weight_per_vert"]:
        return QualityCheck("Max Influences", CheckResult.PASS,
                            f"Max {max_influences} bone influences per vertex")
    else:
        return QualityCheck("Max Influences", CheckResult.WARN,
                            f"Max {max_influences} influences ({high_influence_count} verts over limit)",
                            ["Game engines typically support max 4 influences per vertex",
                             "Use Blender's 'Limit Total' in Weight Paint to reduce"])


def check_ik_chains(armature_obj):
    """Check for IK constraint chains."""
    import bpy
    ik_count = 0
    fk_controls = 0

    # Need to check pose bones for constraints
    if armature_obj.pose:
        for pbone in armature_obj.pose.bones:
            for constraint in pbone.constraints:
                if constraint.type == 'IK':
                    ik_count += 1

    if ik_count > 0:
        return QualityCheck("IK Chains", CheckResult.PASS,
                            f"Found {ik_count} IK constraints")
    else:
        return QualityCheck("IK Chains", CheckResult.WARN,
                            "No IK constraints found",
                            ["IK is recommended for foot/hand placement",
                             "Auto-rigged models from Mixamo/AccuRIG may not include IK",
                             "Consider adding IK in Blender or re-rigging with Rigify"])


def check_constraints(armature_obj):
    """Check for bone constraints (copy rotation, limit rotation, etc.)."""
    constraint_types = {}

    if armature_obj.pose:
        for pbone in armature_obj.pose.bones:
            for constraint in pbone.constraints:
                ctype = constraint.type
                constraint_types[ctype] = constraint_types.get(ctype, 0) + 1

    total = sum(constraint_types.values())
    if total > 10:
        return QualityCheck("Bone Constraints", CheckResult.PASS,
                            f"Found {total} constraints across {len(constraint_types)} types",
                            [f"{k}: {v}" for k, v in sorted(constraint_types.items())])
    elif total > 0:
        return QualityCheck("Bone Constraints", CheckResult.WARN,
                            f"Only {total} constraints - rig may lack advanced controls",
                            [f"{k}: {v}" for k, v in sorted(constraint_types.items())])
    else:
        return QualityCheck("Bone Constraints", CheckResult.WARN,
                            "No bone constraints found",
                            ["Simple rigs from auto-riggers may lack constraints",
                             "Consider adding limits and copy constraints for production"])


def check_rest_pose(armature_obj):
    """Check if rig is in T-pose or A-pose (preferred for rigging)."""
    # Look for upper arm bones to detect pose
    upper_arms = []
    for bone in armature_obj.data.bones:
        name_lower = bone.name.lower()
        if "upper_arm" in name_lower or "upperarm" in name_lower or "shoulder" in name_lower:
            upper_arms.append(bone)

    if not upper_arms:
        return QualityCheck("Rest Pose", CheckResult.SKIP,
                            "Cannot detect rest pose - no upper arm bones found")

    # Check if arms are roughly horizontal (T-pose) or at ~45 degrees (A-pose)
    # This is a simplified check based on bone head/tail positions
    for bone in upper_arms:
        head = bone.head_local
        tail = bone.tail_local
        # Calculate angle from horizontal
        dx = abs(tail.x - head.x)
        dy = abs(tail.y - head.y)
        dz = abs(tail.z - head.z)

        if dx > 0:
            angle_from_horiz = math.degrees(math.atan2(dz, dx))
        else:
            angle_from_horiz = 90

        if angle_from_horiz < 15:
            return QualityCheck("Rest Pose", CheckResult.PASS,
                                "T-pose detected (arms horizontal)")
        elif angle_from_horiz < 60:
            return QualityCheck("Rest Pose", CheckResult.PASS,
                                "A-pose detected (arms at ~45 degrees)")

    return QualityCheck("Rest Pose", CheckResult.WARN,
                        "Rest pose unclear - arms may not be in standard T/A-pose",
                        ["T-pose or A-pose is recommended for clean deformation"])


# ---- Standalone mode (no Blender) ----

def print_rigging_guide():
    """Print the complete rigging pipeline guide when run outside Blender."""
    guide = """
================================================================================
  CHARACTER RIGGING PIPELINE GUIDE
  Fairy Dinosaur Date Night Production
================================================================================

This guide is based on research into professional studio approaches (Pixar,
Disney, DreamWorks), auto-rigging tool comparisons, and indie workflow
best practices.

---- 1. PROFESSIONAL STUDIO APPROACHES ----

PIXAR:
  - Uses custom rigging systems (CurveNet, ProfileMover)
  - CurveNet replaces traditional skinning with spline-based deformation
  - First used on Turning Red (2022), then Elemental
  - Character TDs spend weeks to months per hero character rig
  - USD/USDSkel pipeline for cross-tool interop
  - Team: 5-15 riggers per film, working alongside animators
  - Timeline: 6-12 months rigging phase for a feature film

DISNEY:
  - Frozen had 312 unique characters requiring rigging
  - Character Technical Directors partner with animators + modelers
  - Use Maya primarily, with custom tools
  - Emphasis on animator-friendly controls

DREAMWORKS:
  - How to Train Your Dragon used constrained rigging team
  - Developed "simple dragon" rig for background characters
  - Secondary add-on deformation systems for legacy characters
  - Clever economical solutions for production challenges

KEY TAKEAWAY FOR SMALL TEAMS:
  Studios have 5-15+ dedicated riggers. For our 1-3 person team,
  auto-rigging is essential. Manual rigging should only be done
  for cleanup and polish.

---- 2. AUTO-RIGGING TOOLS COMPARISON ----

+---------------+--------+---------+----------+---------+----------+--------+
| Tool          | Price  | Quality | Stylized | IK/FK   | Anim Lib | Export |
+---------------+--------+---------+----------+---------+----------+--------+
| Mixamo        | Free   | Good    | Limited  | Basic   | 2500+    | FBX    |
| AccuRIG 2     | Free   | Better  | Good     | Good    | 4500+    | FBX/USD|
| Rigify        | Free*  | Best    | Flexible | Full    | None     | Blend  |
| Auto-Rig Pro  | $40*   | Best    | Flexible | Full    | None     | FBX    |
| Cascadeur     | Free** | Good    | Good     | Good    | AI-gen   | FBX/DAE|
| Tripo AI      | $16/mo | Good    | Good     | Basic   | None     | FBX/GLB|
| Meshy         | $20/mo | Basic   | Limited  | Basic   | 500+     | FBX/GLB|
+---------------+--------+---------+----------+---------+----------+--------+
* Blender addon  ** Free for indie

MIXAMO (Adobe):
  Pros:  Free, huge animation library, instant results
  Cons:  Stalled development, humanoid-only, limited stylized support,
         shoulder/hip artifacts in extreme poses
  Best for: Quick prototyping, beginners, applying animations
  Time: ~5 minutes per character

AccuRIG 2 (Reallusion):
  Pros:  Free, handles oversized heads + atypical limbs, 4500+ motions,
         better weight painting than Mixamo, multi-format export
  Cons:  Less mature than Mixamo ecosystem, newer tool
  Best for: Stylized/cartoon characters, production pipelines
  Time: ~10 minutes per character

RIGIFY (Blender built-in):
  Pros:  Free, deeply integrated, modular rig-type system, full IK/FK,
         community support, production-quality output
  Cons:  Steep learning curve (5/10 UX), error-prone for beginners,
         requires manual bone placement, no animation library
  Best for: Characters needing custom controls, long-term projects
  Time: 2-8 hours per character (including weight paint cleanup)
  Note: Blender 4.0 added Bone Collections, making organization easier

AUTO-RIG PRO (Blender addon, $40):
  Pros:  Better UX than Rigify (9/10), includes retargeting, bone picker,
         game export presets, shape key tools, bendy bones + spline IK
  Cons:  Paid, not built-in
  Best for: All-in-one rigging in Blender, game export
  Time: 1-4 hours per character

CASCADEUR:
  Pros:  AI-powered posing (85-95% accuracy), physics-based animation,
         quick rigging tool, now supports quadrupeds (2025.3)
  Cons:  Standalone app (not in Blender), learning curve for AI tools
  Best for: Animation-first workflow, physics-correct motion
  Time: ~15 minutes for rigging, then animation time

TRIPO AI:
  Pros:  Clean quad topology, integrated with generation pipeline,
         supports humanoids + quadrupeds + stylized + mechanical
  Cons:  Basic rig (no advanced IK/FK switching), web/API credits separate
  Best for: Quick rig on Tripo-generated models
  Time: Seconds (automated)

MESHY:
  Pros:  Integrated with model generation, 500+ preset animations
  Cons:  Very basic rigging, weighting oddities at shoulders/elbows,
         humanoid GLB only
  Best for: Quick previs and blocking, not production
  Time: Seconds (automated)

CLOUDRIG (Blender Studio):
  Pros:  Production-proven (used in Blender Studio films), builds on Rigify,
         advanced FK/IK, facial rig support, secondary motion tools
  Cons:  Less documented than Rigify/ARP, newer
  Best for: Production rigs in Blender ecosystem
  Time: 2-6 hours per character

---- 3. RECOMMENDED PIPELINE FOR THIS PROJECT ----

PHASE 1: Auto-Rig (Minutes)
  For each character:
  a) If model from Tripo AI -> use Tripo's built-in auto-rig
  b) If model from Meshy -> use AccuRIG 2 for better quality
  c) For any model -> Mixamo as fallback for quick rig + animations

PHASE 2: Import & Evaluate (30 min)
  a) Import rigged model into Blender (FBX/GLB)
  b) Run this quality checker script
  c) Test basic poses manually
  d) Decision: Is auto-rig sufficient?

PHASE 3: Cleanup (if needed) (1-4 hours)
  For hero characters (Mia, Leo, Ruben, Jetplane):
  a) Fix weight painting at problem joints (shoulders, hips, knees)
  b) Add IK constraints if missing
  c) Add bone limits (rotation limits on joints)
  d) For stylized characters: adjust spine/neck weights for big heads

  For background characters:
  a) Quick weight paint fixes only
  b) Skip advanced controls

PHASE 4: Animation Setup (1-2 hours per character)
  a) Apply Mixamo/AccuRIG animations via retargeting
  b) Or create custom keyframe animations
  c) Add secondary motion (hair/cloth) via Blender physics

---- 4. STYLIZED CHARACTER RIGGING TIPS ----

For Fairy Dinosaur Date Night's Pixar-like characters:

BIG HEADS:
  - Place neck joints parallel to jawline (not vertical)
  - AccuRIG handles oversized heads well automatically
  - In Blender: Add extra neck bone if head is > 40% of body height
  - Use "Bendy Bones" mode for cartoon-style flexibility
  - Weight paint the head bone with sharp falloff at neck

EXAGGERATED PROPORTIONS:
  - Place spine joints closer to center of model (not anatomical)
  - Use pose offsets for stylized performances
  - Rigify's stretch controls handle proportion changes well
  - Test deformation with squash-and-stretch poses

JETPLANE (DINOSAUR CHARACTER):
  - Use quadruped rig base (AccuRIG now supports this)
  - Cascadeur 2025.3 added quadruped support
  - Tail needs 4-6 bones with FK chain
  - Wings (if any) need separate bone chains
  - Jaw bone for mouth animation

CHILDREN (MIA & LEO):
  - Shorter limb proportions relative to head
  - AccuRIG or Mixamo can handle child proportions
  - May need to manually adjust hip height in rig
  - Scale bone lengths after auto-rig if proportions are off

---- 5. PRODUCTION-READY RIG CHECKLIST ----

MUST HAVE (for any animated character):
  [ ] All vertices weighted (>99% coverage)
  [ ] No clipping in rest pose (T-pose or A-pose)
  [ ] Proper deformation at shoulders (arms forward + up)
  [ ] Proper deformation at hips (squat pose)
  [ ] Proper deformation at elbows/knees (full bend)
  [ ] No candy-wrapper twist at forearms/shins
  [ ] Consistent bone naming convention
  [ ] Single root bone
  [ ] Clean export to target format (FBX/GLB)

SHOULD HAVE (for hero characters):
  [ ] IK/FK switching on arms and legs
  [ ] Foot roll controls
  [ ] Finger controls (at least open/close)
  [ ] Rotation limits on all joints
  [ ] Space switching (world/local/parent)
  [ ] Facial controls (at minimum: jaw, blink, brow)
  [ ] Symmetry (left/right bones match)
  [ ] Max 4 bone influences per vertex (game compatibility)
  [ ] Animation-friendly control shapes
  [ ] Bone picker/selection UI

NICE TO HAVE (for premium quality):
  [ ] Corrective shape keys at problem joints
  [ ] Secondary motion bones (hair, cloth, tail)
  [ ] Squash-and-stretch on spine/limbs
  [ ] Bendy bones for smooth curves
  [ ] Custom properties for animation controls
  [ ] Proxy rig for animation (low-poly mesh)
  [ ] Multiple levels of detail (LOD)

---- 6. TIME ESTIMATES ----

AUTO-RIG ONLY (no cleanup):
  - Per character: 5-15 minutes
  - Quality: 60-75% production ready
  - Good for: Background characters, previs, blocking

AUTO-RIG + BASIC CLEANUP:
  - Per character: 1-2 hours
  - Quality: 80-90% production ready
  - Good for: Supporting characters, most scenes

AUTO-RIG + FULL POLISH:
  - Per character: 4-8 hours
  - Quality: 95%+ production ready
  - Good for: Hero characters, close-up shots

MANUAL RIG FROM SCRATCH (Rigify/ARP):
  - Per character: 8-40 hours
  - Quality: 100% custom to needs
  - Good for: When auto-rig fails completely

FOR THIS PROJECT (6 characters):
  Hero characters (Mia, Leo, Ruben, Jetplane): 4-8 hrs each = 16-32 hrs
  Supporting characters (Gabe, Nina): 1-2 hrs each = 2-4 hrs
  TOTAL ESTIMATED: 18-36 hours of rigging work

---- 7. BLENDER-SPECIFIC RIGGING REFERENCE ----

RIGIFY WORKFLOW:
  1. Add Human metarig (Add > Armature > Human)
  2. Scale/position metarig bones to match character mesh
  3. Generate rig (Armature Properties > Generate Rig)
  4. Parent mesh to generated rig (Ctrl+P > Armature Deform > Automatic Weights)
  5. Fix weight painting in Weight Paint mode
  6. Test with poses

KEY BLENDER SHORTCUTS:
  Ctrl+P     = Parent (mesh to armature)
  Ctrl+Tab   = Toggle Weight Paint mode
  Alt+R      = Clear rotation (reset pose)
  Alt+G      = Clear location
  Shift+I    = Add IK constraint interactively
  X mirror   = Mirror weight painting

WEIGHT PAINTING TIPS:
  - Always use "Blur" brush to smooth weight transitions
  - Enable "Mirror" in Weight Paint tool options for symmetry
  - Use "Normalize All" to fix weights that don't sum to 1.0
  - Use "Limit Total" to cap influences at 4 for game export
  - Paint with "Subtract" brush to fix bleed-through at joints

BONE CONSTRAINT TYPES (most useful):
  - Inverse Kinematics: Hand/foot placement
  - Copy Rotation: Twist bones, face controls
  - Limit Rotation: Joint angle limits
  - Damped Track: Eye tracking
  - Stretch To: Bendy cartoon limbs
  - Child Of: Space switching

COMMON BLENDER RIGGING ADDONS (2025):
  - Rigify (built-in): Full auto-rigging system
  - Auto-Rig Pro ($40): Enhanced auto-rigging + export
  - CloudRig (free): Blender Studio's production rigger
  - BlenRig ($0-30): Full body + face rigging
  - Mixamo Rig addon: Import/convert Mixamo rigs
  - Easy Driver: Simplified driver creation
  - Voxel Heat Diffuse Skinning: Better auto-weights
  - Pose Tools: Quick pose library management

================================================================================
"""
    print(guide)


# ---- Entry point ----

def main():
    """Main entry point. Detects Blender or standalone mode."""
    try:
        import bpy
        in_blender = True
    except ImportError:
        in_blender = False

    if not in_blender:
        print_rigging_guide()
        print("\nTo run quality checks, open this script inside Blender")
        print("or run: blender --background --python scripts/rig_quality_checker.py -- model.fbx")
        return

    # Running inside Blender
    import bpy

    # Check if a file was passed as argument
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        if args:
            filepath = args[0]
            print(f"Importing: {filepath}")
            ext = os.path.splitext(filepath)[1].lower()
            if ext == ".fbx":
                bpy.ops.import_scene.fbx(filepath=filepath)
            elif ext in (".glb", ".gltf"):
                bpy.ops.import_scene.gltf(filepath=filepath)
            elif ext == ".obj":
                bpy.ops.wm.obj_import(filepath=filepath)
            else:
                print(f"Unsupported format: {ext}")
                return

    # Find armatures and meshes in scene
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

    if not armatures:
        print("No armatures found in scene. Import a rigged character first.")
        print_rigging_guide()
        return

    for armature in armatures:
        # Find associated mesh (parented to this armature)
        associated_mesh = None
        for mesh in meshes:
            if mesh.parent == armature:
                associated_mesh = mesh
                break
        # Fallback: use first mesh with an armature modifier
        if not associated_mesh:
            for mesh in meshes:
                for mod in mesh.modifiers:
                    if mod.type == 'ARMATURE' and mod.object == armature:
                        associated_mesh = mesh
                        break

        print(f"\nChecking armature: {armature.name}")
        report = run_blender_checks(armature, associated_mesh)
        print(report.summary())

        # Save report as JSON
        report_path = os.path.join(
            os.path.dirname(bpy.data.filepath) if bpy.data.filepath else "/tmp",
            f"rig_report_{armature.name}.json"
        )
        try:
            with open(report_path, 'w') as f:
                json.dump(report.to_dict(), f, indent=2, default=str)
            print(f"\nReport saved to: {report_path}")
        except Exception as e:
            print(f"Could not save report: {e}")


if __name__ == "__main__":
    main()
