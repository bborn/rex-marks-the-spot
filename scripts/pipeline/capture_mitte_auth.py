"""Capture an authenticated mitte.ai Playwright storage_state.

mitte has no API, so the orchestrator's ``MitteSeedanceGenerator`` drives a
browser. A browser on the rex server has no way to log in interactively —
mitte requires email/password (and sometimes email-OTP). This helper is
the one-step fix:

  1. Bruno runs this on his Mac (or wherever he is normally logged in to
     mitte.ai).
  2. A real Chromium window opens at https://mitte.ai/. Bruno logs in
     normally (email + password, OTP if asked).
  3. When the script sees that the page has navigated past the login
     screen, it dumps cookies + localStorage to a single JSON file
     (``--out``, default ``mitte-storage-state.json``).
  4. That JSON is the only secret. Upload it to a private location the
     rex server can read (e.g. ``r2:rex-private/mitte-storage-state.json``
     OR ``scp`` it to ``rex:~/.config/mitte/storage-state.json``), then
     point the orchestrator at it with ``--mitte-storage-state``.

Why this exists:
  * There is no saved storage_state, browser profile, or mitte credential
    anywhere on the rex server. Verified May 2026 (see
    ``reports/scene-01-1A/auth-escalation.md``).
  * mitte's web app has no service-account / API key option on the Basic
    plan, so the storage_state route is currently the only path.

The captured JSON contains the session cookie that proves "this browser
is Bruno". Treat it like a password — anyone with this file can spend
Bruno's mitte credits until the session expires (typically days/weeks).

Usage::

    # On Bruno's local machine (Mac / Windows with a display):
    pip install playwright
    playwright install chromium
    python scripts/pipeline/capture_mitte_auth.py
    # ...log in in the window that opens, then press Enter in the terminal
    # -> mitte-storage-state.json appears in the current directory

    # Verify it actually carries an authenticated session:
    python scripts/pipeline/capture_mitte_auth.py --verify mitte-storage-state.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


MITTE_BASE = "https://mitte.ai/"


def capture(out_path: Path, base_url: str = MITTE_BASE) -> int:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        print(
            "ERROR: playwright is not installed. Run:\n"
            "  pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        return 2

    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        # Headed on purpose — Bruno needs to see the login form.
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(base_url, wait_until="domcontentloaded")
        print(
            f"\n>>> A browser window opened at {base_url}.\n"
            f">>> Log in (email + password, OTP if asked), then click around\n"
            f">>> until you see your dashboard / a 'Generate' / 'New' button.\n"
            f">>> When you're sure you're logged in, come back here and\n"
            f">>> press <Enter> to save the session.\n"
        )
        try:
            input(">>> Press <Enter> when logged in (or Ctrl-C to cancel): ")
        except KeyboardInterrupt:
            print("\nCancelled - nothing saved.", file=sys.stderr)
            browser.close()
            return 130
        context.storage_state(path=str(out_path))
        browser.close()
    print(f"\nSaved storage_state -> {out_path}")
    print("Next: upload this file somewhere the rex server can read, then run")
    print(f"  python -m scripts.pipeline.orchestrator run \\")
    print(f"      --manifest asset-bible/manifests/scene-01.json \\")
    print(f"      --generator mitte --validator real \\")
    print(f"      --mitte-storage-state {out_path}")
    return 0


def verify(state_path: Path, base_url: str = MITTE_BASE) -> int:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        print("ERROR: playwright not installed.", file=sys.stderr)
        return 2
    if not state_path.exists():
        print(f"ERROR: {state_path} does not exist.", file=sys.stderr)
        return 1
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(state_path))
        page = context.new_page()
        page.goto(base_url, wait_until="networkidle", timeout=45_000)
        body = page.locator("body").inner_text()[:2_000].lower()
        # Heuristic: anonymous landing page strongly advertises "log in" and
        # "get started" CTAs; once logged-in those are replaced by the user
        # menu / credit balance / dashboard nav.
        logged_in_signals = ["credits", "my account", "log out", "logout", "sign out"]
        anonymous_cta = "get started" in body and "log in" in body
        looks_logged_in = any(s in body for s in logged_in_signals)
        looks_anonymous = anonymous_cta and not looks_logged_in
        browser.close()
    print(f"verify({state_path}): logged_in={looks_logged_in}, anonymous={looks_anonymous}")
    if looks_anonymous:
        print(
            "Storage state did NOT carry an authenticated session. "
            "Re-run `capture_mitte_auth.py` and stay logged in longer before "
            "pressing Enter.",
            file=sys.stderr,
        )
        return 1
    if looks_logged_in:
        return 0
    print(
        "Could not confidently classify the session. Open the saved JSON in a "
        "headed browser to check by eye.",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=Path("mitte-storage-state.json"))
    p.add_argument("--base-url", default=MITTE_BASE)
    p.add_argument("--verify", type=Path, default=None,
                   help="Skip capture; check that an existing storage_state JSON is still authenticated.")
    args = p.parse_args(argv)
    if args.verify is not None:
        return verify(args.verify, base_url=args.base_url)
    return capture(args.out, base_url=args.base_url)


if __name__ == "__main__":
    sys.exit(main())
