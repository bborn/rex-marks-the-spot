# Shot 1A pipeline run - HALTED on mitte auth

**Generated:** 2026-05-22
**Task:** #328 - Render Scene 1 shot 1A through the pipeline (first live mitte generation test)
**Outcome:** mitte authentication could not be resolved on the rex server. Escalating per task instructions.

---

## HUMAN ACTION NEEDED

Bruno: I need a Playwright `storage_state.json` carrying your logged-in mitte.ai session before the rex server can drive `MitteSeedanceGenerator`.

**Quickest path (~5 min on your Mac):**

```bash
# On your local machine (anywhere you're normally logged in to mitte.ai):
pip install playwright && playwright install chromium
git pull && python scripts/pipeline/capture_mitte_auth.py
# A Chromium window opens at https://mitte.ai/. Log in normally, then
# come back to the terminal and press <Enter>.

# Verify it actually saved an authenticated session:
python scripts/pipeline/capture_mitte_auth.py --verify mitte-storage-state.json
# Expect: "verify(...): logged_in=True, anonymous=False"

# Upload somewhere the rex server can read (treat like a password!):
scp mitte-storage-state.json rex:~/.config/mitte/storage-state.json
# OR: rclone copy mitte-storage-state.json r2:rex-private/mitte/
```

Once that's in place I can re-run this task with:

```bash
python -m scripts.pipeline.orchestrator run \
  --manifest asset-bible/manifests/scene-01.json \
  --references-dir asset-bible \
  --work-dir footage/scene-01 \
  --generator mitte --validator real \
  --mitte-storage-state ~/.config/mitte/storage-state.json \
  --budget 3.00
```

The session cookie expires (typically days/weeks); when it does, the verify command will report `logged_in=False` and we'll need a fresh capture.

---

## What I checked on the rex server

| Check | Result |
|---|---|
| Saved Playwright `storage_state.json` anywhere on disk | **Not found.** Searched `/home/rex/`, project, R2. |
| Browser profile with mitte.ai cookies | **Not found.** `~/.config/{google-chrome,chromium,brave,edge,vivaldi,opera}/Default/` are all either missing or empty. |
| Mitte credentials in env / `.env` / secret stores | **Not found.** No `MITTE_*` env vars; no `.env` in repo. |
| Mitte clip on R2 from a prior run | Found - `r2:rex-assets/animation-tests/scene01-seedance-mitte/shots/01-shot-1A.mp4` (Bruno's earlier manual run). Useful for validator testing later, but doesn't help the auth question. |
| Mitte clip in git history of the orchestrator | Not committed. Per CLAUDE.md, large files stay on R2. |
| `MITTE_STORAGE_STATE` env var | Empty. |
| Python `playwright` package | Installed via `pip3 install --user --break-system-packages playwright` (1.60.0). |
| Chromium for Playwright | Downloaded - `~/.cache/ms-playwright/chromium-1208` + `chromium_headless_shell-1223` (headless launch verified against `https://example.com` and `https://mitte.ai/`). |
| Xvfb / xvfb-run available for headed flows | Yes - `/usr/bin/Xvfb`, `/usr/bin/xvfb-run` installed. `DISPLAY` is unset. |
| Can the rex server reach mitte.ai | Yes - `https://mitte.ai/` resolves to 91.98.117.102 and returns a 200. **Note: `app.mitte.ai` is NXDOMAIN** - the actual app is served at `https://mitte.ai/`, not `https://app.mitte.ai/` as the orchestrator originally assumed. Fixed in this PR. |

So the rex environment is fully capable of running `MitteSeedanceGenerator` once it has a valid `storage_state.json` - that's the only missing piece.

## Why we can't get auth ourselves

Mitte's Basic plan has no API key / service-account option, so a session cookie from a logged-in browser is currently the only path. Logging in requires:

1. Bruno's email + password (not on the server, and shouldn't be).
2. Likely an email OTP confirmation, which lands in Bruno's inbox.

Neither can be done without a human in the loop, so the task's "STOP and report" path is the right one here.

## What changed in this PR

- **`scripts/pipeline/capture_mitte_auth.py`** *(new)*: The helper Bruno runs locally to capture + verify the storage_state. This is the only thing standing between us and a real shot-1A render.
- **`scripts/pipeline/orchestrator.py`**: `MitteSeedanceGenerator(base_url=...)` default changed from `https://app.mitte.ai/` to `https://mitte.ai/` (the app.mitte.ai subdomain does not exist).
- **`reports/scene-01-1A/auth-escalation.md`** *(this file)*: the escalation record so the next session can pick this back up without re-discovering the auth gap.

## Cost

| Item | $ |
|---|---|
| mitte Seedance generation | $0.00 - never reached (blocked on auth) |
| Validator vision calls | $0.00 - validator not reached |
| Total | **$0.00** of the $3.00 cap |
| Mitte credits remaining | unchanged from ~20,730 |

## Next steps after auth lands

1. Bruno runs the capture script -> hands off `mitte-storage-state.json`.
2. I re-run task #328 with the storage_state - same script, same budget cap.
3. Live MitteSeedanceGenerator + RealValidator on shot 1A end-to-end; clip and verdict uploaded to `r2:rex-assets/orchestrator-runs/scene-01-1A/`.

I'd recommend doing the capture once into a memorable location (e.g. `~/.config/mitte/storage-state.json` on Bruno's Mac AND on rex) so future shots don't need to re-do it for a few weeks.
