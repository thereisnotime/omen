#!/usr/bin/env bash
# SAMS Installation Script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

log_info "Installing SAMS (Suspicious Activity Monitoring System)..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install Python dependencies
log_info "Installing Python dependencies..."
pip3 install requests watchdog psutil 2>/dev/null || true

# Install auditd if use_auditd is enabled
log_info "Installing auditd..."
apt-get install -y auditd audispd-plugins 2>/dev/null || true

# Create log directory
log_info "Creating log directory..."
mkdir -p /var/log/omen
chmod 755 /var/log/omen

# Create lib directory for file hashes
mkdir -p /var/lib/omen
chmod 755 /var/lib/omen

# Copy configuration if it doesn't exist
if [[ ! -f "$SCRIPT_DIR/config.json" ]]; then
    log_info "Creating default configuration..."
    cp "$SCRIPT_DIR/config.json.example" "$SCRIPT_DIR/config.json"
    log_warn "Please edit $SCRIPT_DIR/config.json to configure alerting"
fi

# Install systemd service
log_info "Installing systemd service..."
cp "$SCRIPT_DIR/systemd/sams.service" /etc/systemd/system/omen-sams.service
systemctl daemon-reload

log_info "SAMS installation complete!"
log_info ""
log_info "Next steps:"
log_info "1. Edit configuration: $SCRIPT_DIR/config.json"
log_info "2. Start service: systemctl start omen-sams"
log_info "3. Enable on boot: systemctl enable omen-sams"
log_info "4. Check status: systemctl status omen-sams"
log_info "5. View logs: journalctl -u omen-sams -f"

