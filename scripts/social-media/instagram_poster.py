#!/usr/bin/env python3
"""
Instagram Graph API posting automation for @rex_the_movie

Automates publishing posts to Instagram using the Meta Graph API.
Supports single image posts, carousel posts, and Reels.

Requirements:
    - Instagram Business/Creator account connected to a Facebook Page
    - Meta App with instagram_basic and instagram_content_publish permissions
    - Long-lived access token (see setup guide in README.md)

Usage:
    # Post a single image
    python instagram_poster.py post --image-url "https://example.com/img.png" --caption "Hello!"

    # Post from pending-posts.md
    python instagram_poster.py publish --post 1

    # Dry run (preview without posting)
    python instagram_poster.py publish --post 1 --dry-run

    # List pending posts
    python instagram_poster.py list

    # Check API status
    python instagram_poster.py check
"""

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install with: pip install requests")
    sys.exit(1)


# --- Configuration ---

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

CREDENTIALS_FILE = Path.home() / ".config" / "rex-social" / "instagram.env"
STATE_DIR = Path.home() / ".local" / "share" / "rex-instagram"
LOG_FILE = STATE_DIR / "instagram.log"
POSTED_FILE = STATE_DIR / "posted.json"

# R2 public URL for assets
R2_PUBLIC_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev"

# Project root (relative to this script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PENDING_POSTS_FILE = PROJECT_ROOT / "docs" / "social-media" / "pending-posts.md"


# --- Data Models ---

@dataclass
class InstagramConfig:
    access_token: str
    ig_user_id: str
    page_id: str = ""

    def is_valid(self) -> bool:
        return bool(self.access_token and self.ig_user_id)


@dataclass
class PostContent:
    """A single Instagram post to publish."""
    post_number: int
    title: str
    caption: str
    hashtags: str = ""
    image_urls: list[str] = field(default_factory=list)
    image_paths: list[str] = field(default_factory=list)
    post_type: str = "image"  # image, carousel, reel


# --- Logging ---

def log(message: str, level: str = "INFO"):
    """Log to file and stdout."""
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


# --- Credentials ---

def load_credentials() -> Optional[InstagramConfig]:
    """Load Instagram API credentials from env file."""
    # Check env file first
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    if line.startswith("export "):
                        line = line[7:]
                    key, value = line.split("=", 1)
                    value = value.strip('"').strip("'")
                    if value and not value.startswith("your_"):
                        os.environ[key] = value

    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
    ig_user_id = os.environ.get("INSTAGRAM_USER_ID", "")
    page_id = os.environ.get("FACEBOOK_PAGE_ID", "")

    if not access_token or not ig_user_id:
        return None

    return InstagramConfig(
        access_token=access_token,
        ig_user_id=ig_user_id,
        page_id=page_id,
    )


# --- Instagram Graph API ---

