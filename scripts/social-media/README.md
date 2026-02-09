# Social Media Automation for Rex Marks the Spot

Automated posting and monitoring tools for the project's social media accounts.

## Tools

| Script | Platform | Purpose |
|--------|----------|---------|
| `instagram_poster.py` | Instagram | Automated posting via Graph API |
| `twitter_monitor.py` | Twitter/X | Mention monitoring and keyword tracking |

---

## Instagram Posting (`instagram_poster.py`)

Automates publishing posts to Instagram using the Meta/Instagram Graph API.
Supports single image posts, carousel posts, and Reels.

### Prerequisites

The Instagram Graph API requires:

1. An **Instagram Business or Creator account** (free to convert)
2. A **Facebook Page** connected to the Instagram account
3. A **Meta App** registered in the Meta Developer Portal
4. API permissions: `instagram_basic`, `instagram_content_publish`

### Setup Guide (Bruno must complete these steps)

#### Step 1: Convert Instagram to Business/Creator Account

1. Open Instagram app > Settings > Account > Switch to Professional Account
2. Choose **Creator** (best for content creators) or **Business**
3. Pick a category (e.g., "Art" or "Film")
4. This does NOT affect your handle, followers, or existing posts

#### Step 2: Create/Connect a Facebook Page

1. Go to https://www.facebook.com/pages/create
2. Create a page for "Rex Marks the Spot" (or use an existing one)
3. In Instagram Settings > Account > Linked Accounts, connect the Facebook Page
4. Alternatively: In Facebook Page settings > Instagram, connect the IG account

#### Step 3: Create a Meta App

1. Go to https://developers.facebook.com/apps/
2. Click "Create App"
3. Choose "Business" type
4. Name it "Rex Social Poster" (or similar)
5. Add the **Instagram Graph API** product to the app

#### Step 4: Get Permissions

For a personal project (posting to your own account), you can use **Development Mode** without App Review:

1. In the Meta App Dashboard, go to **Instagram Graph API > Settings**
2. Add your Instagram account as a test user
3. Generate a **User Access Token** with these permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`

#### Step 5: Get a Long-Lived Token

Short-lived tokens expire in 1 hour. Convert to long-lived (60 days):

1. In Meta App Dashboard, go to Tools > Graph API Explorer
2. Generate a User Token with the permissions above
3. Exchange it for a long-lived token:

```bash
curl -s "https://graph.facebook.com/v21.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=YOUR_SHORT_TOKEN"
```

4. The response contains a token valid for 60 days
5. Use `instagram_poster.py refresh-token` to extend before expiry

#### Step 6: Get Your Instagram User ID

```bash
curl -s "https://graph.facebook.com/v21.0/me/accounts?access_token=YOUR_TOKEN" | python3 -m json.tool
```

This returns your Facebook Pages. For each page, get the connected IG account:

```bash
curl -s "https://graph.facebook.com/v21.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"
```

The `instagram_business_account.id` is your `INSTAGRAM_USER_ID`.

#### Step 7: Configure Credentials

```bash
mkdir -p ~/.config/rex-social
cp scripts/social-media/instagram_credentials.env.example ~/.config/rex-social/instagram.env
```

Edit `~/.config/rex-social/instagram.env`:

```bash
export INSTAGRAM_USER_ID="17841400123456789"
export INSTAGRAM_ACCESS_TOKEN="EAABx..."
export FACEBOOK_PAGE_ID="123456789"
export META_APP_ID="your_app_id"
export META_APP_SECRET="your_app_secret"
```

#### Step 8: Verify

```bash
python3 scripts/social-media/instagram_poster.py check
```

### Usage

```bash
# Check API access
python3 scripts/social-media/instagram_poster.py check

# List pending posts from content calendar
python3 scripts/social-media/instagram_poster.py list

# Preview a post (dry run)
python3 scripts/social-media/instagram_poster.py publish --post 1 --dry-run

# Publish post 1
python3 scripts/social-media/instagram_poster.py publish --post 1

# Publish with a specific image URL
python3 scripts/social-media/instagram_poster.py publish --post 1 --image-url "https://example.com/img.png"

# Direct post (no content calendar)
python3 scripts/social-media/instagram_poster.py post --image-url "https://example.com/img.png" --caption "Hello world!"

