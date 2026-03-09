#!/usr/bin/env bash
#
# weekly-diary.sh — Auto-generate a weekly production diary blog post
#
# Gathers data from git commits, TaskYou tasks, and R2 asset changes,
# then uses Gemini to write a conversational blog post.
#
# USAGE:
#   ./scripts/weekly-diary.sh              # Generate this week's diary
#   ./scripts/weekly-diary.sh 2026-03-07   # Generate diary for week ending on date
#
# REQUIREMENTS:
#   - GEMINI_API_KEY in environment
#   - rclone configured with r2: remote
#   - jq installed
#   - git repo context (run from project root)
#
# CRON SETUP (every Friday at 6pm):
#   0 18 * * 5 cd /home/rex/rex-marks-the-spot && GEMINI_API_KEY=your_key ./scripts/weekly-diary.sh
#
# OUTPUT:
#   - docs/blog/posts/weekly-diary-YYYY-MM-DD.html
#   - Prints a Twitter-ready summary to stdout
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BLOG_DIR="$PROJECT_ROOT/docs/blog/posts"
R2_MANIFEST_DIR="$PROJECT_ROOT/.r2-manifests"
GEMINI_MODEL="gemini-2.5-flash"

# Date for the diary (default: today)
END_DATE="${1:-$(date +%Y-%m-%d)}"
START_DATE="$(date -d "$END_DATE - 7 days" +%Y-%m-%d 2>/dev/null || date -v-7d -j -f "%Y-%m-%d" "$END_DATE" +%Y-%m-%d)"

# Format dates for display
END_DISPLAY="$(date -d "$END_DATE" "+%B %-d, %Y" 2>/dev/null || date -j -f "%Y-%m-%d" "$END_DATE" "+%B %-d, %Y")"
WEEK_LABEL="$(date -d "$START_DATE" "+%b %-d" 2>/dev/null || date -j -f "%Y-%m-%d" "$START_DATE" "+%b %-d")–$(date -d "$END_DATE" "+%b %-d" 2>/dev/null || date -j -f "%Y-%m-%d" "$END_DATE" "+%b %-d")"

echo "Generating weekly diary for $WEEK_LABEL..."

# --- 1. Git commits from the last 7 days ---
echo "  Collecting git commits..."
GIT_LOG="$(cd "$PROJECT_ROOT" && git log --since="$START_DATE" --until="$END_DATE 23:59:59" --oneline --no-merges 2>/dev/null || echo "(no commits found)")"
COMMIT_COUNT="$(echo "$GIT_LOG" | grep -c '.' || true)"
COMMIT_COUNT="${COMMIT_COUNT:-0}"

# --- 2. TaskYou completed tasks ---
echo "  Collecting completed tasks..."
TASK_LIST="$(ty list 2>/dev/null || echo "(TaskYou unavailable)")"

# --- 3. New R2 assets (compare to cached manifest) ---
echo "  Checking R2 for new assets..."
mkdir -p "$R2_MANIFEST_DIR"
CURRENT_MANIFEST="$R2_MANIFEST_DIR/manifest-$END_DATE.txt"
PREVIOUS_MANIFEST="$(ls -t "$R2_MANIFEST_DIR"/manifest-*.txt 2>/dev/null | head -1 || true)"

# Get current R2 listing (just filenames, skip huge listing details)
if rclone ls r2:rex-assets/ --max-depth 2 2>/dev/null | awk '{print $2}' | sort > "$CURRENT_MANIFEST.tmp"; then
    mv "$CURRENT_MANIFEST.tmp" "$CURRENT_MANIFEST"
else
    echo "(rclone unavailable)" > "$CURRENT_MANIFEST"
fi

NEW_ASSETS=""
if [ -n "$PREVIOUS_MANIFEST" ] && [ "$PREVIOUS_MANIFEST" != "$CURRENT_MANIFEST" ] && [ -f "$PREVIOUS_MANIFEST" ]; then
    NEW_ASSETS="$(comm -13 "$PREVIOUS_MANIFEST" "$CURRENT_MANIFEST" 2>/dev/null | head -50 || echo "")"
fi
NEW_ASSET_COUNT="$(echo "$NEW_ASSETS" | grep -c '.' || true)"
NEW_ASSET_COUNT="${NEW_ASSET_COUNT:-0}"

# --- 4. Call Gemini to write the blog post ---
echo "  Generating blog post with Gemini..."

if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "ERROR: GEMINI_API_KEY not set" >&2
    exit 1
fi

# Build the prompt
PROMPT="$(cat <<PROMPT_EOF
You are writing a weekly production diary for "Rex Marks the Spot" (working title: "Fairy Dinosaur Date Night"), an AI-generated animated movie. The blog is conversational, honest, and technical — aimed at people interested in AI filmmaking.

Write a blog post summarizing this week's progress ($WEEK_LABEL). Keep it short (300-500 words). Be conversational and specific — mention actual tools, actual problems, actual wins. Don't be generic or hype-y.

