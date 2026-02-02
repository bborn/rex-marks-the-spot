#!/usr/bin/env python3
"""Capture website screenshots for social media posts."""

from pathlib import Path
from playwright.sync_api import sync_playwright

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "social-media" / "images"

# Pages to capture
PAGES = [
    {
        "url": "https://rexmarksthespot.com/",
        "filename": "website-homepage.png",
        "description": "Homepage"
    },
    {
        "url": "https://rexmarksthespot.com/storyboards/act1/panels/",
        "filename": "website-storyboards.png",
        "description": "Storyboard browser"
    },
    {
        "url": "https://rexmarksthespot.com/characters.html",
        "filename": "website-characters.png",
        "description": "Characters page"
    },
]


def main():
    """Capture screenshots of all pages."""
    print("Capturing website screenshots...")
    print("=" * 50)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)

        # Create a context with a specific viewport size (good for social media)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            device_scale_factor=2  # Retina quality
        )

        page = context.new_page()

        for item in PAGES:
            print(f"\nCapturing: {item['description']}")
            print(f"  URL: {item['url']}")

            try:
                # Navigate to page (use domcontentloaded instead of networkidle for faster loading)
                page.goto(item["url"], wait_until="domcontentloaded", timeout=30000)

                # Wait for content to render
                page.wait_for_timeout(2000)

                # Take screenshot
                output_path = OUTPUT_DIR / item["filename"]
                page.screenshot(path=str(output_path), full_page=False)

                print(f"  ✓ Saved: {output_path}")

            except Exception as e:
                print(f"  ✗ Error: {e}")

        browser.close()

    print("\n" + "=" * 50)
    print("Done!")


if __name__ == "__main__":
    main()