class InstagramAPI:
    """Instagram Graph API client for content publishing."""

    def __init__(self, config: InstagramConfig):
        self.config = config
        self.base_url = GRAPH_API_BASE
        self.session = requests.Session()

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request."""
        url = f"{self.base_url}/{endpoint}"

        # Always include access token
        if "params" not in kwargs:
            kwargs["params"] = {}
        kwargs["params"]["access_token"] = self.config.access_token

        response = self.session.request(method, url, **kwargs)

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", response.text)
            raise APIError(
                f"API error ({response.status_code}): {error_msg}",
                status_code=response.status_code,
                error_data=error_data,
            )

        return response.json()

    def check_account(self) -> dict:
        """Verify the Instagram account and token are working."""
        return self._request(
            "GET",
            self.config.ig_user_id,
            params={"fields": "id,username,name,biography,followers_count,media_count"},
        )

    def check_token_expiry(self) -> dict:
        """Check when the access token expires."""
        return self._request(
            "GET",
            "debug_token",
            params={"input_token": self.config.access_token},
        )

    def create_image_container(self, image_url: str, caption: str = "",
                                is_carousel_item: bool = False) -> str:
        """
        Create a media container for a single image.

        Args:
            image_url: Publicly accessible URL of the image
            caption: Post caption (ignored for carousel items)
            is_carousel_item: If True, creates a carousel item container

        Returns:
            Container/creation ID
        """
        data = {
            "image_url": image_url,
        }

        if is_carousel_item:
            data["is_carousel_item"] = "true"
        else:
            data["caption"] = caption

        result = self._request(
            "POST",
            f"{self.config.ig_user_id}/media",
            data=data,
        )
        return result["id"]

    def create_carousel_container(self, children_ids: list[str], caption: str) -> str:
        """
        Create a carousel container from individual media containers.

        Args:
            children_ids: List of container IDs for carousel items
            caption: Post caption

        Returns:
            Carousel container ID
        """
        result = self._request(
            "POST",
            f"{self.config.ig_user_id}/media",
            data={
                "media_type": "CAROUSEL",
                "caption": caption,
                "children": ",".join(children_ids),
            },
        )
        return result["id"]

    def create_reel_container(self, video_url: str, caption: str = "",
                               cover_url: str = "") -> str:
        """
        Create a Reels container.

        Args:
            video_url: Publicly accessible URL of the video
            caption: Reel caption
            cover_url: Optional cover image URL

        Returns:
            Container ID
        """
        data = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
        }

        if cover_url:
            data["cover_url"] = cover_url

        result = self._request(
            "POST",
            f"{self.config.ig_user_id}/media",
            data=data,
        )
        return result["id"]

    def check_container_status(self, container_id: str) -> dict:
        """Check the status of a media container (for video uploads)."""
        return self._request(
            "GET",
            container_id,
            params={"fields": "status_code,status"},
        )

    def publish(self, container_id: str) -> str:
        """
        Publish a media container.

        Args:
            container_id: The container/creation ID to publish

        Returns:
            Published media ID
        """
        result = self._request(
            "POST",
            f"{self.config.ig_user_id}/media_publish",
            data={"creation_id": container_id},
        )
        return result["id"]

    def get_media_permalink(self, media_id: str) -> str:
        """Get the permalink for a published post."""
        result = self._request(
            "GET",
            media_id,
            params={"fields": "permalink"},
        )
        return result.get("permalink", "")

    def publish_image(self, image_url: str, caption: str) -> dict:
        """
        Full flow: create container and publish a single image post.

        Returns:
            dict with media_id and permalink
        """
        log(f"Creating image container...")
        container_id = self.create_image_container(image_url, caption)
        log(f"Container created: {container_id}")

        # Brief wait for processing
        time.sleep(2)

        log(f"Publishing...")
        media_id = self.publish(container_id)
        log(f"Published! Media ID: {media_id}")

        permalink = self.get_media_permalink(media_id)
        log(f"Post URL: {permalink}")

        return {"media_id": media_id, "permalink": permalink}

    def publish_carousel(self, image_urls: list[str], caption: str) -> dict:
        """
        Full flow: create containers and publish a carousel post.

        Returns:
            dict with media_id and permalink
        """
        # Create individual item containers
        children_ids = []
        for i, url in enumerate(image_urls):
            log(f"Creating carousel item {i+1}/{len(image_urls)}...")
            child_id = self.create_image_container(url, is_carousel_item=True)
            children_ids.append(child_id)
            time.sleep(1)  # Rate limit buffer

        # Create carousel container
        log(f"Creating carousel container with {len(children_ids)} items...")
        container_id = self.create_carousel_container(children_ids, caption)
        log(f"Carousel container: {container_id}")

        time.sleep(2)

        log(f"Publishing carousel...")
        media_id = self.publish(container_id)
        log(f"Published! Media ID: {media_id}")

        permalink = self.get_media_permalink(media_id)
        log(f"Post URL: {permalink}")

        return {"media_id": media_id, "permalink": permalink}

    def publish_reel(self, video_url: str, caption: str,
                     cover_url: str = "", timeout: int = 120) -> dict:
        """
        Full flow: upload and publish a Reel.

        Returns:
            dict with media_id and permalink
        """
        log(f"Creating Reel container...")
        container_id = self.create_reel_container(video_url, caption, cover_url)
        log(f"Reel container: {container_id}")

        # Wait for video processing
        start = time.time()
        while time.time() - start < timeout:
            status = self.check_container_status(container_id)
            code = status.get("status_code", "")
            log(f"Processing status: {code}")

            if code == "FINISHED":
                break
            elif code == "ERROR":
                raise APIError(f"Video processing failed: {status.get('status', '')}")

            time.sleep(5)
        else:
            raise APIError(f"Video processing timed out after {timeout}s")

        log(f"Publishing Reel...")
        media_id = self.publish(container_id)
        log(f"Published! Media ID: {media_id}")

        permalink = self.get_media_permalink(media_id)
        log(f"Post URL: {permalink}")

        return {"media_id": media_id, "permalink": permalink}


class APIError(Exception):
    """Instagram API error."""
    def __init__(self, message: str, status_code: int = 0, error_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_data = error_data or {}


# --- Content Parsing ---

def parse_pending_posts(filepath: Path = None) -> list[PostContent]:
    """Parse the pending-posts.md file to extract Instagram posts."""
    filepath = filepath or PENDING_POSTS_FILE

    if not filepath.exists():
        log(f"Pending posts file not found: {filepath}", "WARN")
        return []

    content = filepath.read_text()
    posts = []

    # Split by "## Post N:" headers
    post_sections = re.split(r"## Post (\d+):", content)

    # post_sections[0] is before first post, then alternating number/content
    for i in range(1, len(post_sections) - 1, 2):
        post_num = int(post_sections[i])
        section = post_sections[i + 1]

        # Extract the Instagram section
        ig_match = re.search(
            r"### Instagram\s*\n(.*?)(?=\n---|\n### (?!Instagram)|\Z)",
            section,
            re.DOTALL,
        )

        if not ig_match:
            continue

        ig_section = ig_match.group(1)

        # Extract caption (between **Caption:** and next section)
        caption_match = re.search(
            r"\*\*Caption:\*\*\s*\n(.*?)(?=\n---|\n\*\*|\Z)",
            ig_section,
            re.DOTALL,
        )

        caption = caption_match.group(1).strip() if caption_match else ""

        # Extract title from section header
        title_match = re.match(r"\s*(.+?)(?:\n|$)", section)
        title = title_match.group(1).strip() if title_match else f"Post {post_num}"

        # Extract suggested images section
        images_match = re.search(
            r"### Suggested Images\s*\n(.*?)(?=\n---|\n## |\Z)",
            section,
            re.DOTALL,
        )

        image_paths = []
        if images_match:
            images_text = images_match.group(1)
            # Find file paths in backticks
            image_paths = re.findall(r"`([^`]+\.(?:png|jpg|jpeg|gif|mp4|webp))`", images_text)

        # Determine post type
        post_type = "image"
        if len(image_paths) > 1:
            # Check if suggested as carousel
            if "carousel" in section.lower() or "comparison" in section.lower():
                post_type = "carousel"
        if any(p.endswith(".mp4") for p in image_paths):
            post_type = "reel"

        posts.append(PostContent(
            post_number=post_num,
            title=title,
            caption=caption,
            image_paths=image_paths,
            post_type=post_type,
        ))

    return posts


def resolve_image_url(path: str) -> str:
    """
    Convert a local asset path to a public R2 URL.

    If the path is already an http URL, return as-is.
    Otherwise, assume it's relative to the R2 bucket.
    """
    if path.startswith("http://") or path.startswith("https://"):
        return path

    # Strip leading paths that reference local directories
    # e.g., "docs/social-media/images/foo.png" -> "social-media/images/foo.png"
    clean_path = path.lstrip("./")

    # If it starts with docs/, strip it for R2 path
    if clean_path.startswith("docs/"):
        clean_path = clean_path[5:]

    return f"{R2_PUBLIC_URL}/{clean_path}"


# --- Post Tracking ---

def load_posted() -> dict:
    """Load the record of already-posted content."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if POSTED_FILE.exists():
        with open(POSTED_FILE) as f:
            return json.load(f)
    return {"posts": {}}