# Export posts for manual copy-paste
python3 scripts/social-media/instagram_poster.py export
python3 scripts/social-media/instagram_poster.py export --post 1

# Refresh token (before it expires)
python3 scripts/social-media/instagram_poster.py refresh-token
```

### How It Works

1. **Content source**: Reads posts from `docs/social-media/pending-posts.md`
2. **Image resolution**: Converts local asset paths to public R2 URLs
3. **API flow**: Creates a media container, then publishes it
4. **Tracking**: Records what was posted in `~/.local/share/rex-instagram/posted.json`
5. **Manual fallback**: `export` command outputs copy-paste ready captions

### Image Requirements

- Images must be publicly accessible (R2 URLs work)
- Supported formats: JPEG, PNG (no WebP for feed posts)
- Minimum 320px, maximum 1440px width
- Aspect ratio between 4:5 and 1.91:1
- Maximum file size: 8MB

### Rate Limits

The Instagram Graph API has these limits:
- 25 API calls per user per hour (for content publishing)
- Maximum 25 posts per 24-hour period per account
- Carousel posts: 2-10 items

### Token Maintenance

Long-lived tokens expire after 60 days. To avoid interruption:
- Run `instagram_poster.py refresh-token` every 50 days
- The script warns when the token is expiring within 7 days
- Consider setting up a cron job for automatic refresh

### State Files

- `~/.config/rex-social/instagram.env` - API credentials
- `~/.local/share/rex-instagram/posted.json` - Post tracking
- `~/.local/share/rex-instagram/instagram.log` - Activity log

### Troubleshooting

#### "OAuthException" errors

- Token may have expired. Regenerate and update credentials.
- Permissions may be missing. Check app permissions in Meta Developer Portal.

#### "Invalid image URL"

- Image must be at a publicly accessible HTTPS URL
- R2 public URLs should work. Test by opening the URL in a browser.
- Instagram can't access localhost or private network URLs.

#### "Application does not have permission"

- In Development Mode, only test users/pages work
- Make sure your IG account is added as a test user in the app
- For production use, submit for App Review

---

## Twitter/X Monitoring (`twitter_monitor.py`)

Automated monitoring of Twitter/X for @rex_the_movie account mentions and relevant keywords.

### Overview

Uses the [bird CLI](https://github.com/steipete/bird) to monitor Twitter for:
- Mentions of @rex_the_movie
- Keywords: "fairy dinosaur", "rex marks the spot", "ai movie", etc.

When relevant tweets are found, tasks are created in the personal project for engagement.

### Setup

#### 1. Install bird CLI

```bash
npm install -g @steipete/bird
```

#### 2. Configure Twitter Credentials

The bird CLI uses cookie-based authentication (no API keys needed).

1. Login to x.com in your browser
2. Open Developer Tools (F12)
3. Go to Application -> Cookies -> https://x.com
4. Copy the values for `auth_token` and `ct0`

```bash
cp scripts/social-media/twitter_credentials.env.example ~/.config/bird/credentials.env
```

Edit `~/.config/bird/credentials.env`:

```bash
export AUTH_TOKEN="your_actual_auth_token"
export CT0="your_actual_ct0_token"
```

#### 3. Verify Setup

```bash
source ~/.config/bird/credentials.env
bird whoami
./scripts/social-media/twitter_monitor.py --check
```

#### 4. Install Cron Job

```bash
./scripts/social-media/setup_twitter_cron.sh
```

### Usage

```bash
# Full monitoring run
./scripts/social-media/twitter_monitor.py

# Dry run (don't create tasks)
./scripts/social-media/twitter_monitor.py --dry-run

# Only check credentials
./scripts/social-media/twitter_monitor.py --check
```

### State Files

- `~/.local/share/rex-twitter-monitor/seen_tweets.json` - Tracks processed tweets
- `~/.local/share/rex-twitter-monitor/monitor.log` - Activity log

---

## Files

| File | Purpose |
|------|---------|
| `instagram_poster.py` | Instagram Graph API posting automation |
| `instagram_credentials.env.example` | Instagram credential template |
| `twitter_monitor.py` | Twitter mention/keyword monitoring |
| `twitter_credentials.env.example` | Twitter credential template |
| `setup_twitter_cron.sh` | Twitter cron job installer |
| `README.md` | This file |
