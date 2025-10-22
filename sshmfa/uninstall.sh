#!/usr/bin/env bash
# SSHMFA Uninstallation Script

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

log_warn "SSHMFA Uninstallation"
log_warn "====================="
log_warn ""
log_warn "This will disable and remove SSH 2FA configuration."
log_warn "Configuration backups will be restored if available."
log_warn ""

read -p "Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    log_info "Uninstallation cancelled"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Disable 2FA first
if [[ -f "$SCRIPT_DIR/scripts/disable-2fa.sh" ]]; then
    log_info "Disabling 2FA..."
    "$SCRIPT_DIR/scripts/disable-2fa.sh"
fi

# Remove bypass directory
log_info "Removing bypass directory..."
rm -rf /var/run/omen/bypass

# Note about omen-totp-admins group
log_info "Note: omen-totp-admins group has been left intact"
log_info "      Remove it manually if needed: groupdel omen-totp-admins"

log_info "SSHMFA uninstalled successfully"
log_info ""
log_info "Configuration backups are preserved:"
log_info "  /etc/ssh/sshd_config.pre-omen-2fa"
log_info "  /etc/pam.d/sshd.pre-omen-2fa"

