#!/usr/bin/env python3
"""
Twitter/X monitoring script for @rex_the_movie

Monitors mentions and keywords, creates tasks for engagement opportunities.
Uses bird CLI for Twitter API access.
"""

import json
import subprocess
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Configuration
ACCOUNT_HANDLE = "rex_the_movie"
CREDENTIALS_FILE = Path.home() / ".config" / "bird" / "credentials.env"


def load_credentials():
    """Load Twitter credentials from env file if available."""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    # Handle export VAR=value format
                    if line.startswith("export "):
                        line = line[7:]
                    key, value = line.split("=", 1)
                    # Remove quotes from value
                    value = value.strip('"').strip("'")
                    if value and not value.startswith("your_"):
                        os.environ[key] = value


# Load credentials on import
load_credentials()
KEYWORDS = [
    "fairy dinosaur",
    "rex marks the spot",
    "rexmarksthespot",
    "ai movie",
    "ai animation",
    "ai filmmaking",
    "ai animated movie",
]

# Paths
STATE_DIR = Path.home() / ".local" / "share" / "rex-twitter-monitor"
SEEN_TWEETS_FILE = STATE_DIR / "seen_tweets.json"
LOG_FILE = STATE_DIR / "monitor.log"

# Task creation settings
TASK_PROJECT = "personal"


@dataclass
class Tweet:
    """Represents a tweet from the bird CLI output."""
    id: str
    text: str
    author_handle: str
    author_name: str
    created_at: str
    url: str
    likes: int = 0
    retweets: int = 0
    replies: int = 0


