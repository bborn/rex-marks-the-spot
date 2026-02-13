#!/bin/bash
# Start the rigging review app
# Usage: ./start.sh [--port PORT]
#
# Default port: 3090
# Access at: http://rex:3090

set -e
cd "$(dirname "$0")"

PORT="${1:-3090}"
if [ "$1" = "--port" ]; then
    PORT="$2"
fi

echo "Starting Rigging Review App on port $PORT..."
echo "Access at: http://$(hostname):$PORT"
echo ""

exec uvicorn app:app --host 0.0.0.0 --port "$PORT"
