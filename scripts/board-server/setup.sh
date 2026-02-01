#!/bin/bash
# TaskYou Board Server Setup Script
# This script installs Node.js and sets up the board server as a systemd service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="taskyou-board-server"
PORT=3080

echo "=== TaskYou Board Server Setup ==="
echo ""

# Check if running as root for systemd operations
if [ "$EUID" -eq 0 ]; then
    echo "Please run this script as a regular user (not root)."
    echo "The script will use sudo when necessary."
    exit 1
fi

# Install Node.js if not present
install_nodejs() {
    if command -v node &> /dev/null; then
        echo "[OK] Node.js is already installed: $(node --version)"
        return 0
    fi

    echo "[*] Installing Node.js via nvm..."

    # Install nvm
    if [ ! -d "$HOME/.nvm" ]; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    fi

    # Source nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    # Install latest LTS
    nvm install --lts
    nvm use --lts

    echo "[OK] Node.js installed: $(node --version)"
}

# Install npm dependencies
install_dependencies() {
    echo "[*] Installing npm dependencies..."
    cd "$SCRIPT_DIR"

    # Source nvm if needed
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    npm install
    echo "[OK] Dependencies installed"
}

# Create systemd service
create_systemd_service() {
    echo "[*] Creating systemd service..."

    # Get the full path to node
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    NODE_PATH=$(which node)

    # Create service file
    SERVICE_FILE="/tmp/${SERVICE_NAME}.service"
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=TaskYou Board API Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment=NODE_ENV=production
Environment=PORT=$PORT
Environment=HOME=$HOME
ExecStart=$NODE_PATH $SCRIPT_DIR/server.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Install service
    sudo mv "$SERVICE_FILE" "/etc/systemd/system/${SERVICE_NAME}.service"
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"

    echo "[OK] Systemd service created and enabled"
}

# Start the service
start_service() {
    echo "[*] Starting the service..."
    sudo systemctl start "$SERVICE_NAME"

    # Wait a moment and check status
    sleep 2
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "[OK] Service is running"
        echo ""
        echo "=== Service Status ==="
        sudo systemctl status "$SERVICE_NAME" --no-pager
    else
        echo "[ERROR] Service failed to start"
        sudo journalctl -u "$SERVICE_NAME" -n 20 --no-pager
        exit 1
    fi
}

# Main setup flow
main() {
    install_nodejs
    install_dependencies
    create_systemd_service
    start_service

    echo ""
    echo "=== Setup Complete ==="
    echo ""
    echo "The TaskYou Board API server is now running on port $PORT"
    echo ""
    echo "API Endpoints:"
    echo "  GET http://localhost:$PORT/api/board"
    echo "  GET http://localhost:$PORT/api/task/:id"
    echo "  GET http://localhost:$PORT/api/task/:id/output"
    echo "  GET http://localhost:$PORT/health"
    echo ""
    echo "Useful commands:"
    echo "  sudo systemctl status $SERVICE_NAME   # Check status"
    echo "  sudo systemctl restart $SERVICE_NAME  # Restart service"
    echo "  sudo systemctl stop $SERVICE_NAME     # Stop service"
    echo "  sudo journalctl -u $SERVICE_NAME -f   # View logs"
    echo ""
    echo "To make this accessible from the internet, configure your reverse proxy"
    echo "(nginx/caddy) to proxy api.rexmarksthespot.com to localhost:$PORT"
}

main