Also output a Twitter summary (under 280 chars) on the very last line, prefixed with "TWEET: ".

Here is the raw data:

## Git Commits ($COMMIT_COUNT commits)
$GIT_LOG

## TaskYou Tasks
$TASK_LIST

## New R2 Assets ($NEW_ASSET_COUNT new files)
$NEW_ASSETS

Write the blog post body as plain HTML (just the content inside <div class="post-body">, no surrounding structure). Use <h2>, <p>, <ul>/<li> tags. Do not include a title <h1> — that goes in the header separately.

End with the TWEET: line.
PROMPT_EOF
)"

# Escape the prompt for JSON
PROMPT_JSON="$(echo "$PROMPT" | jq -Rs .)"

# Call Gemini API
RESPONSE="$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${GEMINI_API_KEY}" \
    -H 'Content-Type: application/json' \
    -d "{
        \"contents\": [{
            \"parts\": [{\"text\": $PROMPT_JSON}]
        }],
        \"generationConfig\": {
            \"temperature\": 0.8,
            \"maxOutputTokens\": 2048
        }
    }")"

# Extract the text from the response
BLOG_CONTENT="$(echo "$RESPONSE" | jq -r '.candidates[0].content.parts[0].text // empty')"

if [ -z "$BLOG_CONTENT" ]; then
    echo "ERROR: Gemini returned no content" >&2
    echo "Response: $RESPONSE" >&2
    exit 1
fi

# Split tweet from blog content
# Strip markdown code fences if Gemini wraps the response
BLOG_CONTENT="$(echo "$BLOG_CONTENT" | sed '/^```html$/d; /^```$/d')"

TWEET="$(echo "$BLOG_CONTENT" | grep -i '^\s*TWEET: ' | sed 's/^[[:space:]]*TWEET: //i' | tail -1 || true)"
POST_BODY="$(echo "$BLOG_CONTENT" | sed '/^[[:space:]]*TWEET: /Id')"

# Generate a title from the first line or heading
POST_TITLE="Weekly Diary: $WEEK_LABEL"

# --- 5. Write the HTML file ---
mkdir -p "$BLOG_DIR"
OUTPUT_FILE="$BLOG_DIR/weekly-diary-${END_DATE}.html"

cat > "$OUTPUT_FILE" <<HTML_EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${POST_TITLE} - Rex Marks The Spot</title>
    <link rel="stylesheet" href="../../css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
</head>
<body>
    <header class="site-header">
        <nav class="nav-container">
            <a href="../../index.html" class="logo">
                <span class="logo-icon">🦖</span>
                <span class="logo-text">Rex Marks The Spot</span>
            </a>
            <button class="mobile-menu-toggle" aria-label="Toggle menu">
                <span></span>
                <span></span>
                <span></span>
            </button>
            <ul class="nav-links">
                <li><a href="../../index.html">Home</a></li>
                <li><a href="../../production.html">Production</a></li>
                <li><a href="../index.html" class="active">Blog</a></li>
                <li><a href="../../about.html">About</a></li>
                <li><a href="../../links.html">Links</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <article>
            <header class="post-header">
                <div class="container">
                    <span class="post-category">Production</span>
                    <h1>${POST_TITLE}</h1>
                    <div class="post-author">
                        <time datetime="${END_DATE}">${END_DISPLAY}</time>
                    </div>
                </div>
            </header>

            <div class="post-content">
                <div class="container">
                    <div class="post-body">
                        ${POST_BODY}
                    </div>

                    <nav class="post-nav">
                        <a href="../index.html">&larr; Back to Blog</a>
                        <span></span>
                    </nav>
                </div>
            </div>
        </article>
    </main>

    <footer class="site-footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-brand">
                    <span class="logo-icon">🦖</span>
                    <span>Rex Marks The Spot</span>
                </div>
                <p class="footer-tagline">An experiment in AI-assisted filmmaking</p>
                <div class="footer-social">
                    <a href="https://github.com/bborn/rex-marks-the-spot" target="_blank" rel="noopener" title="GitHub">
                        <svg viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                    </a>
                    <a href="https://twitter.com/rex_the_movie" target="_blank" rel="noopener" title="Twitter/X">
                        <svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                    </a>
                </div>
                <nav class="footer-nav">
                    <a href="../../index.html">Home</a>
                    <a href="../../production.html">Production</a>
                    <a href="../index.html">Blog</a>
                    <a href="../../about.html">About</a>
                    <a href="../../links.html">Links</a>
                </nav>
                <p class="footer-copyright">&copy; 2026 Rex Marks The Spot. Made with creativity and AI assistance.</p>
            </div>
        </div>
    </footer>

    <script src="../../js/main.js"></script>
    <script src="../../js/chat-widget.js"></script>
</body>
</html>
HTML_EOF

echo ""
echo "Blog post written to: $OUTPUT_FILE"
echo ""
echo "--- Twitter Summary ---"
echo "$TWEET"
echo ""