def log(message: str, level: str = "INFO"):
    """Log a message to file and stdout."""
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)

    # Ensure log directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def run_bird_command(args: list[str], timeout: int = 60) -> Optional[dict | list]:
    """Run a bird CLI command and return JSON output."""
    cmd = ["bird", "--json", "--plain"] + args
    log(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            log(f"bird command failed: {result.stderr}", "ERROR")
            return None

        if not result.stdout.strip():
            return None

        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        log(f"bird command timed out after {timeout}s", "ERROR")
        return None
    except json.JSONDecodeError as e:
        log(f"Failed to parse JSON output: {e}", "ERROR")
        return None
    except FileNotFoundError:
        log("bird CLI not found. Install with: npm install -g @steipete/bird", "ERROR")
        return None


def check_credentials() -> bool:
    """Verify bird CLI credentials are configured and working."""
    result = subprocess.run(
        ["bird", "check"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        log("Bird credentials not configured or invalid", "ERROR")
        log("Run: bird whoami to check your authentication", "ERROR")
        return False

    return True


def load_seen_tweets() -> set[str]:
    """Load the set of already-processed tweet IDs."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    if SEEN_TWEETS_FILE.exists():
        with open(SEEN_TWEETS_FILE) as f:
            data = json.load(f)
            return set(data.get("seen_ids", []))
    return set()


def save_seen_tweets(seen: set[str]):
    """Save the set of processed tweet IDs."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Keep only recent IDs to prevent unbounded growth
    # Twitter IDs are time-based, so we can sort and trim
    sorted_ids = sorted(seen, reverse=True)[:1000]

    with open(SEEN_TWEETS_FILE, "w") as f:
        json.dump({
            "seen_ids": sorted_ids,
            "updated_at": datetime.now().isoformat()
        }, f, indent=2)


def parse_tweet(data: dict) -> Optional[Tweet]:
    """Parse a tweet from bird CLI JSON output."""
    try:
        # Handle different response formats from bird
        tweet_id = data.get("id") or data.get("rest_id") or data.get("id_str")
        if not tweet_id:
            return None

        # Get author info
        author = data.get("author", {})
        if not author:
            user = data.get("user", {})
            author = {
                "handle": user.get("screen_name", "unknown"),
                "name": user.get("name", "Unknown")
            }

        return Tweet(
            id=str(tweet_id),
            text=data.get("text", data.get("full_text", "")),
            author_handle=author.get("handle", author.get("screen_name", "unknown")),
            author_name=author.get("name", "Unknown"),
            created_at=data.get("created_at", ""),
            url=f"https://x.com/{author.get('handle', 'i')}/status/{tweet_id}",
            likes=data.get("favorite_count", 0),
            retweets=data.get("retweet_count", 0),
            replies=data.get("reply_count", 0)
        )
    except Exception as e:
        log(f"Failed to parse tweet: {e}", "ERROR")
        return None


def get_mentions() -> list[Tweet]:
    """Fetch recent mentions of @rex_the_movie."""
    log(f"Fetching mentions for @{ACCOUNT_HANDLE}")

    result = run_bird_command(["mentions", f"@{ACCOUNT_HANDLE}", "--limit", "20"])
    if not result:
        return []

    tweets = []
    items = result if isinstance(result, list) else result.get("tweets", [])

    for item in items:
        tweet = parse_tweet(item)
        if tweet:
            tweets.append(tweet)

    log(f"Found {len(tweets)} mentions")
    return tweets


def search_keywords() -> list[Tweet]:
    """Search for tweets matching our keywords."""
    all_tweets = []

    for keyword in KEYWORDS:
        log(f"Searching for: {keyword}")

        # Search excluding our own account's tweets
        query = f'"{keyword}" -from:{ACCOUNT_HANDLE}'
        result = run_bird_command(["search", query, "--limit", "10"])

        if not result:
            continue

        items = result if isinstance(result, list) else result.get("tweets", [])

        for item in items:
            tweet = parse_tweet(item)
            if tweet:
                all_tweets.append(tweet)

    # Deduplicate
    seen_ids = set()
    unique_tweets = []
    for tweet in all_tweets:
        if tweet.id not in seen_ids:
            seen_ids.add(tweet.id)
            unique_tweets.append(tweet)

    log(f"Found {len(unique_tweets)} unique keyword matches")
    return unique_tweets


def create_engagement_task(tweet: Tweet, reason: str):
    """Create a task for engagement opportunity."""
    title = f"Twitter: Engage with @{tweet.author_handle} ({reason})"

    body = f"""Engagement opportunity on Twitter/X

**Tweet**: {tweet.url}
**Author**: @{tweet.author_handle} ({tweet.author_name})
**Reason**: {reason}

**Tweet text**:
> {tweet.text[:500]}{'...' if len(tweet.text) > 500 else ''}

**Metrics**: {tweet.likes} likes, {tweet.retweets} RTs, {tweet.replies} replies

**Suggested actions**:
- Like the tweet
- Reply with relevant info about Rex Marks the Spot
- Consider quote tweeting if highly relevant
"""

    try:
        result = subprocess.run(
            ["ty", "create", "--project", TASK_PROJECT, "--title", title, "--body", body],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            log(f"Created task for tweet {tweet.id}")
            return True
        else:
            log(f"Failed to create task: {result.stderr}", "ERROR")
            return False
    except FileNotFoundError:
        log("ty CLI not found, skipping task creation", "WARN")
        return False


def categorize_tweet(tweet: Tweet) -> str:
    """Determine why this tweet is relevant."""
    text_lower = tweet.text.lower()

    if f"@{ACCOUNT_HANDLE}".lower() in text_lower:
        return "mention"

    for keyword in KEYWORDS:
        if keyword.lower() in text_lower:
            return f"keyword: {keyword}"

    return "related"


def should_create_task(tweet: Tweet) -> bool:
    """Determine if a tweet warrants a task."""
    # Skip our own tweets
    if tweet.author_handle.lower() == ACCOUNT_HANDLE.lower():
        return False

    # Skip very low engagement tweets (likely spam or bots)
    # But allow any mention regardless of engagement
    if f"@{ACCOUNT_HANDLE}".lower() not in tweet.text.lower():
        if tweet.likes == 0 and tweet.retweets == 0:
            return False

    return True


def monitor():
    """Main monitoring loop."""
    log("=" * 50)
    log("Starting Twitter monitor run")

    # Check credentials first
    if not check_credentials():
        log("Aborting: credentials not configured", "ERROR")
        sys.exit(1)

    # Load previously seen tweets
    seen = load_seen_tweets()
    log(f"Loaded {len(seen)} previously seen tweet IDs")

    # Collect all relevant tweets
    all_tweets: list[Tweet] = []

    # Get mentions
    mentions = get_mentions()
    all_tweets.extend(mentions)

    # Search keywords
    keyword_tweets = search_keywords()
    all_tweets.extend(keyword_tweets)

    # Process new tweets
    new_count = 0
    task_count = 0

    for tweet in all_tweets:
        if tweet.id in seen:
            continue

        seen.add(tweet.id)
        new_count += 1

        reason = categorize_tweet(tweet)
        log(f"New tweet: {tweet.url} ({reason})")

        if should_create_task(tweet):
            if create_engagement_task(tweet, reason):
                task_count += 1

    # Save updated seen list
    save_seen_tweets(seen)

    log(f"Monitor run complete: {new_count} new tweets, {task_count} tasks created")
    log("=" * 50)


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Twitter/X monitoring for @rex_the_movie")
    parser.add_argument("--check", action="store_true", help="Only check credentials")
    parser.add_argument("--dry-run", action="store_true", help="Don't create tasks")
    args = parser.parse_args()

    if args.check:
        if check_credentials():
            whoami = run_bird_command(["whoami"])
            if whoami:
                print(f"Authenticated as: @{whoami.get('screen_name', 'unknown')}")
            sys.exit(0)
        else:
            sys.exit(1)

    if args.dry_run:
        # Monkey-patch to skip task creation
        global create_engagement_task
        original_create = create_engagement_task
        def dry_run_create(tweet, reason):
            log(f"[DRY RUN] Would create task for {tweet.url} ({reason})")
            return True
        create_engagement_task = dry_run_create

    monitor()


if __name__ == "__main__":
    main()