def save_posted(data: dict):
    """Save the posted content record."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(POSTED_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_post(post_number: int, media_id: str, permalink: str):
    """Record that a post was published."""
    data = load_posted()
    data["posts"][str(post_number)] = {
        "media_id": media_id,
        "permalink": permalink,
        "posted_at": datetime.now().isoformat(),
    }
    save_posted(data)


# --- Commands ---

def cmd_check(config: InstagramConfig):
    """Check API access and account status."""
    api = InstagramAPI(config)

    print("Checking Instagram API access...\n")

    try:
        account = api.check_account()
        print(f"  Account: @{account.get('username', 'unknown')}")
        print(f"  Name: {account.get('name', 'N/A')}")
        print(f"  Followers: {account.get('followers_count', 'N/A')}")
        print(f"  Posts: {account.get('media_count', 'N/A')}")
        print(f"\n  API access: OK")
    except APIError as e:
        print(f"\n  API access: FAILED")
        print(f"  Error: {e}")
        return False

    # Check token expiry
    try:
        token_info = api.check_token_expiry()
        token_data = token_info.get("data", {})
        expires = token_data.get("expires_at", 0)
        if expires:
            from datetime import datetime as dt
            expiry_date = dt.fromtimestamp(expires)
            days_left = (expiry_date - dt.now()).days
            print(f"\n  Token expires: {expiry_date.isoformat()} ({days_left} days)")
            if days_left < 7:
                print("  WARNING: Token expiring soon! Refresh it.")
        else:
            print("\n  Token: Never expires (long-lived)")
    except APIError:
        print("\n  Token expiry: Could not check")

    return True


def cmd_list():
    """List pending posts from pending-posts.md."""
    posts = parse_pending_posts()
    posted = load_posted()

    if not posts:
        print("No pending posts found.")
        print(f"  File: {PENDING_POSTS_FILE}")
        return

    print(f"Found {len(posts)} posts in pending-posts.md:\n")

    for post in posts:
        status = "POSTED" if str(post.post_number) in posted.get("posts", {}) else "PENDING"
        status_icon = "[x]" if status == "POSTED" else "[ ]"

        print(f"  {status_icon} Post {post.post_number}: {post.title}")
        print(f"      Type: {post.post_type}")
        print(f"      Images: {len(post.image_paths)}")
        if post.caption:
            preview = post.caption[:80].replace("\n", " ")
            print(f"      Caption: {preview}...")

        if status == "POSTED":
            info = posted["posts"][str(post.post_number)]
            print(f"      Posted: {info.get('posted_at', 'unknown')}")
            print(f"      URL: {info.get('permalink', 'N/A')}")

        print()


def cmd_post(config: InstagramConfig, image_url: str, caption: str,
             post_type: str = "image", dry_run: bool = False):
    """Post a single image/carousel/reel to Instagram."""
    api = InstagramAPI(config)

    if dry_run:
        print("\n=== DRY RUN - No actual posting ===\n")
        print(f"  Type: {post_type}")
        print(f"  Image URL: {image_url}")
        print(f"  Caption ({len(caption)} chars):")
        print(f"  {caption[:200]}...")
        print("\n=== END DRY RUN ===")
        return

    result = api.publish_image(image_url, caption)
    print(f"\nPost published!")
    print(f"  Media ID: {result['media_id']}")
    print(f"  URL: {result['permalink']}")


def cmd_publish(config: InstagramConfig, post_number: int,
                dry_run: bool = False, image_url_override: str = ""):
    """Publish a specific post from pending-posts.md."""
    posts = parse_pending_posts()

    post = None
    for p in posts:
        if p.post_number == post_number:
            post = p
            break

    if not post:
        print(f"Post {post_number} not found in pending-posts.md")
        return False

    # Check if already posted
    posted = load_posted()
    if str(post_number) in posted.get("posts", {}):
        info = posted["posts"][str(post_number)]
        print(f"Post {post_number} was already published!")
        print(f"  Posted: {info.get('posted_at')}")
        print(f"  URL: {info.get('permalink')}")
        answer = input("\nPublish again? [y/N]: ").strip().lower()
        if answer != "y":
            return False

    # Resolve image URLs
    if image_url_override:
        image_urls = [image_url_override]
    else:
        image_urls = [resolve_image_url(p) for p in post.image_paths]

    if not image_urls:
        print(f"No images found for Post {post_number}.")
        print("Provide an image URL with --image-url, or add images to pending-posts.md")
        return False

    # Show preview
    print(f"\n{'='*60}")
    print(f"Post {post.post_number}: {post.title}")
    print(f"{'='*60}")
    print(f"Type: {post.post_type}")
    print(f"Images ({len(image_urls)}):")
    for url in image_urls:
        print(f"  - {url}")
    print(f"\nCaption ({len(post.caption)} chars):")
    print(f"{post.caption}")
    print(f"{'='*60}")

    if dry_run:
        print("\n[DRY RUN] Would publish the above post. No API call made.")
        return True

    api = InstagramAPI(config)

    try:
        if post.post_type == "carousel" and len(image_urls) > 1:
            result = api.publish_carousel(image_urls, post.caption)
        elif post.post_type == "reel" and image_urls[0].endswith(".mp4"):
            result = api.publish_reel(image_urls[0], post.caption)
        else:
            result = api.publish_image(image_urls[0], post.caption)

        # Record the post
        record_post(post_number, result["media_id"], result["permalink"])

        print(f"\nPost {post_number} published successfully!")
        print(f"  Media ID: {result['media_id']}")
        print(f"  URL: {result['permalink']}")
        return True

    except APIError as e:
        log(f"Failed to publish post {post_number}: {e}", "ERROR")
        print(f"\nFailed to publish: {e}")
        return False


def cmd_export(post_number: Optional[int] = None):
    """
    Export posts in ready-to-paste format (manual fallback).

    If no post number given, exports all pending posts.
    """
    posts = parse_pending_posts()
    posted = load_posted()

    if post_number:
        posts = [p for p in posts if p.post_number == post_number]

    if not posts:
        print("No posts to export.")
        return

    for post in posts:
        status = "POSTED" if str(post.post_number) in posted.get("posts", {}) else "PENDING"

        print(f"\n{'='*60}")
        print(f"POST {post.post_number}: {post.title} [{status}]")
        print(f"{'='*60}")

        # Caption ready to copy-paste
        print(f"\n--- CAPTION (copy below) ---\n")
        print(post.caption)
        print(f"\n--- END CAPTION ---")

        # Image URLs
        if post.image_paths:
            print(f"\n--- IMAGES ---")
            for path in post.image_paths:
                url = resolve_image_url(path)
                local = PROJECT_ROOT / path.lstrip("./")
                exists = local.exists()
                print(f"  {'[local]' if exists else '[R2]   '} {url}")
                if exists:
                    print(f"           Local: {local}")
            print(f"--- END IMAGES ---")

        print()


def cmd_refresh_token(config: InstagramConfig):
    """Refresh a long-lived token (extends by 60 days)."""
    try:
        response = requests.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": os.environ.get("META_APP_ID", ""),
                "client_secret": os.environ.get("META_APP_SECRET", ""),
                "fb_exchange_token": config.access_token,
            },
        )

        if response.status_code == 200:
            data = response.json()
            new_token = data.get("access_token")
            expires_in = data.get("expires_in", 0)
            days = expires_in // 86400

            print(f"Token refreshed! New token expires in {days} days.")
            print(f"\nNew token (update your credentials file):")
            print(f"  INSTAGRAM_ACCESS_TOKEN=\"{new_token}\"")
            return True
        else:
            error = response.json().get("error", {}).get("message", response.text)
            print(f"Token refresh failed: {error}")
            print("\nMake sure META_APP_ID and META_APP_SECRET are set.")
            return False
    except Exception as e:
        print(f"Token refresh error: {e}")
        return False


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Instagram posting automation for @rex_the_movie",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s check                          Check API access
  %(prog)s list                           List pending posts
  %(prog)s publish --post 1 --dry-run     Preview post 1
  %(prog)s publish --post 1               Publish post 1
  %(prog)s export                         Export all for manual posting
  %(prog)s export --post 1                Export post 1 for manual posting
  %(prog)s post --image-url URL --caption "text"  Direct post
  %(prog)s refresh-token                  Extend token expiry
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # check
    subparsers.add_parser("check", help="Check API access and account status")

    # list
    subparsers.add_parser("list", help="List pending posts from content calendar")

    # publish
    pub_parser = subparsers.add_parser("publish", help="Publish a post from pending-posts.md")
    pub_parser.add_argument("--post", type=int, required=True, help="Post number to publish")
    pub_parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    pub_parser.add_argument("--image-url", help="Override image URL")

    # post (direct)
    post_parser = subparsers.add_parser("post", help="Post directly with URL and caption")
    post_parser.add_argument("--image-url", required=True, help="Public image URL")
    post_parser.add_argument("--caption", required=True, help="Post caption")
    post_parser.add_argument("--type", choices=["image", "carousel", "reel"], default="image")
    post_parser.add_argument("--dry-run", action="store_true", help="Preview without posting")

    # export
    export_parser = subparsers.add_parser("export", help="Export posts for manual posting")
    export_parser.add_argument("--post", type=int, help="Specific post number")

    # refresh-token
    subparsers.add_parser("refresh-token", help="Refresh long-lived access token")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Commands that don't need credentials
    if args.command == "list":
        cmd_list()
        return

    if args.command == "export":
        cmd_export(args.post if hasattr(args, "post") else None)
        return

    # Commands that need credentials
    config = load_credentials()
    if not config or not config.is_valid():
        print("Instagram API credentials not configured.")
        print(f"\nSetup instructions:")
        print(f"  1. Follow the setup guide in scripts/social-media/README.md")
        print(f"  2. Create {CREDENTIALS_FILE} with your tokens")
        print(f"  3. Or set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID env vars")

        if args.command in ("list", "export"):
            print(f"\nNote: '{args.command}' works without credentials for previewing content.")

        sys.exit(1)

    if args.command == "check":
        success = cmd_check(config)
        sys.exit(0 if success else 1)

    elif args.command == "publish":
        cmd_publish(config, args.post, args.dry_run,
                    args.image_url or "")

    elif args.command == "post":
        cmd_post(config, args.image_url, args.caption, args.type, args.dry_run)

    elif args.command == "refresh-token":
        cmd_refresh_token(config)


if __name__ == "__main__":
    main()
