#!/bin/bash
# Setup cron job for Twitter monitoring
# Run this script once after configuring bird credentials

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/twitter_monitor.py"
LOG_DIR="$HOME/.local/share/rex-twitter-monitor"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Create the cron entry (every 30 minutes)
CRON_CMD="*/30 * * * * $MONITOR_SCRIPT >> $LOG_DIR/cron.log 2>&1"

# Check if entry already exists
if crontab -l 2>/dev/null | grep -F "twitter_monitor.py" > /dev/null; then
    echo "Cron job already exists. Current crontab:"
    crontab -l | grep twitter_monitor
    echo ""
    read -p "Replace existing entry? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing cron job."
        exit 0
    fi
    # Remove existing entry
    crontab -l | grep -v "twitter_monitor.py" | crontab -
fi

# Add new cron entry
(crontab -l 2>/dev/null || true; echo "$CRON_CMD") | crontab -

echo "Cron job installed:"
crontab -l | grep twitter_monitor
echo ""
echo "Monitor will run every 30 minutes."
echo "Logs: $LOG_DIR/cron.log"
echo ""
echo "To test immediately, run:"
echo "  $MONITOR_SCRIPT"
echo ""
echo "To remove the cron job later:"
echo "  crontab -l | grep -v 'twitter_monitor.py' | crontab -"
