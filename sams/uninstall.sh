#!/usr/bin/env bash
# SAMS Uninstallation Script

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

log_warn "SAMS Uninstallation"
log_warn "==================="
log_warn ""
log_warn "This will remove SAMS service and stop monitoring."
log_warn "Log files will be preserved in /var/log/omen/"
log_warn ""

read -p "Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    log_info "Uninstallation cancelled"
    exit 0
fi

log_info "Stopping SAMS service..."
systemctl stop omen-sams 2>/dev/null || true
systemctl disable omen-sams 2>/dev/null || true

log_info "Removing systemd service..."
rm -f /etc/systemd/system/omen-sams.service
systemctl daemon-reload

log_info "SAMS uninstalled successfully"
log_info ""
log_info "Logs are still available in /var/log/omen/sams.log"
log_info "Configuration preserved in $(dirname "$0")/config.json"

