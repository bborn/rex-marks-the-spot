# Twitter/X Monitoring for Rex Marks the Spot

Automated monitoring of Twitter/X for @rex_the_movie account mentions and relevant keywords.

## Overview

This system uses the [bird CLI](https://github.com/steipete/bird) to monitor Twitter for:
- Mentions of @rex_the_movie
- Keywords: "fairy dinosaur", "rex marks the spot", "ai movie", "ai animation", etc.

When relevant tweets are found, tasks are created in the personal project for engagement.

## Setup

### 1. Install bird CLI

```bash
npm install -g @steipete/bird
```

### 2. Configure Twitter Credentials

The bird CLI uses cookie-based authentication (no API keys needed).

1. Login to x.com in your browser
2. Open Developer Tools (F12)
3. Go to Application -> Cookies -> https://x.com
4. Copy the values for `auth_token` and `ct0`

Create the credentials file:

```bash
cp scripts/social-media/twitter_credentials.env.example ~/.config/bird/credentials.env
```

Edit `~/.config/bird/credentials.env` and fill in your tokens:

```bash
export AUTH_TOKEN="your_actual_auth_token"
export CT0="your_actual_ct0_token"
```

### 3. Verify Setup

```bash
# Test bird CLI
source ~/.config/bird/credentials.env
bird whoami

# Test monitor script
./scripts/social-media/twitter_monitor.py --check
```

### 4. Install Cron Job

```bash
./scripts/social-media/setup_twitter_cron.sh
```

This creates a cron job that runs every 30 minutes.

## Usage

### Manual Run

```bash
# Full monitoring run
./scripts/social-media/twitter_monitor.py

# Dry run (don't create tasks)
./scripts/social-media/twitter_monitor.py --dry-run

# Only check credentials
./scripts/social-media/twitter_monitor.py --check
```

### View Logs

```bash
# Recent activity
tail -f ~/.local/share/rex-twitter-monitor/monitor.log

# Cron output
tail -f ~/.local/share/rex-twitter-monitor/cron.log
```

### State Files

- `~/.local/share/rex-twitter-monitor/seen_tweets.json` - Tracks processed tweets
- `~/.local/share/rex-twitter-monitor/monitor.log` - Activity log

## How It Works

1. **Fetch mentions**: Gets recent tweets mentioning @rex_the_movie
2. **Search keywords**: Searches for relevant terms (excluding our own tweets)
3. **Filter**: Skips already-seen tweets and low-engagement spam
4. **Create tasks**: For each new relevant tweet, creates a task in the personal project

## Keywords Monitored

- "fairy dinosaur"
- "rex marks the spot"
- "rexmarksthespot"
- "ai movie"
- "ai animation"
- "ai filmmaking"
- "ai animated movie"

## Important Notes

### Cookie Expiration

Twitter cookies expire periodically. If monitoring stops working:
1. Re-login to x.com
2. Get fresh `auth_token` and `ct0` values
3. Update `~/.config/bird/credentials.env`

### Rate Limits

The bird CLI uses Twitter's undocumented GraphQL API. To avoid issues:
- Read-only operations are generally safe
- Avoid posting/replying through bird CLI
- Monitor runs every 30 minutes (not too aggressive)

### Security

Keep your credentials secure:
- `~/.config/bird/credentials.env` should have restricted permissions
- Never commit credentials to git
- Credentials give full account access

## Troubleshooting

### "Credentials not configured"

```bash
source ~/.config/bird/credentials.env
bird check
```

Make sure AUTH_TOKEN and CT0 environment variables are set.

### "bird CLI not found"

```bash
npm install -g @steipete/bird
# or
export PATH="$HOME/.nvm/versions/node/$(ls ~/.nvm/versions/node | tail -1)/bin:$PATH"
```

### No tasks being created

- Check if `ty` CLI is available
- Verify the personal project exists
- Check monitor.log for errors

## Files

- `twitter_monitor.py` - Main monitoring script
- `setup_twitter_cron.sh` - Cron job installer
- `twitter_credentials.env.example` - Credential template
- `README.md` - This file
