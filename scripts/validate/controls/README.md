# Identity-validator control set

The validator this guards used to return **1.00 on every character of every
shot**, including a control where the wrong person's turnaround was supplied as
the reference. It cleared all nine v4 Scene 1 panels. Full story:
[`docs/research/identity-validator-repair.md`](../../../docs/research/identity-validator-repair.md).

This directory exists so that cannot happen quietly again.

## Run it

```bash
# unit tests: the arithmetic half. $0.00, no network.
python -m pytest scripts/validate/controls/test_identity_scoring.py -q

# control set: the vision half. ~$0.11, needs GEMINI_API_KEY + rclone + ffmpeg.
python scripts/validate/controls/run_controls.py --fetch
echo $?    # 0 = every case matched its ground truth

# the same cases with identity graded on the whole frame (the pre-346
# behaviour), for a before/after table. ~$0.06.
python scripts/validate/controls/run_controls.py --no-identity-crop
```

`--fetch` pulls ~10 MB of fixtures from R2 into `.validator-controls/`
(gitignored) and extracts the clip mid-frames with ffmpeg. Add `--json <path>`
for a machine-readable result, `--only <ids>` to run a subset.

## Files

| File | What it is |
|---|---|
| `control-set.json` | The thirteen cases, each with **written ground truth** — what a human saw when they looked at the image. |
| `control-manifest.json` | Shot entries the cases validate against, derived from `asset-bible/manifests/scene-01.json`. |
| `run_controls.py` | Fetches fixtures, runs the validator, checks the results against the ground truth. |
| `test_identity_scoring.py` | 34 unit tests over the scorer, the crop geometry, the gate, the aggregation and the shipped identity sheet. |

## The two guards

A control set of nothing but adversarial cases cannot tell a fixed validator
from one that now fails everything, so the harness checks both ends:

- **rubber-stamp guard** — regression if every case returns PASS.
- **clean-pass guard** — regression if *no* case scores every visible character
  at or above the identity gate.

That is why `tp-1B-panel` is in here. It is the load-bearing case; do not remove
it to make the table tidier.

## Adding a case

Look at the images yourself first. `ground_truth` must say what *you saw* — not
what the validator said, and not what you expect it to say. A case whose ground
truth was written from a validator's output tests nothing.

Then set the expectation you actually want pinned:

- `expect_identity_below` / `expect_identity_at_or_above` — per character. Prefer
  these; they say what the case is really about.
- `expect_overall` — `"PASS"`, `"FAIL"`, or `null` for "not asserted". Use
  `null` when the case is about identity and the shot's other rubrics (artifacts,
  presence) would otherwise hold the assertion hostage.
- `expect_frame_attribute` — per character, what the validator must have READ
  off the frame (`{"Gabe": {"eyewear": "thin_wire_rectangular"}}`). Use it when
  the case is about a specific attribute: a score can come out right for the
  wrong reason, an attribute cannot.
- `kind: "known-weakness"` — a characterization test. Pins behaviour we are not
  happy with, so a change in either direction is noticed. Not a place to file
  failures you would rather not fix; each one is written up in the repair note.

## The scale pair (task 346)

`scale-1A-a1-gabe-small-correct` and `scale-veo3-v1-gabe-small-wrong` are a
matched pair and only mean anything together. Both are Gabe at a head height of
a fourteenth of the frame or less. In the first he is right and must pass; in
the second he is genuinely the wrong man and must fail. Identity is graded on a
per-character crop (`docs/research/identity-validator-scale-fix.md`) — the
first case proves that stopped over-calling small faces, the second proves it
was not bought by making small faces easier to pass. Removing either one leaves
the other unable to tell a fix from a softening.
